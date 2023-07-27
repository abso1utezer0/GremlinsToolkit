import os
import sys
import struct
import zlib
import io

from formats.filemanipulator import FileManipulator

# create packfile class
class Packfile:
    packfile_path = ""
    magic = "    "
    version = 0
    num_files = 0
    header_zero = 0
    header_size = 0
    header_data_ptr = 0
    string_pointer = 0
    current_data_positon = 0
    current_header_position = 0

    string_partition_folder_pointers = []
    string_partition_file_pointers = []

    containing_file_paths = []

    file_manipulator = None

    def __init__(self, path):
        # set packfile path
        self.packfile_path = path
        # check if packfile exists
        if os.path.exists(path):
            # open packfile
            self.file_manipulator = FileManipulator(path, "rb", "big")
            # read magic ("PAK " or " KAP")
            self.magic = self.file_manipulator.r_str(4)
            endian = "big"
            if self.magic == "PAK ":
                endian = "little"
            self.file_manipulator.set_endian(endian)
        else:
            self.file_manipulator = FileManipulator(path, "wb", "big")
    
    def get_header_magic(self):
        # set file position to 0
        self.file_manipulator.seek(0)
        # read magic
        magic = self.file_manipulator.r_str(4)
        # return magic
        return magic
    
    def get_header_version(self):
        # set file position to 4
        self.file_manipulator.seek(4)
        # read version
        version = self.file_manipulator.r_int()
        # return version
        return version
    
    def get_header_zero(self):
        # set file position to 8
        self.file_manipulator.seek(8)
        # read zero
        zero = self.file_manipulator.r_int()
        # return zero
        return zero
    
    def get_header_size(self):
        # set file position to 12
        self.file_manipulator.seek(12)
        # read header size
        header_size = self.file_manipulator.r_int()
        # return header size
        return header_size
    
    def get_header_data_ptr(self):
        #set file position to 16
        self.file_manipulator.seek(16)
        # read header data pointer
        header_data_ptr = self.file_manipulator.r_int()
        # return header data pointer
        return header_data_ptr
    
    def get_header_num_files(self):
        # go to header size
        self.file_manipulator.seek(self.get_header_size())
        # read number of files
        num_files = self.file_manipulator.r_int()
        # return number of files
        return num_files
    
    def close(self):
        self.file_manipulator.close()
    
    def get_containing_paths(self):
        self.update_header_vars()
        # seek to current header position
        self.file_manipulator.seek(self.current_header_position)
        paths = []
        # loop through all files
        for i in range(self.num_files):
            # skip 12 bytes forward
            self.file_manipulator.move(12)
            # read folder pointer as a 4 byte int
            folder_pointer = self.file_manipulator.r_int()
            # skip 4 bytes forward
            self.file_manipulator.move(4)
            # read file pointer as a 4 byte int
            file_pointer = self.file_manipulator.r_int()

            # add the string pointer to the folder name pointer and the file name pointer
            folder_pointer += self.string_pointer
            file_pointer += self.string_pointer

            # add 24 to the current header position
            self.current_header_position += 24

            # go to the folder name pointer
            self.file_manipulator.seek(folder_pointer)

            # read the folder name as a null terminated string
            folder_name = self.file_manipulator.r_str_null()

            # go to the file name pointer
            self.file_manipulator.seek(file_pointer)

            # read the file name as a null terminated string
            file_name = self.file_manipulator.r_str_null()

            # combine the folder name and the file name
            path = folder_name + "/" + file_name

            # add the path to the list of paths
            paths.append(path)

            # seek to the current header position
            self.file_manipulator.seek(self.current_header_position)
        # return the list of paths
        return paths

    def update_header_vars(self):
        self.magic = self.get_header_magic()
        self.version = self.get_header_version()
        self.header_zero = self.get_header_zero()
        self.header_size = self.get_header_size()
        self.header_data_ptr = self.get_header_data_ptr()
        self.header_data_ptr += self.header_size
        self.current_data_positon = self.header_data_ptr
        self.num_files = self.get_header_num_files()
        self.string_pointer = (self.num_files * 24) + self.header_size + 4
        self.current_header_position = self.header_size + 4

    def throw_error(self, var_name, expected, actual):
        raise Exception("Invalid " + var_name + " on file " + self.packfile_path + ". Expected: " + str(expected) + ", Actual: " + str(actual))

    def extract(self, extraction_path):
        # delete the extraction path if it exists
        if os.path.exists(extraction_path):
            os.remove(extraction_path)
        # create the extraction path
        os.mkdir(extraction_path)
        extraction_path = extraction_path.replace("\\", "/")
        # remove the last slash if it exists
        if extraction_path[-1] == "/":
            extraction_path = extraction_path[:-1]
        
        self.update_header_vars()

        # check magic
        if self.magic != "PAK " and self.magic != " KAP":
            self.throw_error("magic", "'PAK ' or ' KAP'", self.magic)
        
        # check version
        if self.version != 2:
            self.throw_error("version", "2", self.version)
        
        # check header zero
        if self.header_zero != 0:
            self.throw_error("header zero", "0", self.header_zero)

        # go to current header position
        self.file_manipulator.seek(self.current_header_position)

        # loop through all files
        for i in range(self.num_files):
            # get the real file size as a 4 byte int
            real_file_size = self.file_manipulator.r_int()
            # get the compressed file size as a 4 byte int
            compressed_file_size = self.file_manipulator.r_int()
            # get the aligned file size as a 4 byte int
            aligned_file_size = self.file_manipulator.r_int()

            # check if aligned file size is modulable by 32
            if aligned_file_size % 32 != 0:
                self.throw_error("aligned file size", "multiple of 32", aligned_file_size)
            
            # read the folder pointer as a 4 byte int
            folder_pointer = self.file_manipulator.r_int()
            # read the file type as a 4 byte string
            file_type = self.file_manipulator.r_str(4)
            # read the file pointer as a 4 byte int
            file_pointer = self.file_manipulator.r_int()

            # add the string pointer to the folder name pointer and the file name pointer
            folder_pointer += self.string_pointer
            file_pointer += self.string_pointer

            # set the current header position to the current position
            self.current_header_position = self.file_manipulator.tell()

            # go to the folder name pointer
            self.file_manipulator.seek(folder_pointer)
            # read the folder name as a null terminated string
            folder_name = self.file_manipulator.r_str_null()

            # go to the file name pointer
            self.file_manipulator.seek(file_pointer)
            # read the file name as a null terminated string
            file_name = self.file_manipulator.r_str_null()

            # combine the folder name and the file name
            path = folder_name + "/" + file_name

            path = extraction_path + "/" + path

            # create the folder if it doesn't exist
            if not os.path.exists(path[:path.rfind("/")]):
                os.makedirs(path[:path.rfind("/")])
            
            # create the file
            out_fm = FileManipulator(path, "wb", "little")

            # go to the current data position
            self.file_manipulator.seek(self.current_data_positon)

            # read the data
            data = self.file_manipulator.r_bytes(compressed_file_size)

            # if the file is compressed, decompress it
            if compressed_file_size != real_file_size:
                data = zlib.decompress(data)
            
            # write the data to the file
            out_fm.w_bytes(data)

            # add the aligned file size to the current data position
            self.current_data_positon += aligned_file_size

            # close the file
            out_fm.close()

            # go to the current header position
            self.file_manipulator.seek(self.current_header_position)

    def compress(self, base_path, files_to_compress, endian):
        # wipe the file if it exists
        if os.path.exists(self.packfile_path):
            # delete all data in the file, but keep the file
            open(self.packfile_path, "w").close()

        self.file_manipulator.set_endian(endian)

        # create the file
        
        



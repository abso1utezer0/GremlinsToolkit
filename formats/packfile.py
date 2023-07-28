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

    def assemble_path_partition(self, paths):
        path_partition = ""
        current_folder = ""
        current_folder_pointer = 0
        for i in range(len(paths)):
            path = paths[i]
            path = path.replace("\\", "/")
            # split the path into parts split by forward slashes
            split_path = path.split("/")
            # get the filename
            filename = split_path[len(split_path) - 1]
            # get the directory
            directory = path[0:path.rfind("/")]
            # remove the last forward slash from the directory if it exists
            if directory[len(directory) - 1] == "/":
                directory = directory[0:len(directory) - 1]

            # if the directory is not the same as the current folder, append it to the path
            # partition
            if directory != current_folder:
                # update the current folder pointer
                current_folder_pointer = len(path_partition)
                path_partition += directory
                current_folder = directory
                # write a null byte to the path partition
                path_partition += '\0'
            # add the folder name pointer to the array
            # increase the size of the array by 1
            self.string_partition_folder_pointers.append(0)
            self.string_partition_folder_pointers[i] = current_folder_pointer
            # add the file name pointer to the array
            # increase the size of the array by 1
            self.string_partition_file_pointers.append(0)
            self.string_partition_file_pointers[i] = len(path_partition)
            # write the filename to the path partition
            path_partition += filename
            # write a null byte to the path partition
            path_partition += '\0'
        return path_partition

    def compress(self, base_path, files_to_compress, endian):
        # wipe the file if it exists
        if os.path.exists(self.packfile_path):
            # delete all data in the file, but keep the file
            open(self.packfile_path, "w").close()
        
        # open the file
        self.file_manipulator = FileManipulator(self.packfile_path, "wb", endian)

        # check if the base path exists
        if not os.path.exists(base_path):
            self.throw_error("base path", "exists", base_path)
        
        # change base path to forward slashes
        base_path = base_path.replace("\\", "/")

        # remove the last forward slash from the base path if it exists
        if base_path[len(base_path) - 1] == "/":
            base_path = base_path[0:len(base_path) - 1]

        self.num_files = len(files_to_compress)

        path_partition = self.assemble_path_partition(files_to_compress)

        # set the magic
        if endian == "big":
            self.magic = " KAP"
        else:
            self.magic = "PAK "
        
        # set the version
        self.version = 2

        # set the header zero
        self.header_zero = 0

        # set the header size
        self.header_size = 32

        self.header_data_ptr = self.header_size + len(path_partition) + (self.num_files * 24)

        while self.header_data_ptr % 32 != 0:
            self.header_data_ptr += 1
        
        # write the magic
        self.file_manipulator.w_str(self.magic)

        # write the version
        self.file_manipulator.w_int(self.version)

        # write the header zero
        self.file_manipulator.w_int(self.header_zero)

        # write the header size
        self.file_manipulator.w_int(self.header_size)

        # write the data pointer
        self.file_manipulator.w_int(self.header_data_ptr - self.header_size)

        # go to the header size
        self.file_manipulator.seek(self.header_size)

        # write the number of files
        self.file_manipulator.w_int(self.num_files)

        # set the current header position
        self.current_header_position = self.file_manipulator.tell()

        self.string_pointer = self.current_header_position + (self.num_files * 24)

        # go to the string pointer
        self.file_manipulator.seek(self.string_pointer)

        # write the path partition
        self.file_manipulator.w_str(path_partition)

        # set the current data position
        self.current_data_positon = self.header_data_ptr

        # go to the current header position
        self.file_manipulator.seek(self.current_header_position)

        # loop through all the files
        for i in range(self.num_files):
            rel_path = files_to_compress[i].replace("\\", "/")
            # join the base path and the file path
            file_path = base_path + "/" + files_to_compress[i]
            fm2 = FileManipulator(file_path, "rb", "big")
            file_extension = file_path[file_path.rfind(".") + 1:len(file_path)].lower()

            quick_access = False

            quick_access_extensions = {
                "hkx",
                "hkx_wii",
                "hkw",
                "hkw_wii",
                "nif",
                "nif_wii",
                "kfm",
                "kfm_wii",
                "kf",
                "kf_wii",
                "lit",
                "lit_cooked",
                "bsq",
                "dct",
            }
            
            if file_extension in quick_access_extensions:
                quick_access = True
            
            file_type = ""

            if file_extension == "hkx" or file_extension == "hkx_wii":
                # go to offset 0x58 in file
                fm2.seek(0x58)
                hkx_type = fm2.r_int()
                if hkx_type == 224:
                    file_type = "hkb"
                elif hkx_type == 144:
                    file_type = "hkp"
                else:
                    file_type = "hkx"
                fm2.seek(0)
            elif file_extension == "hkw" or file_extension == "hkw_wii":
                file_type = "hkw"
            elif file_extension == "nif" or file_extension == "nif_wii":
                file_type = "nif"
            elif file_extension == "kfm" or file_extension == "kfm_wii":
                file_type = "kfm"
            elif file_extension == "kf" or file_extension == "kf_wii":
                file_type = "kf"
            elif file_extension == "lit" or file_extension == "lit_cooked":
                file_type = "lit"
            elif file_extension == "bsq":
                file_type = "bsq"
            elif file_extension == "gfx":
                file_type = "gfx"
            
            file_type = file_type.upper()
            # while the file type is less than 4 characters, add null bytes
            while len(file_type) < 4:
                file_type += "\0"
            
            # get the file data
            file_data = fm2.read()

            real_file_size = len(file_data)

            # if the file is not a quick access file, compress it
            if not quick_access:
                file_data = zlib.compress(file_data, 6)
            
            # get the compressed file size
            compressed_file_size = len(file_data)

            aligned_file_size = compressed_file_size

            while aligned_file_size % 32 != 0:
                aligned_file_size += 1
            
            # write the real file size
            self.file_manipulator.w_int(real_file_size)

            # write the compressed file size
            self.file_manipulator.w_int(compressed_file_size)

            # write the aligned file size
            self.file_manipulator.w_int(aligned_file_size)

            # write the string partition folder pointer
            self.file_manipulator.w_int(self.string_partition_folder_pointers[i])

            # write the file type
            if len(file_type) > 4:
                self.throw_error("file type", "string with length of 4", file_type)

            self.file_manipulator.w_str(file_type)

            # write the string partition file pointer
            self.file_manipulator.w_int(self.string_partition_file_pointers[i])

            self.current_header_position = self.file_manipulator.tell()

            # go to the current data position
            self.file_manipulator.seek(self.current_data_positon)

            # write the file data
            self.file_manipulator.write(file_data)

            # add the aligned file size to the current data position
            self.current_data_positon += aligned_file_size

            # write null bytes
            null_amount = aligned_file_size - compressed_file_size
            for i in range(null_amount):
                self.file_manipulator.w_str("\0")
            
            # go to the current header position
            self.file_manipulator.seek(self.current_header_position)


            



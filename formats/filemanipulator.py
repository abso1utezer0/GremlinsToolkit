import os
import sys
import io
import struct

class FileManipulator:
    endian = "big"

    path = ""
    file = None

    def __init__(self, path, operation, endian):
        self.path = path
        self.file = open(path, operation)
        self.endian = endian

    # close
    def close(self):
        self.file.close()

    def set_endian(self, endian):
        self.endian = endian

    # reading shortcuts
    def r_int(self, length):
        # read bytes
        bytes = self.file.read(length)
        # unpack bytes as integer
        return int.from_bytes(bytes, byteorder = self.endian)
    
    def r_int(self):
        # read bytes
        bytes = self.file.read(4)
        # unpack bytes as integer
        return int.from_bytes(bytes, byteorder = self.endian)

    def r_float(self, length):
        # read bytes
        bytes = self.file.read(length)
        # unpack bytes as float
        if self.endian == "big":
            return struct.unpack(">f", bytes)[0]
        else:
            return struct.unpack("<f", bytes)[0]

    def r_str(self, length):
        # read bytes
        bytes = self.file.read(length)
        # unpack bytes as string
        return bytes.decode("utf-8")
    
    def r_str_null(self):
        # read string until null byte
        str = ""
        while True:
            byte = self.file.read(1)
            if byte == b"\x00":
                break
            str += byte.decode("utf-8")
        return str

    def r_bytes(self, length):
        # read bytes
        return self.file.read(length)
    
    # writing shortcuts
    def w_int(self, value, length):
        # pack integer as bytes
        bytes = value.to_bytes(length, byteorder = self.endian)
        # write bytes
        self.file.write(bytes)

    def w_int(self, value):
        # pack integer as bytes
        bytes = value.to_bytes(4, byteorder = self.endian)
        # write bytes
        self.file.write(bytes)

    def w_float(self, value, length):
        # pack float as bytes
        if self.endian == "big":
            bytes = struct.pack(">f", value)
        else:
            bytes = struct.pack("<f", value)
        # write bytes
        self.file.write(bytes)

    def w_str(self, value):
        # pack string as bytes
        bytes = value.encode("utf-8")
        # write bytes
        self.file.write(bytes)

    def w_str_null(self, value):
        # pack string as bytes
        bytes = value.encode("utf-8")
        # write bytes
        self.file.write(bytes)
        # write null byte
        self.file.write(b"\x00")

    def w_bytes(self, value):
        # write bytes
        self.file.write(value)

    # other
    def move(self, amount):
        # move file pointer
        self.file.seek(self.file.tell() + amount)
    
    def tell(self):
        # get file pointer
        return self.file.tell()
    
    def seek(self, position):
        # set file pointer
        self.file.seek(position)
    
    def get_size(self):
        # get file size
        return os.path.getsize(self.path)
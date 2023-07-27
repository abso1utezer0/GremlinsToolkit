import eel
from formats.packfile import Packfile

#eel.init('html')
#
#@eel.expose
#def get_header_magic(path):
#    packfile = Packfile(path)
#    return packfile.get_header_magic()
#
#@eel.expose
#def print_header_magic(path):
#    print(get_header_magic(path))
#
#@eel.expose
#def print_hi():
#    print("hi")
#
#eel.start('index.html', size=(1000, 600))

packfile = Packfile("E:/Modding/EpicMickey/Builds/EM1/clean/DATA/files/packfiles/_Dynamic.pak")
packfile.extract("test")
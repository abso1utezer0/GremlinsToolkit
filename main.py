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

packfile = Packfile("test.pak")
files_to_compress = [
    "Environments/_Test/building_standards.bin",
    "Palettes/_Dynamic/Effects/PaintHit.bin",
    "Palettes/_Dynamic/Effects/ThinnerHit.bin",
    "Palettes/_Dynamic/Effects/MickeyThinnerDeathFX.bin",
    "Palettes/_Dynamic/PlayerTools/PaintStream.bin",
    "Palettes/_Dynamic/PlayerTools/ThinnerStream.bin",
    "GameObjects/Pickups/GenPickupCollision.hkx_wii",
    "Environments/Demo/Props/Demo_GV_Portal_Stand.hkx_wii",
    "Environments/_Shared/Scripts/Prefab_GrabCameraFancy.lua",
    "environments/_test/Building_Standards_building_standards_AI_path_database_01/data.hpd",
    "environments/_test/Building_Standards_building_standards_AI_path_database_02/data.hpd",
    "Effects/_Shared/Distribution_Anim_Quest.nif_wii"
]
packfile.compress("E:/Modding/EpicMickey/BuildsEx/EM1", files_to_compress, "big")
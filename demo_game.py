from direct.showbase.ShowBase import ShowBase
from panda3d.core import GeoMipTerrain

class DemoGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        terrain = GeoMipTerrain("worldTerrain")
        terrain.setHeightfield("height_map.png")
        terrain.setColorMap("colour_map_flipped.png")
        terrain.setBruteforce(True)
        root = terrain.getRoot()
        root.reparentTo(render)
        root.setSz(60)
        terrain.generate()

game = DemoGame()
game.run()

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from pandac.PandaModules import CompassEffect
from panda3d.core import AmbientLight, DirectionalLight, Vec4, Vec3, Fog
from panda3d.core import GeoMipTerrain
import sys

class DemoGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.world = self.loader.loadModel("world.bam")
        self.world.reparentTo(self.render)

        self.world_size = 1024

        self.player = self.loader.loadModel("alliedflanker.egg")
        self.player.setPos(self.world, 200, 200, 65)
        self.player.setH(self.world, 255)
        self.player.reparentTo(self.render)

        self.taskMgr.add(self.updateTask, "update")
        self.keyboardSetup()
        self.speed = 0.0
        self.max_speed = 100.0
        self.player.setScale(0.2, 0.2, 0.2)

        self.max_distance = 400
        self.camLens.setFar(self.max_distance)
        self.camLens.setFov(60)
        
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

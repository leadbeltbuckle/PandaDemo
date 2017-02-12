from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from pandac.PandaModules import CompassEffect
from panda3d.core import AmbientLight, DirectionalLight, Vec4, Vec3, Fog
from panda3d.core import GeoMipTerrain
import sys


class DemoGame(ShowBase):
    def __init__(self):
        try:
            self.world = self.loader.loadModel("world.bam")
            self.world.reparentTo(self.render)
            self.world_size = 1024
        except:
            ShowBase.__init__(self)
            terrain = GeoMipTerrain("worldTerrain")
            terrain.setHeightfield("height_map.png")
            terrain.setColorMap("colour_map_flipped.png")
            terrain.setBruteforce(True)
            root = terrain.getRoot()
            root.reparentTo(render)
            root.setSz(60)
            terrain.generate()
            root.writeBamFile("world.bam")

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

        self.createEnvironment()

    def keyboardSetup(self):
            self.keyMap = {"left": 0, "right": 0, "climb": 0, "fall": 0,
                           "accelerate": 0, "decelerate": 0, "fire": 0}
            self.accept("escape", sys.exit)
            self.accept("a", self.setKey, ["accelerate", 1])
            self.accept("a-up", self.setKey, ["accelerate", 0])
            self.accept("z", self.setKey, ["decelerate", 1])
            self.accept("z-up", self.setKey, ["decelerate", 0])
            self.accept("arrow_left", self.setKey, ["left", 1])
            self.accept("arrow_left-up", self.setKey, ["left", 0])
            self.accept("arrow_right", self.setKey, ["right", 1])
            self.accept("arrow_right-up", self.setKey, ["right", 0])
            self.accept("arrow_down", self.setKey, ["climb", 1])
            self.accept("arrow_down-up", self.setKey, ["climb", 0])
            self.accept("arrow_up", self.setKey, ["fall", 1])
            self.accept("arrow_up-up", self.setKey, ["fall", 0])
            self.accept("space", self.setKey, ["fire", 1])
            self.accept("space-up", self.setKey, ["fire", 0])
            base.disableMouse() # or updateCamera will fail!

    def setKey(self, key, value):
        self.keyMap[key] = value

    def updateTask(self, task):
        self.updatePlayer()
        self.updateCamera()
        return Task.cont

    def updatePlayer(self):
        # Global Clock
        # by default, panda runs as fast as it can frame by frame
        scale_factor = (globalClock.getDt()*self.speed)
        climb_factor = scale_factor * 0.5
        bank_factor = scale_factor
        speed_factor = scale_factor * 2.9

        # Climb and Fall
        if self.keyMap["climb"] != 0 and self.speed > 0.00:
            # The faster you go, the faster you climb
            self.player.setZ(self.player.getZ() + climb_factor)
            self.player.setR(self.player.getR() + climb_factor)
            # quickest return: avaoids uncoil/unwind
            if (self.player.getR() >= 180):
                self.player.setR(-180)

        elif self.keyMap["fall"] != 0 and self.speed > 0.00:
            self.player.setZ(self.player.getZ() - climb_factor)
            self.player.setR(self.player.getR() - climb_factor)
            # quickest return
            if (self.player.getR() <= -180):
                self.player.setR(180)

        # autoreturn - add a bit regardless to make sure it happens
        elif self.player.getR() > 0:
            self.player.setR(self.player.getR() - (climb_factor + 0.1))
            if self.player.getR() < 0:
                self.player.setR(0)
        elif self.player.getR() < 0:
            self.player.setR(self.player.getR() + (climb_factor + 0.1))
            if self.player.getR() > 0:
                self.player.setR(0)

        # Left and Right
        if self.keyMap["left"] != 0 and self.speed > 0.0:
            self.player.setH(self.player.getH() + bank_factor)
            self.player.setP(self.player.getP() + bank_factor)
            if self.player.getP() >= 180:
                self.player.setP(-180)
        elif self.keyMap["right"] != 0 and self.speed > 0.0:
            self.player.setH(self.player.getH() - bank_factor)
            self.player.setP(self.player.getP() - bank_factor)
            if self.player.getP() <= -180:
                self.player.setP(180)
        elif self.player.getP() > 0:
            self.player.setP(self.player.getP() - (bank_factor + 0.1))
            if self.player.getP() < 0:
                self.player.setP(0)
        elif self.player.getP() < 0:
            self.player.setP(self.player.getP() + (bank_factor + 0.1))
            if self.player.getP() > 0:
                self.player.setP(0)

        # throttle control
        if self.keyMap["accelerate"] != 0:
            self.speed += 1
            if self.speed > self.max_speed:
                self.speed = self.max_speed
        elif self.keyMap["decelerate"] != 0:
            self.speed -= 1
            if self.speed < 0.0:
                self.speed = 0.0

        # move forwards - our X/Y is inverted
        self.player.setX(self.player, -speed_factor)

        # respet max camera distance else you
        # cannot see the floor post loop the loop
        if self.player.getZ() > self.max_distance:
            self.player.setZ(self.max_distance)
        # should never happen once we add collusion, but in case:
        elif self.player.getZ() < 0:
            self.player.setZ(0)

        # and now the X/Y world boundaries:
        if self.player.getX() < 0:
            self.player.setX(0)
        elif self.player.getX() > self.world_size:
            self.player.setX(self.world_size)

        if self.player.getY() < 0:
            self.player.setY(0)
        elif self.player.getY() > self.world_size:
            self.player.setY(self.world_size)

    def updateCamera(self):
        self.camera.setPos(self.player, 25.6225, 3.8807, 10.2779)
        self.camera.setHpr(self.player, 94.8996, -16.6549, 1.55508)

    def createEnvironment(self):
        # Fog to hide a performance tweak
        colour = (0.0, 0.0, 0.0)
        exp_fog = Fog("scene-wide-fog")
        exp_fog.setColor(*colour)
        exp_fog.setExpDensity(0.004)
        render.setFog(exp_fog)
        base.setBackgroundColor(*colour)

        # Sky
        sky_dome = loader.loadModel("sky.egg")
        sky_dome.setEffect(CompassEffect.make(self.render))
        sky_dome.setScale(self.max_distance / 2)
        sky_dome.setZ(-65)  # sink it
        # NOT render - you'll fly through the sky!
        sky_dome.reparentTo(self.camera)

        # Lighting
        ambient_light = AmbientLight("ambientLight")
        ambient_colour = Vec4(0.6, 0.6, 0.6, 1)
        ambient_light.setColor(ambient_colour)
        directional_light = DirectionalLight("directionalLight")
        direction = Vec3(0, -10, -10)
        directional_light.setDirection(direction)
        directional_colour = Vec4(1, 1, 1, 1)
        directional_light.setColor(directional_colour)
        directional_specular = Vec4(1, 1, 1, 1)
        directional_light.setSpecularColor(directional_specular)
        render.setLight(render.attachNewNode(ambient_light))
        render.setLight(render.attachNewNode(directional_light))



game = DemoGame()
game.run()

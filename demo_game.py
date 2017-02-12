from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.interval.LerpInterval import LerpTexOffsetInterval
from direct.gui.OnscreenText import OnscreenText
from pandac.PandaModules import CompassEffect, CollisionTraverser, CollisionNode
from pandac.PandaModules import CollisionSphere, CollisionHandlerQueue, Material
from pandac.PandaModules import VBase4, VBase3, TransparencyAttrib
from panda3d.core import AmbientLight, DirectionalLight, Vec4, Vec3, Fog
from panda3d.core import BitMask32, Texture, TextNode, TextureStage
from panda3d.core import NodePath, PandaNode
# from panda3d.core import GeoMipTerrain
import sys


class DemoGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.debug = False
        self.status_label = self.makeStatusLabel(0)
        self.collision_label = self.makeCollisionLabel(1)

        # terrain = GeoMipTerrain("worldTerrain")
        # terrain.setHeightfield("models/height_map.png")
        # terrain.setColorMap("models/colour_map_flipped.png")
        # terrain.setBruteforce(True)
        # root = terrain.getRoot()
        # root.reparentTo(render)
        # root.setSz(60)
        # terrain.generate()
        # root.writeBamFile("models/world.bam")

        self.world = self.loader.loadModel("models/world.bam")
        self.world.reparentTo(self.render)
        self.world_size = 1024

        self.player = self.loader.loadModel("models/alliedflanker")    # alliedflanker.egg by default
        self.max_speed = 100.0
        self.start_pos = Vec3(200, 200, 65)
        self.start_hpr = Vec3(225, 0, 0)
        self.player.setScale(0.2, 0.2, 0.2)
        self.player.reparentTo(self.render)
        self.resetPlayer()

        self.taskMgr.add(self.updateTask, "update")
        self.keyboardSetup()

        self.max_distance = 400
        if not self.debug:
            self.camLens.setFar(self.max_distance)
        else:
            base.oobe()

        self.camLens.setFov(60)
        self.createEnvironment()
        self.setupCollisions()
        self.text_counter = 0

        # load the explosion ring
        self.explosion_model = loader.loadModel("models/explosion")    # Panda3D Defaults to '.egg'
        self.explosion_model.reparentTo(self.render)
        self.explosion_model.setScale(0.0)
        self.explosion_model.setLightOff()
        # Only one explosion at a time
        self.exploding = False

    def makeStatusLabel(self, i):
        return OnscreenText(style=2, fg=(0.5, 1, 0.5, 1), pos=(-1.3, 0.92, (-0.08 * i)),
                            align=TextNode.ALeft, scale=0.08, mayChange=1)

    def makeCollisionLabel(self, i):
        return OnscreenText(style=2, fg=(0.5, 1, 0.5, 1), pos=(-1.3, 0.92, (-0.08 * i)),
                            align=TextNode.ALeft, scale=0.08, mayChange=1)

    def resetPlayer(self):
        self.player.show()
        self.player.setPos(self.world, self.start_pos)
        self.player.setHpr(self.world, self.start_hpr)
        self.speed = self.max_speed / 2

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

        self.coll_trav.traverse(self.render)
        for i in range(self.player_ground_handler.getNumEntries()):
            entry = self.player_ground_handler.getEntry(i)
            if self.debug:
                self.collision_label.setText("dead:"+str(globalClock.getFrameTime()))
            if not self.exploding:
                self.player.setZ(entry.getSurfacePoint(self.render).getZ() + 10)
                self.explosionSequence()
        return Task.cont

    def explosionSequence(self):
        self.exploding = True
        pos = Vec3(self.player.getX(), self.player.getY(), self.player.getZ())
        hpr = Vec3(self.player.getH(), 0, 0)
        self.explosion_model.setPosHpr(pos, hpr)
        self.player.hide()
        taskMgr.add(self.expandExplosion, "expandExplosion")

    def expandExplosion(self, Task):
        if self.explosion_model.getScale() < VBase3(60.0, 60.0, 60.0):
            factor = globalClock.getDt()
            scale = self.explosion_model.getScale()
            scale += VBase3(factor*40, factor*40, factor*40)
            self.explosion_model.setScale(scale)
            return Task.cont
        else:
            self.explosion_model.setScale(0)
            self.exploding = False
            self.resetPlayer()

    def updatePlayer(self):
        # Global Clock
        # by default, panda runs as fast as it can frame by frame
        scale_factor = (globalClock.getDt()*self.speed)
        climb_factor = scale_factor * 0.5
        bank_factor = scale_factor
        speed_factor = scale_factor * 2.9
        gravity_factor = 2 * (self.max_speed - self.speed) / 100

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
        if not self.exploding:
            self.player.setX(self.player, -speed_factor)
            self.applyBoundaries()
            self.player.setZ(self.player, -gravity_factor)

    def applyBoundaries(self):
        # respet max camera distance else you
        # cannot see the floor post loop the loop
        if self.player.getZ() > self.max_distance:
            self.player.setZ(self.max_distance)
        # should never happen once we add collusion, but in case:
        elif self.player.getZ() < 0:
            self.player.setZ(0)

        boundary = False

        # and now the X/Y world boundaries:
        if self.player.getX() < 0:
            self.player.setX(0)
            boundary = True
        elif self.player.getX() > self.world_size:
            self.player.setX(self.world_size)
            boundary = True

        if self.player.getY() < 0:
            self.player.setY(0)
            boundary = True
        elif self.player.getY() > self.world_size:
            self.player.setY(self.world_size)
            boundary = True

        # Avoid doing this every frame
        if boundary and self.text_counter > 30:
            self.status_label.setText("STATUS: MAP END; TURN AROUND")
        elif self.text_counter > 30:
            self.status_label.setText("STATUS: OK")

        if self.text_counter > 30:
            self.text_counter = 0
        else:
            self.text_counter += 1

    def updateCamera(self):
        self.camera.setPos(self.player, 25.6225, 3.8807, 10.2779)
        self.camera.setHpr(self.player, 94.8996, -16.6549, 1.55508)

    def createEnvironment(self):
        # Fog to hide a performance tweak
        exp_fog = Fog("scene-wide-fog")
        exp_fog.setColor(1, 0.8, 0.8)
        exp_fog.setExpDensity(0.002)
        render.setFog(exp_fog)
        # base.setBackgroundColor(*colour)

        # Sky Dome
        '''
        sky_dome = loader.loadModel("models/sky")      # sky_sphere.egg by default
        sky_dome.setEffect(CompassEffect.make(self.render))
        sky_dome.setScale(self.max_distance / 2)
        sky_dome.setZ(-65)  # sink it
        # NOT render - you'll fly through the sky!
        sky_dome.reparentTo(self.camera)
        '''

        # Sky Sphere
        sky_sphere = self.loader.loadModel("models/sky_sphere")
        sky_sphere.setEffect(CompassEffect.make(self.render))
        sky_sphere.setScale(0.08)
        sky_sphere.reparentTo(self.camera)

        # Lighting
        ambient_light = AmbientLight("ambientLight")
        ambient_colour = Vec4(0.6, 0.6, 0.6, 1)
        ambient_light.setColor(ambient_colour)
        self.render.setLight(self.render.attachNewNode(ambient_light))

        directional_light = DirectionalLight("directionalLight")
        # direction = Vec3(0, -10, -10)
        # directional_light.setDirection(direction)
        directional_colour = Vec4(0.8, 0.8, 0.5, 1)
        directional_light.setColor(directional_colour)

        # directional_specular = Vec4(1, 1, 1, 1)
        # directional_light.setSpecularColor(directional_specular)

        dir_light_np = self.render.attachNewNode(directional_light)
        dir_light_np.setPos(0, 0, 260)
        dir_light_np.lookAt(self.player)
        self.render.setLight(dir_light_np)

        # Water
        self.water = self.loader.loadModel("models/square")
        self.water.setSx(self.world_size*2)
        self.water.setSy(self.world_size*2)
        self.water.setPos(self.world_size/2, self.world_size/2, 25)   # z is sea level
        self.water.setTransparency(TransparencyAttrib.MAlpha)
        newTS = TextureStage("1")
        self.water.setTexture(newTS, self.loader.loadTexture("models/water.png"))
        self.water.setTexScale(newTS, 4)
        self.water.reparentTo(self.render)
        LerpTexOffsetInterval(self.water, 200, (1,0), (0,0), textureStage=newTS).loop()

    def setupCollisions(self):
        self.coll_trav = CollisionTraverser()

        self.player_ground_sphere = CollisionSphere(0, 1.5, -1.5, 1.5)
        self.player_ground_col = CollisionNode('playerSphere')
        self.player_ground_col.addSolid(self.player_ground_sphere)

        # bitmasks
        self.player_ground_col.setFromCollideMask(BitMask32.bit(0))
        self.player_ground_col.setIntoCollideMask(BitMask32.allOff())
        self.world.setCollideMask(BitMask32.bit(0))
        self.water.setCollideMask(BitMask32.bit(0))

        # and done
        self.player_ground_col_np = self.player.attachNewNode(self.player_ground_col)
        self.player_ground_handler = CollisionHandlerQueue()
        self.coll_trav.addCollider(self.player_ground_col_np, self.player_ground_handler)

        # DEBUG
        if self.debug:
            self.player_ground_col_np.show()
            self.coll_trav.showCollisions(self.render)


game = DemoGame()
game.run()

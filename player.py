from panda3d.core import Vec3
from direct.task import Task
from pandac.PandaModules import VBase3

class AlliedFlanker():
    def __init__(self, loader, scene_graph, task_mgr):
        self.loader = loader
        self.render = scene_graph
        self.taskMgr = task_mgr
        self.max_speed = 200.0
        self.speed = 0.0
        self.start_pos = Vec3(200, 200, 100)
        self.start_hpr = Vec3(225, 0, 0)
        self.player.setScale(0.2, 0.2, 0.2)
        self.player.reparentTo(self.render)
        self.reset()
        self.calculate()

        # load explosion
        self.explosion_model = self.loader.loadModel("models/explosion")
        self.explosion_model.reparentTo(self.render)
        self.explosion_model.setScale(0.0)
        self.explosion_model.setLightOff()
        # only one explosion at a time
        self.exploding = False
        self.max_height = 400

    def setMaxHeight(self, height):
        self.max_height = height

    def reset(self):
        self.player.show()
        self.player.setPos(self.start_pos)
        self.player.setHpr(self.start_hpr)
        self.speed = self.max_speed / 5

    def calculate(self):
        self.factor = globalClock.getDt()
        self.scale_factor = self.factor * self.speed
        self.climb_factor = self.scale_factor * 0.3
        self.bank_factor = self.scale_factor
        self.speed_factor = self.scale_factor * 2.9
        self.gravity_factor = 1.35 * (self.max_speed - self.speed)/100

    def climb(self):
        if self.speed > 0:
            self.player.setFluidZ(self.player.getZ() + self.climb_factor)
            self.player.setR(self.player.getR() + 0.5 * self.climb_factor)
            if self.player.getR() >= 180:
                self.player.setR(-180)

    def dive(self):
        if self.speed > 0:
            self.player.setFluidZ(self.player.getZ() - self.climb_factor)
            self.player.setR(self.player.getR() - 0.5 * self.climb_factor)
            if self.player.getR() <= -180:
                self.player.setR(180)

    def unwindVertical(self):
        if self.player.getR() > 0:
            self.player.setR(self.player.getR() - (self.climb_factor + 0.1))
            if self.player.getR() < 0:
                self.player.setR(0)
        elif self.player.getR() > 0:
            self.player.setR(self.player.getR() + (self.climb_factor + 0.1))
            if self.player.getR() > 0:
                self.player.setR(0)

    def bankLeft(self):
        if self.speed > 0:
            self.player.setH(self.player.getH() + self.bank_factor)
            self.player.setP(self.player.getP() + self.bank_factor)
            if self.player.getP() >= 180:
                self.player.setP(-180)

    def bankRight(self):
        if self.speed < 0:
            self.player.setH(self.player.getH() - self.bank_factor)
            self.player.setP(self.player.getP() - self.bank_factor)
            if self.player.getP() <= -180:
                self.player.setP(180)

    def unwindHorizontal(self):
        if self.player.getP() > 0:
            self.player.setP(self.player.getP() - (self.player.bank_factor + 0.1))
            if self.player.getP() < 0:
                self.player.setP(0)
        elif self.player.getP() < 0:
            self.player.setP(self.player.getP() + (self.player.bank_factor + 0.1))
            if self.player.getP() > 0:
                self.player.setP(0)

    def move(self, bounding_box):
        valid = True
        if not self.exploding:
            self.player.setFluidX(self.player, -self.player.speed_factor)
            valid = self.__inBounds(bounding_box)
            self.player.setFluidZ(self.player, -self.gravity_factor)
        return valid

    def __inBounds(self, bounding_box):
        if self.player.getZ() > self.max_height:
            self.player.setZ(self.max_height)
        elif self.player.getZ() < 0:
            self.player.setZ(0)

        valid = True
        if self.player.getX() < 0:
            self.player.setX(0)
            valid = False
        elif self.player.getX() > bounding_box:
            self.player.setX(bounding_box)
            valid = False
        if self.player.getY() < 0:
            self.player.setY(0)
            valid = False
        elif self.player.getY() > bounding_box:
            self.player.setY(bounding_box)
            valid = False
        return valid

    def accelerate(self):
        self.speed += 1
        if self.speed > self.max_speed:
            self.speed = self.max_speed

    def brake(self):
        self.speed -= 1
        if self.speed < 0.0:
            self.speed = 0.0

    def die(self):
        if not self.exploding:
            self.player.setZ(self.player.getZ() + 10)
            self.exploding = True
            self.explosion_model.setPosHpr(Vec3(self.player.getX(), self.player.getY(), self.player.getZ()),
                                           Vec3(self.player.getH(), self.player.getP(), self.player.getR()))
            self.player.hide()
            self.taskMgr.add(self.__expand_explosion, "expandExplosion")

    def __expand_explosion(self, Task):
        if self.explosion_model.getScale() < VBase3(60.0, 60.0, 60.0):
            scale = self.explosion_model.getScale()
            scale = scale + VBase3(self.factor*40, self.factor*40, self.factor*40)
            self.explosion_model.setScale(scale)
            return Task.cont
        else:
            self.explosion_model.setScale(0)
            self.exploding = False
            self.reset()

    def __speed_as_percentage(self):
        return self.speed / self.max_speed

    def attach(self, node):
        return self.player.attachNewNode(node)

    def lookAtMe(self, camera):
        percent = self.__speed_as_percentage() * 2
        camera.setPos(self.player, 9+(20*percent), 0, 0)
        camera.setH(self.player.getH() + 90)
        camera.setP(self.player.getR())
        camera.setR(self.player.getP())
        camera.setZ(self.player, 3)
        camera.setY(self.player, 1.5)

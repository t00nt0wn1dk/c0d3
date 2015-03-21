from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.toon import DistributedToon
from direct.controls import ControlManager
from direct.showbase.InputStateGlobal import inputState
from direct.controls.GravityWalker import GravityWalker
from direct.controls.SwimWalker import SwimWalker
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import *
import math
from direct.task import Task

class LocalToon(DistributedToon.DistributedToon):

    def __init__(self, cr):
        try:
            self.LocalToon_initialized
        except:
            self.LocalToon_initialized = 1
            DistributedToon.DistributedToon.__init__(self, cr)
            self.soundRun = base.loadSfx('phase_3.5/audio/sfx/AV_footstep_runloop.wav')
            self.soundWalk = base.loadSfx('phase_3.5/audio/sfx/AV_footstep_walkloop.wav')
            newScale = oldScale = 0.8
            self.cTrav = CollisionTraverser('base.cTrav')
            base.pushCTrav(self.cTrav)
            self.cTrav.setRespectPrevTransform(1)
            self.avatarControlsEnabled = 0
            self.controlManager = ControlManager.ControlManager(True, False)
            self.setupControls()
            self.initializeSmartCamera()
            self.cameraPositions = []
            self.animMultiplier = 1.0
            self.runTimeout = 2.5
            self.isPageUp = 0
            self.isPageDown = 0
            self.movingFlag = 0
            self.swimmingFlag = 0
            self.lastNeedH = None
            self.jumpLandAnimFixTask = None
            self.fov = DefaultCameraFov
            self.accept('avatarMoving', self.clearPageUpDown)

    def wantLegacyLifter(self):
        return True

    def allowHardLand(self):
        return True

    def getAutoRun(self):
        return False

    def announceGenerate(self):
        self.startLookAround()
        DistributedToon.DistributedToon.announceGenerate(self)
        toonGeom = self.getGeomNode()

    def disable(self):
        self.ignoreAll()
        DistributedToon.DistributedToon.disable(self)

    def disableBodyCollisions(self):
        return None

    def delete(self):
        try:
            self.LocalToon_deleted
        except:
            self.LocalToon_deleted = 1
            DistributedToon.DistributedToon.delete(self)
            self.ignoreAll()
            self.stopJumpLandTask()
            base.popCTrav()
            taskMgr.remove('posCamera')
            self.disableAvatarControls()
            self.stopTrackAnimToSpeed()
            self.stopUpdateSmartCamera()
            self.shutdownSmartCamera()
            self.deleteCollisions()
            self.controlManager.delete()
            self.physControls = None
            del self.controlManager
            taskMgr.remove(self.uniqueName('walkReturnTask'))
            del self.soundRun
            del self.soundWalk

    def isLocal(self):
        return 1

    def getAirborneHeight(self):
        return (base.localAvatar.getHeight() + 0.025)

    def walkSound(self):
        self.soundRun.stop()
        base.playSfx(self.soundWalk, looping=1)

    def runSound(self):
        self.soundWalk.stop()
        base.playSfx(self.soundRun, looping=1)

    def setupControls(self):
        walkControls = GravityWalker(legacyLifter=self.wantLegacyLifter())
        walkControls.setWallBitMask(WallBitmask)
        walkControls.setFloorBitMask(FloorBitmask)
        walkControls.initializeCollisions(
            self.cTrav, self, avatarRadius=AvatarDefaultRadius, floorOffset=FloorOffset, reach=4
        )
        walkControls.setAirborneHeightFunc(self.getAirborneHeight)
        self.physControls = walkControls
        self.controlManager.add(walkControls, 'walk')
        swimControls = SwimWalker()
        swimControls.setWallBitMask(WallBitmask)
        swimControls.setFloorBitMask(FloorBitmask)
        swimControls.initializeCollisions(
            self.cTrav, self, avatarRadius=AvatarDefaultRadius, floorOffset=FloorOffset, reach=4
        )
        swimControls.setAirborneHeightFunc(self.getAirborneHeight)
        self.controlManager.add(swimControls, 'swim')
        self.controlManager.use('walk', self)
        self.controlManager.disable()

    def initializeSmartCamera(self):
        self.__idealCameraObstructed = 0
        self.closestObstructionDistance = 0.0
        self.cameraIndex = 0
        self.auxCameraPositions = []
        self.cameraZOffset = 0.0
        self.__onLevelGround = 0
        self.__camCollCanMove = 0
        self.__geom = render
        self.__disableSmartCam = 0
        self.initializeSmartCameraCollisions()
        self._smartCamEnabled = False

    def initializeSmartCameraCollisions(self):
        self.ccTrav = CollisionTraverser('LocalToon.ccTrav')
        self.ccLine = CollisionSegment(0, 0, 0, 1, 0, 0)
        self.ccLineNode = CollisionNode('ccLineNode')
        self.ccLineNode.addSolid(self.ccLine)
        self.ccLineNodePath = self.attachNewNode(self.ccLineNode)
        self.ccLineBitMask = CameraBitmask
        self.ccLineNode.setFromCollideMask(self.ccLineBitMask)
        self.ccLineNode.setIntoCollideMask(BitMask32.allOff())
        self.camCollisionQueue = CollisionHandlerQueue()
        self.ccTrav.addCollider(self.ccLineNodePath, self.camCollisionQueue)
        self.ccSphere = CollisionSphere(0, 0, 0, 1)
        self.ccSphereNode = CollisionNode('ccSphereNode')
        self.ccSphereNode.addSolid(self.ccSphere)
        self.ccSphereNodePath = base.camera.attachNewNode(self.ccSphereNode)
        self.ccSphereNode.setFromCollideMask(CameraBitmask)
        self.ccSphereNode.setIntoCollideMask(BitMask32.allOff())
        self.camPusher = CollisionHandlerPusher()
        self.camPusher.addCollider(self.ccSphereNodePath, base.camera)
        self.camPusher.setCenter(self)
        self.ccPusherTrav = CollisionTraverser('LocalToon.ccPusherTrav')
        self.ccSphere2 = self.ccSphere
        self.ccSphereNode2 = CollisionNode('ccSphereNode2')
        self.ccSphereNode2.addSolid(self.ccSphere2)
        self.ccSphereNodePath2 = base.camera.attachNewNode(self.ccSphereNode2)
        self.ccSphereNode2.setFromCollideMask(CameraBitmask)
        self.ccSphereNode2.setIntoCollideMask(BitMask32.allOff())
        self.camPusher2 = CollisionHandlerPusher()
        self.ccPusherTrav.addCollider(self.ccSphereNodePath2, self.camPusher2)
        self.camPusher2.addCollider(self.ccSphereNodePath2, base.camera)
        self.camPusher2.setCenter(self)
        self.camFloorRayNode = self.attachNewNode('camFloorRayNode')
        self.ccRay = CollisionRay(0.0, 0.0, 0.0, 0.0, 0.0, -1.0)
        self.ccRayNode = CollisionNode('ccRayNode')
        self.ccRayNode.addSolid(self.ccRay)
        self.ccRayNodePath = self.camFloorRayNode.attachNewNode(self.ccRayNode)
        self.ccRayBitMask = FloorBitmask
        self.ccRayNode.setFromCollideMask(self.ccRayBitMask)
        self.ccRayNode.setIntoCollideMask(BitMask32.allOff())
        self.ccTravFloor = CollisionTraverser('LocalToon.ccTravFloor')
        self.camFloorCollisionQueue = CollisionHandlerQueue()
        self.ccTravFloor.addCollider(self.ccRayNodePath, self.camFloorCollisionQueue)
        self.ccTravOnFloor = CollisionTraverser('LocalToon.ccTravOnFloor')
        self.ccRay2 = CollisionRay(0.0, 0.0, 0.0, 0.0, 0.0, -1.0)
        self.ccRay2Node = CollisionNode('ccRay2Node')
        self.ccRay2Node.addSolid(self.ccRay2)
        self.ccRay2NodePath = self.camFloorRayNode.attachNewNode(self.ccRay2Node)
        self.ccRay2BitMask = FloorBitmask
        self.ccRay2Node.setFromCollideMask(self.ccRay2BitMask)
        self.ccRay2Node.setIntoCollideMask(BitMask32.allOff())
        self.ccRay2MoveNodePath = hidden.attachNewNode('ccRay2MoveNode')
        self.camFloorCollisionBroadcaster = CollisionHandlerFloor()
        self.camFloorCollisionBroadcaster.setInPattern('on-floor')
        self.camFloorCollisionBroadcaster.setOutPattern('off-floor')
        self.camFloorCollisionBroadcaster.addCollider(self.ccRay2NodePath, self.ccRay2MoveNodePath)

    def deleteSmartCameraCollisions(self):
        del self.ccTrav
        del self.ccLine
        del self.ccLineNode
        self.ccLineNodePath.removeNode()
        del self.ccLineNodePath
        del self.camCollisionQueue
        del self.ccRay
        del self.ccRayNode
        self.ccRayNodePath.removeNode()
        del self.ccRayNodePath
        del self.ccRay2
        del self.ccRay2Node
        self.ccRay2NodePath.removeNode()
        del self.ccRay2NodePath
        self.ccRay2MoveNodePath.removeNode()
        del self.ccRay2MoveNodePath
        del self.ccTravOnFloor
        del self.ccTravFloor
        del self.camFloorCollisionQueue
        del self.camFloorCollisionBroadcaster
        del self.ccSphere
        del self.ccSphereNode
        self.ccSphereNodePath.removeNode()
        del self.ccSphereNodePath
        del self.camPusher
        del self.ccPusherTrav
        del self.ccSphere2
        del self.ccSphereNode2
        self.ccSphereNodePath2.removeNode()
        del self.ccSphereNodePath2
        del self.camPusher2

    def attachCamera(self):
        base.disableMouse()
        camera.reparentTo(self)
        camera.setPos(0, -10.0 - 3.2375, 3.2375)
        self.setWalkSpeedNormal()

    def collisionsOff(self):
        self.controlManager.collisionsOff()

    def collisionsOn(self):
        self.controlManager.collisionsOn()

    def clearPageUpDown(self):
        if self.isPageDown or self.isPageUp:
            self.lerpCameraFov(self.fov, 0.6)
            self.isPageDown = 0
            self.isPageUp = 0
            self.setCameraPositionByIndex(self.cameraIndex)

    def addCameraPosition(self, camPos):
        if camPos == None:
            lookAtNP = self.attachNewNode('lookAt')
            lookAtNP.setPos(base.cam, 0, 1, 0)
            lookAtPos = lookAtNP.getPos()
            camHeight = self.getClampedAvatarHeight()
            camPos = (
                base.cam.getPos(self), lookAtPos,
                Point3(0.0, 1.5, (camHeight * 4.0)),
                Point3(0.0, 1.5, (camHeight * -1.0)), 1
            )
            lookAtNP.removeNode()
        self.auxCameraPositions.append(camPos)
        self.cameraPositions.append(camPos)

    def deleteCollisions(self):
        self.controlManager.deleteCollisions()
        self.ignore('entero157')
        del self.cTrav

    def disableAvatarControls(self):
        if not self.avatarControlsEnabled:
            return None
        self.avatarControlsEnabled = 0
        self.ignoreAnimationEvents()
        self.controlManager.disable()
        self.clearPageUpDown()

    def enableAvatarControls(self):
        if self.avatarControlsEnabled:
            return None
        self.avatarControlsEnabled = 1
        self.setupAnimationEvents()
        self.controlManager.enable()

    def disableRun(self):
        self.ignore('arrow_up')
        self.ignore('arrow_up-up')
        self.ignore('control-arrow_up')
        self.ignore('control-arrow_up-up')
        self.ignore('alt-arrow_up')
        self.ignore('alt-arrow_up-up')
        self.ignore('shift-arrow_up')
        self.ignore('shift-arrow_up-up')

    def enableRun(self):
        self.accept('arrow_up', self.startRunWatch)
        self.accept('arrow_up-up', self.stopRunWatch)
        self.accept('control-arrow_up', self.startRunWatch)
        self.accept('control-arrow_up-up', self.stopRunWatch)
        self.accept('alt-arrow_up', self.startRunWatch)
        self.accept('alt-arrow_up-up', self.stopRunWatch)
        self.accept('shift-arrow_up', self.startRunWatch)
        self.accept('shift-arrow_up-up', self.stopRunWatch)

    def disableSmartCameraViews(self):
        self.ignore('tab')
        self.ignore('shift-tab')
        self.ignore('page_up')
        self.ignore('page_down')
        self.ignore('page_down-up')

    def enableSmartCameraViews(self):
        self.accept('tab', self.nextCameraPos, [1])
        self.accept('shift-tab', self.nextCameraPos, [0])
        self.accept('page_up', self.pageUp)
        self.accept('page_down', self.pageDown)

    def getAnimMultiplier(self):
        return self.animMultiplier

    def getClampedAvatarHeight(self):
        return max(self.getHeight(), 3.0)

    def getCompromiseCameraPos(self):
        if self.__idealCameraObstructed == 0:
            compromisePos = self.getIdealCameraPos()
        else:
            visPnt = self.getVisibilityPoint()
            idealPos = self.getIdealCameraPos()
            distance = Vec3(idealPos - visPnt).length()
            ratio = self.closestObstructionDistance/distance
            compromisePos = ((idealPos * ratio) + (visPnt * (1 - ratio)))
            liftMult = (1.0 - (ratio * ratio))
            compromisePos = Point3(
                compromisePos[0], compromisePos[1], (compromisePos[2] + ((self.getHeight() * 0.4) * liftMult))
            )
        compromisePos.setZ(compromisePos[2] + self.cameraZOffset)
        return compromisePos

    def getIdealCameraPos(self):
        return Point3(self.__idealCameraPos)

    def getLookAtPoint(self):
        return Point3(self.__curLookAt)

    def getVisibilityPoint(self):
        return Point3(0.0, 0.0, self.getHeight())

    def handleCameraFloorInteraction(self):
        self.putCameraFloorRayOnCamera()
        self.ccTravFloor.traverse(self.__geom)
        if self.__onLevelGround:
            return None
        if self.camFloorCollisionQueue.getNumEntries() == 0:
            return None
        self.camFloorCollisionQueue.sortEntries()
        camObstrCollisionEntry = self.camFloorCollisionQueue.getEntry(0)
        camHeightFromFloor = camObstrCollisionEntry.getSurfacePoint(self.ccRayNodePath)[2]
        self.cameraZOffset = (camera.getPos()[2] + camHeightFromFloor)
        if self.cameraZOffset < 0:
            self.cameraZOffset = 0
        if self.__floorDetected == 0:
            self.__floorDetected = 1
            self.popCameraToDest()

    def handleCameraObstruction(self, camObstrCollisionEntry):
        collisionPoint = camObstrCollisionEntry.getSurfacePoint(self.ccLineNodePath)
        collisionVec = Vec3(collisionPoint - self.ccLine.getPointA())
        distance = collisionVec.length()
        self.__idealCameraObstructed = 1
        self.closestObstructionDistance = distance
        self.popCameraToDest()

    def hasTrackAnimToSpeed(self):
        taskName = self.taskName('trackAnimToSpeed')
        return taskMgr.hasTaskNamed(taskName)

    def ignoreAnimationEvents(self):
        self.ignore('jumpStart')
        self.ignore('jumpHardLand')
        self.ignore('jumpLand')

    def initCameraPositions(self):
        camHeight = self.getClampedAvatarHeight()
        heightScaleFactor = (camHeight * (1.0/3.0))
        defLookAt = Point3(0.0, 1.5, camHeight)
        scXoffset = 3.0
        scPosition = (Point3((scXoffset - 1), -10.0, (camHeight + 5.0)), Point3(scXoffset, 2.0, camHeight))
        self.cameraPositions = ([
            (
                Point3(0.0, (-11.0 * heightScaleFactor), camHeight),
                defLookAt,
                Point3(0.0, camHeight, (camHeight * 4.0)),
                Point3(0.0, camHeight, (camHeight * -1.0)),
                0
            ),
            (
                Point3((5.7 * heightScaleFactor), (7.65 * heightScaleFactor), (camHeight + 2.0)),
                Point3(0.0, 1.0, camHeight),
                Point3(0.0, 1.0, (camHeight * 4.0)),
                Point3(0.0, 1.0, (camHeight * -1.0)),
                0
            ),
            (
                Point3(0.0, (-24.0 * heightScaleFactor), (camHeight + 4.0)),
                defLookAt,
                Point3(0.0, 1.5, (camHeight * 4.0)),
                Point3(0.0, 1.5, (camHeight * -1.0)),
                0
            ),
            (
                Point3(0.0, (-12.0 * heightScaleFactor), (camHeight + 4.0)),
                defLookAt,
                Point3(0.0, 1.5, (camHeight * 4.0)),
                Point3(0.0, 1.5, (camHeight * -1.0)),
                0
            )
        ] + self.auxCameraPositions)

    def d_broadcastPositionNow(self):
        self.d_clearSmoothing()
        self.d_broadcastPosHpr()

    def jumpHardLand(self):
        if self.allowHardLand():
            self.b_setAnimState('jumpLand', 1.0)
            self.stopJumpLandTask()
            self.jumpLandAnimFixTask = self.jumpLandAnimFix(1.0)
        if self.d_broadcastPosHpr:
            self.d_broadcastPosHpr()

    def jumpLand(self):
        self.jumpLandAnimFixTask = self.jumpLandAnimFix(0.01)
        if self.d_broadcastPosHpr:
            self.d_broadcastPosHpr()

    def jumpLandAnimFix(self, jumpTime):
        if (self.playingAnim != 'run') and (self.playingAnim != 'walk'):
            return taskMgr.doMethodLater(jumpTime, self.returnToWalk, self.uniqueName('walkReturnTask'))

    def jumpStart(self):
        self.b_setAnimState('jumpAirborne', 1.0)
        self.stopJumpLandTask()

    def lerpCameraFov(self, fov, time):
        taskMgr.remove('cam-fov-lerp-play')
        oldFov = base.camLens.getHfov()
        if abs(fov - oldFov) > 0.1:
            def setCamFov(fov):
                base.camLens.setFov(fov)

            self.camLerpInterval = LerpFunctionInterval(
                setCamFov, fromData=oldFov, toData=fov, duration=time, name='cam-fov-lerp'
            )
            self.camLerpInterval.start()

    def nextCameraPos(self, forward):
        if not self.avatarControlsEnabled:
            return None
        self.__cameraHasBeenMoved = 1
        if forward:
            self.cameraIndex += 1
            if self.cameraIndex > (len(self.cameraPositions) - 1):
                self.cameraIndex = 0
        else:
            self.cameraIndex -= 1
            if self.cameraIndex < 0:
                self.cameraIndex = (len(self.cameraPositions) - 1)
        self.setCameraPositionByIndex(self.cameraIndex)

    def nudgeCamera(self):
        CLOSE_ENOUGH = 0.1
        curCamPos = self.__instantaneousCamPos
        curCamHpr = camera.getHpr()
        targetCamPos = self.getCompromiseCameraPos()
        targetCamLookAt = self.getLookAtPoint()
        posDone = 0
        if ((Vec3((curCamPos - targetCamPos)).length() <= CLOSE_ENOUGH) and camera.setPos(targetCamPos)):
            posDone = 1
        camera.setPos(targetCamPos)
        camera.lookAt(targetCamLookAt)
        targetCamHpr = camera.getHpr()
        hprDone = 0
        if (Vec3((curCamHpr - targetCamHpr)).length() <= CLOSE_ENOUGH):
            hprDone = 1
        if posDone and hprDone:
            return None
        lerpRatio = 0.15
        lerpRatio = (1 - pow((1 - lerpRatio), (globalClock.getDt() * 30.0)))
        self.__instantaneousCamPos = ((targetCamPos * lerpRatio) + (curCamPos * (1 - lerpRatio)))

    def pageDown(self):
        if not self.avatarControlsEnabled:
            return None
        if not self.isPageDown:
            self.isPageUp = 0
            self.isPageDown = 1
            self.lerpCameraFov(70, 0.6)
            self.setCameraPositionByIndex(self.cameraIndex)
        else:
            self.clearPageUpDown()

    def pageUp(self):
        if not self.avatarControlsEnabled:
            return None
        if not self.isPageUp:
            self.isPageDown = 0
            self.isPageUp = 1
            self.lerpCameraFov(70, 0.6)
            self.setCameraPositionByIndex(self.cameraIndex)
        else:
            self.clearPageUpDown()

    def popCameraToDest(self):
        newCamPos = self.getCompromiseCameraPos()
        newCamLookAt = self.getLookAtPoint()
        self.positionCameraWithPusher(newCamPos, newCamLookAt)
        self.__instantaneousCamPos = camera.getPos()

    def posCamera(self, lerp, time):
        if not lerp:
            self.positionCameraWithPusher(self.getCompromiseCameraPos(), self.getLookAtPoint())
        else:
            camPos = self.getCompromiseCameraPos()
            savePos = camera.getPos()
            saveHpr = camera.getHpr()
            self.positionCameraWithPusher(camPos, self.getLookAtPoint())
            x = camPos[0]
            y = camPos[1]
            z = camPos[2]
            destHpr = camera.getHpr()
            h = destHpr[0]
            p = destHpr[1]
            r = destHpr[2]
            camera.setPos(savePos)
            camera.setHpr(saveHpr)
            taskMgr.remove('posCamera')
            camera.lerpPosHpr(x, y, z, h, p, r, time, task='posCamera')

    def positionCameraWithPusher(self, pos, lookAt):
        camera.setPos(pos)
        self.ccPusherTrav.traverse(self.__geom)
        camera.lookAt(lookAt)

    def putCameraFloorRayOnAvatar(self):
        self.camFloorRayNode.setPos(self, 0, 0, 5)

    def putCameraFloorRayOnCamera(self):
        self.camFloorRayNode.setPos(self.ccSphereNodePath, 0, 0, 0)

    def recalcCameraSphere(self):
        nearPlaneDist = base.camLens.getNear()
        hFov = base.camLens.getHfov()
        vFov = base.camLens.getVfov()
        hOff = (nearPlaneDist * math.tan(deg2Rad((hFov / 2.0))))
        vOff = (nearPlaneDist * math.tan(deg2Rad((vFov / 2.0))))
        camPnts = [Point3(hOff, nearPlaneDist, vOff),
         Point3(-hOff, nearPlaneDist, vOff),
         Point3(hOff, nearPlaneDist, -vOff),
         Point3(-hOff, nearPlaneDist, -vOff),
         Point3(0.0, 0.0, 0.0)]
        avgPnt = Point3(0.0, 0.0, 0.0)
        for camPnt in camPnts:
            avgPnt = (avgPnt + camPnt)
        avgPnt = (avgPnt / len(camPnts))
        sphereRadius = 0.0
        for camPnt in camPnts:
            dist = Vec3((camPnt - avgPnt)).length()
            if (dist > sphereRadius):
                sphereRadius = dist
        avgPnt = Point3(avgPnt)
        self.ccSphereNodePath.setPos(avgPnt)
        self.ccSphereNodePath2.setPos(avgPnt)
        self.ccSphere.setRadius(sphereRadius)

    def removeCameraPosition(self):
        if len(self.cameraPositions) > 1:
            camPos = self.cameraPositions[self.cameraIndex]
            if camPos in self.auxCameraPositions:
                self.auxCameraPositions.remove(camPos)
            if camPos in self.cameraPositions:
                self.cameraPositions.remove(camPos)
            self.nextCameraPos(1)

    def resetCameraPosition(self):
        self.cameraIndex = 0
        self.setCameraPositionByIndex(self.cameraIndex)

    def returnToWalk(self, task):
        self.b_setAnimState('Happy', 1.0)
        return Task.done

    def setAnimMultiplier(self, value):
        self.animMultiplier = value

    def setCameraCollisionsCanMove(self, flag):
        self.__camCollCanMove = flag

    def setCameraFov(self, fov):
        self.fov = fov
        if (not self.isPageDown) and (not self.isPageUp):
            base.camLens.setFov(self.fov)

    def setCameraPositionByIndex(self, index):
        self.setCameraSettings(self.cameraPositions[index])

    def setCameraSettings(self, camSettings):
        self.setIdealCameraPos(camSettings[0])
        if ((not self.isPageUp) and (not self.isPageDown)):
            self.__cameraHasBeenMoved = 1
            self.setLookAtPoint(camSettings[1])
        elif self.isPageUp:
            self.__cameraHasBeenMoved = 1
            self.setLookAtPoint(camSettings[2])
        elif self.isPageDown:
            self.__cameraHasBeenMoved = 1
            self.setLookAtPoint(camSettings[3])
        self.__disableSmartCam = camSettings[4]
        if self.__disableSmartCam:
            self.putCameraFloorRayOnAvatar()
            self.cameraZOffset = 0.0
        self.posCamera(1, 0.5)

    def setGeom(self, geom):
        self.__geom = geom

    def setIdealCameraPos(self, pos):
        self.__idealCameraPos = Point3(pos)
        self.updateSmartCameraCollisionLineSegment()

    def setLookAtPoint(self, la):
        self.__curLookAt = Point3(la)

    def setOnLevelGround(self, flag):
        self.__onLevelGround = flag

    def setupAnimationEvents(self):
        self.accept('jumpStart', self.jumpStart, [])
        self.accept('jumpHardLand', self.jumpHardLand, [])
        self.accept('jumpLand', self.jumpLand, [])

    def setWalkSpeedNormal(self):
        self.controlManager.setSpeeds(
            ToonForwardSpeed, ToonJumpForce, ToonReverseSpeed, ToonRotateSpeed
        )

    def setWalkSpeedSlow(self):
        self.controlManager.setSpeeds(
            ToonForwardSlowSpeed, ToonJumpSlowForce, ToonReverseSlowSpeed,  ToonRotateSlowSpeed
        )

    def shutdownSmartCamera(self):
        self.deleteSmartCameraCollisions()

    def startRunWatch(self):
        def setRun(ignored):
            messenger.send('running-on')

        taskMgr.doMethodLater(self.runTimeout, setRun, self.uniqueName('runWatch'))
        return Task.cont

    def startTrackAnimToSpeed(self):
        self.b_setAnimState('Happy')
        taskName = self.taskName('trackAnimToSpeed')
        taskMgr.remove(taskName)
        task = Task.Task(self.trackAnimToSpeed)
        self.lastMoved = globalClock.getFrameTime()
        self.lastState = None
        self.lastAction = None
        self.trackAnimToSpeed(task)
        taskMgr.add(self.trackAnimToSpeed, taskName, 35)

    def startUpdateSmartCamera(self, push):
        if self._smartCamEnabled:
            return None
        self._smartCamEnabled = True
        self.__floorDetected = 0
        self.__cameraHasBeenMoved = 0
        self.recalcCameraSphere()
        self.initCameraPositions()
        self.setCameraPositionByIndex(self.cameraIndex)
        self.posCamera(0, 0.0)
        self.__instantaneousCamPos = camera.getPos()
        if push:
            self.cTrav.addCollider(self.ccSphereNodePath, self.camPusher)
            self.ccTravOnFloor.addCollider(self.ccRay2NodePath, self.camFloorCollisionBroadcaster)
            self.__disableSmartCam = 0
        self.__lastPosWrtRender = camera.getPos(render)
        self.__lastHprWrtRender = camera.getHpr(render)
        taskName = self.taskName('updateSmartCamera')
        taskMgr.remove(taskName)
        taskMgr.add(self.updateSmartCamera, taskName, priority=47)
        self.enableSmartCameraViews()
        self.nudgeCamera()

    def stopJumpLandTask(self):
        if self.jumpLandAnimFixTask:
            self.jumpLandAnimFixTask.remove()
            self.jumpLandAnimFixTask = None

    def stopRunWatch(self):
        taskMgr.remove(self.uniqueName('runWatch'))
        messenger.send('running-off')
        return Task.cont

    def stopSound(self):
        self.soundRun.stop()
        self.soundWalk.stop()

    def stopTrackAnimToSpeed(self):
        taskName = self.taskName('trackAnimToSpeed')
        taskMgr.remove(taskName)
        self.stopSound()

    def stopUpdateSmartCamera(self):
        if self._smartCamEnabled:
            return None
        self.disableSmartCameraViews()
        self.cTrav.removeCollider(self.ccSphereNodePath)
        self.ccTravOnFloor.removeCollider(self.ccRay2NodePath)
        if base.localAvatar.isEmpty():
            self.putCameraFloorRayOnAvatar()
        taskName = self.taskName('updateSmartCamera')
        taskMgr.remove(taskName)
        self._smartCamEnabled = False

    def trackAnimToSpeed(self, task):
        speed, rotSpeed, slideSpeed = self.controlManager.getSpeeds()
        if (speed != 0.0) or (rotSpeed != 0.0):
            if inputState.isSet('jump') and (not self.movingFlag):
                self.movingFlag = 1
                self.stopLookAround()
            elif (not inputState.isSet('jump')) and self.movingFlag:
                self.movingFlag = 0
                self.startLookAround()
        action = self.setSpeed(speed, rotSpeed)
        if action != self.lastAction:
            self.lastAction = action
            self.stopSound()
            if (action == WALK_INDEX) or (action == REVERSE_INDEX):
                self.walkSound()
            elif action == RUN_INDEX:
                self.runSound()
        return Task.cont

    def travCollisionsFloor(self, n):
        if n == None:
            n = self.__geom
        self.ccTravFloor.traverse(n)

    def travCollisionsLOS(self, n):
        if n == None:
            n = self.__geom
        self.ccTrav.traverse(n)

    def travCollisionsPusher(self, n):
        if n == None:
            n = self.__geom
        self.ccPusherTrav.traverse(n)

    def updateSmartCamera(self, task):
        if (not self.__camCollCanMove) and (not self.__cameraHasBeenMoved):
            if self.__lastPosWrtRender == camera.getPos(render):
                if self.__lastHprWrtRender == camera.getHpr(render):
                    return Task.cont
        self.__cameraHasBeenMoved = 0
        self.__lastPosWrtRender = camera.getPos(render)
        self.__lastHprWrtRender = camera.getHpr(render)
        self.__idealCameraObstructed = 0
        if not self.__disableSmartCam:
            self.ccTrav.traverse(self.__geom)
            if self.camCollisionQueue.getNumEntries() > 0:
                self.camCollisionQueue.sortEntries()
                self.handleCameraObstruction(self.camCollisionQueue.getEntry(0))
            if self.__onLevelGround:
                self.handleCameraFloorInteraction()
        if self.__idealCameraObstructed:
            self.nudgeCamera()
        if self.__disableSmartCam:
            self.ccPusherTrav.traverse(self.__geom)
            self.putCameraFloorRayOnCamera()
        self.ccTravOnFloor.traverse(self.__geom)
        return Task.cont

    def updateSmartCameraCollisionLineSegment(self):
        pointB = self.getIdealCameraPos()
        pointA = self.getVisibilityPoint()
        vectorAB = Vec3((pointB - pointA))
        lengthAB = vectorAB.length()
        if lengthAB > 0.001:
            self.ccLine.setPointA(pointA)
            self.ccLine.setPointB(pointB)

    def useWalkControls(self):
        self.controlManager.use('walk', self)

    def useSwimControls(self):
        self.controlManager.use('swim', self)

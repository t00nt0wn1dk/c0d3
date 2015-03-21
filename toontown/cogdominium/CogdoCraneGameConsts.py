# 2013.08.22 22:17:32 Pacific Daylight Time
# Embedded file name: toontown.cogdominium.CogdoCraneGameConsts
from direct.fsm.StatePush import StateVar
from otp.level.EntityStateVarSet import EntityStateVarSet
from toontown.cogdominium.CogdoEntityTypes import CogdoCraneGameSettings, CogdoCraneCogSettings
Settings = EntityStateVarSet(CogdoCraneGameSettings)
CogSettings = EntityStateVarSet(CogdoCraneCogSettings)
CranePosHprs = [(13.4, -136.6, 6, -45, 0, 0),
 (13.4, -91.4, 6, -135, 0, 0),
 (58.6, -91.4, 6, 135, 0, 0),
 (58.6, -136.6, 6, 45, 0, 0)]
MoneyBagPosHprs = [[77.2 - 84,
  -329.3 + 201,
  0,
  -90,
  0,
  0],
 [77.1 - 84,
  -302.7 + 201,
  0,
  -90,
  0,
  0],
 [165.7 - 84,
  -326.4 + 201,
  0,
  90,
  0,
  0],
 [165.5 - 84,
  -302.4 + 201,
  0,
  90,
  0,
  0],
 [107.8 - 84,
  -359.1 + 201,
  0,
  0,
  0,
  0],
 [133.9 - 84,
  -359.1 + 201,
  0,
  0,
  0,
  0],
 [107.0 - 84,
  -274.7 + 201,
  0,
  180,
  0,
  0],
 [134.2 - 84,
  -274.7 + 201,
  0,
  180,
  0,
  0]]
for i in xrange(len(MoneyBagPosHprs)):
    MoneyBagPosHprs[i][2] += 6
# okay decompyling C:\Users\Maverick\Documents\Visual Studio 2010\Projects\Unfreezer\py2\toontown\cogdominium\CogdoCraneGameConsts.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.08.22 22:17:32 Pacific Daylight Time
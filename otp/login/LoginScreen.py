# 2013.08.22 22:15:37 Pacific Daylight Time
# Embedded file name: otp.login.LoginScreen
import os
import time
from datetime import datetime
from pandac.PandaModules import *
from direct.distributed.MsgTypes import *
from direct.gui.DirectGui import *
from direct.fsm import StateData
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
from otp.otpgui import OTPDialog
from otp.otpbase import OTPLocalizer
from otp.otpbase import OTPGlobals
from otp.uberdog.AccountDetailRecord import AccountDetailRecord, SubDetailRecord
import TTAccount
import GuiScreen

class LoginScreen(StateData.StateData, GuiScreen.GuiScreen):
    __module__ = __name__
    AutoLoginName = base.config.GetString('%s-auto-login%s' % (game.name, os.getenv('otp_client', '')), '')
    AutoLoginPassword = base.config.GetString('%s-auto-password%s' % (game.name, os.getenv('otp_client', '')), '')
    notify = DirectNotifyGlobal.directNotify.newCategory('LoginScreen')
    ActiveEntryColor = Vec4(1, 1, 1, 1)
    InactiveEntryColor = Vec4(0.8, 0.8, 0.8, 1)

    def __init__(self, cr, doneEvent):
        self.notify.debug('__init__')
        StateData.StateData.__init__(self, doneEvent)
        GuiScreen.GuiScreen.__init__(self)
        self.cr = cr
        self.loginInterface = self.cr.loginInterface
        self.userName = ''
        self.password = ''
        self.fsm = ClassicFSM.ClassicFSM('LoginScreen', [State.State('off', self.enterOff, self.exitOff, ['login', 'waitForLoginResponse']),
         State.State('login', self.enterLogin, self.exitLogin, ['waitForLoginResponse', 'login', 'showLoginFailDialog']),
         State.State('showLoginFailDialog', self.enterShowLoginFailDialog, self.exitShowLoginFailDialog, ['login', 'showLoginFailDialog']),
         State.State('waitForLoginResponse', self.enterWaitForLoginResponse, self.exitWaitForLoginResponse, ['login', 'showLoginFailDialog', 'showConnectionProblemDialog']),
         State.State('showConnectionProblemDialog', self.enterShowConnectionProblemDialog, self.exitShowConnectionProblemDialog, ['login'])], 'off', 'off')
        self.fsm.enterInitialState()

    def load(self):
        self.notify.debug('load')
        masterScale = 0.8
        textScale = 0.1 * masterScale
        entryScale = 0.08 * masterScale
        lineHeight = 0.21 * masterScale
        buttonScale = 1.15 * masterScale
        buttonLineHeight = 0.14 * masterScale
        self.frame = DirectFrame(parent=aspect2d, relief=None, sortOrder=20)
        self.frame.hide()
        linePos = -0.26
        self.nameLabel = DirectLabel(parent=self.frame, relief=None, pos=(-0.21, 0, linePos), text=OTPLocalizer.LoginScreenUserName, text_scale=textScale, text_align=TextNode.ARight)
        self.nameEntry = DirectEntry(parent=self.frame, relief=DGG.SUNKEN, borderWidth=(0.1, 0.1), scale=entryScale, pos=(-0.125, 0.0, linePos), width=OTPGlobals.maxLoginWidth, numLines=1, focus=0, cursorKeys=1)
        linePos -= lineHeight
        self.passwordLabel = DirectLabel(parent=self.frame, relief=None, pos=(-0.21, 0, linePos), text=OTPLocalizer.LoginScreenPassword, text_scale=textScale, text_align=TextNode.ARight)
        self.passwordEntry = DirectEntry(parent=self.frame, relief=DGG.SUNKEN, borderWidth=(0.1, 0.1), scale=entryScale, pos=(-0.125, 0.0, linePos), width=OTPGlobals.maxLoginWidth, numLines=1, focus=0, cursorKeys=1, obscured=1, command=self.__handleLoginPassword)
        linePos -= lineHeight
        buttonImageScale = (1.7, 1.1, 1.1)
        self.loginButton = DirectButton(parent=self.frame, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0, linePos), scale=buttonScale, text=OTPLocalizer.LoginScreenLogin, text_scale=0.06, text_pos=(0, -0.02), command=self.__handleLoginButton)
        linePos -= buttonLineHeight
        self.createAccountButton = DirectButton(parent=self.frame, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0, linePos), scale=buttonScale, text=OTPLocalizer.LoginScreenCreateAccount, text_scale=0.06, text_pos=(0, -0.02), command=self.__handleCreateAccount)
        linePos -= buttonLineHeight
        self.quitButton = DirectButton(parent=self.frame, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0, linePos), scale=buttonScale, text=OTPLocalizer.LoginScreenQuit, text_scale=0.06, text_pos=(0, -0.02), command=self.__handleQuit)
        linePos -= buttonLineHeight
        self.dialogDoneEvent = 'loginDialogAck'
        dialogClass = OTPGlobals.getGlobalDialogClass()
        self.dialog = dialogClass(dialogName='loginDialog', doneEvent=self.dialogDoneEvent, message='', style=OTPDialog.Acknowledge, sortOrder=NO_FADE_SORT_INDEX + 100)
        self.dialog.hide()
        self.failDialog = DirectFrame(parent=aspect2dp, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0.1, 0), text='', text_scale=0.08, text_pos=(0.0, 0.3), text_wordwrap=15, sortOrder=NO_FADE_SORT_INDEX)
        linePos = -0.05
        self.failTryAgainButton = DirectButton(parent=self.failDialog, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0, linePos), scale=0.9, text=OTPLocalizer.LoginScreenTryAgain, text_scale=0.06, text_pos=(0, -0.02), command=self.__handleFailTryAgain)
        linePos -= buttonLineHeight
        self.failCreateAccountButton = DirectButton(parent=self.failDialog, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0, linePos), scale=0.9, text=OTPLocalizer.LoginScreenCreateAccount, text_scale=0.06, text_pos=(0, -0.02), command=self.__handleFailCreateAccount)
        linePos -= buttonLineHeight
        self.failDialog.hide()
        self.connectionProblemDialogDoneEvent = 'loginConnectionProblemDlgAck'
        dialogClass = OTPGlobals.getGlobalDialogClass()
        self.connectionProblemDialog = dialogClass(dialogName='connectionProblemDialog', doneEvent=self.connectionProblemDialogDoneEvent, message='', style=OTPDialog.Acknowledge, sortOrder=NO_FADE_SORT_INDEX + 100)
        self.connectionProblemDialog.hide()
        return

    def unload(self):
        self.notify.debug('unload')
        self.nameEntry.destroy()
        self.passwordEntry.destroy()
        self.failTryAgainButton.destroy()
        self.failCreateAccountButton.destroy()
        self.createAccountButton.destroy()
        self.loginButton.destroy()
        self.quitButton.destroy()
        self.dialog.cleanup()
        del self.dialog
        self.failDialog.destroy()
        del self.failDialog
        self.connectionProblemDialog.cleanup()
        del self.connectionProblemDialog
        self.frame.destroy()
        del self.fsm
        del self.loginInterface
        del self.cr

    def enter(self):
        if self.cr.blue:
            self.userName = 'blue'
            self.password = self.cr.blue
            self.fsm.request('waitForLoginResponse')
        elif self.cr.playToken:
            self.userName = '*'
            self.password = self.cr.playToken
            self.fsm.request('waitForLoginResponse')
        elif hasattr(self.cr, 'DISLToken') and self.cr.DISLToken:
            self.userName = '*'
            self.password = self.cr.DISLToken
            self.fsm.request('waitForLoginResponse')
        elif self.AutoLoginName:
            self.userName = self.AutoLoginName
            self.password = self.AutoLoginPassword
            self.fsm.request('waitForLoginResponse')
        else:
            self.fsm.request('login')

    def exit(self):
        self.frame.hide()
        self.ignore(self.dialogDoneEvent)
        self.fsm.requestFinalState()

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterLogin(self):
        self.cr.resetPeriodTimer(None)
        self.userName = ''
        self.password = ''
        self.userName = launcher.getLastLogin()
        if self.userName and self.nameEntry.get():
            if self.userName != self.nameEntry.get():
                self.userName = ''
        self.frame.show()
        self.nameEntry.enterText(self.userName)
        self.passwordEntry.enterText(self.password)
        self.focusList = [self.nameEntry, self.passwordEntry]
        focusIndex = 0
        if self.userName:
            focusIndex = 1
        self.startFocusMgmt(startFocus=focusIndex)
        return

    def exitLogin(self):
        self.stopFocusMgmt()

    def enterShowLoginFailDialog(self, msg):
        base.transitions.fadeScreen(0.5)
        self.failDialog['text'] = msg
        self.failDialog.show()

    def __handleFailTryAgain(self):
        self.fsm.request('login')

    def __handleFailCreateAccount(self):
        messenger.send(self.doneEvent, [{'mode': 'createAccount'}])

    def __handleFailNoNewAccountsAck(self):
        self.dialog.hide()
        self.fsm.request('showLoginFailDialog', [self.failDialog['text']])

    def exitShowLoginFailDialog(self):
        base.transitions.noTransitions()
        self.failDialog.hide()

    def __handleLoginPassword(self, password):
        if password != '':
            if self.nameEntry.get() != '':
                self.__handleLoginButton()

    def __handleLoginButton(self):
        self.removeFocus()
        self.userName = self.nameEntry.get()
        self.password = self.passwordEntry.get()
        if self.userName == '':
            self.dialog.setMessage(OTPLocalizer.LoginScreenLoginPrompt)
            self.dialog.show()
            self.acceptOnce(self.dialogDoneEvent, self.__handleEnterLoginAck)
        else:
            self.fsm.request('waitForLoginResponse')

    def __handleQuit(self):
        self.removeFocus()
        messenger.send(self.doneEvent, [{'mode': 'quit'}])

    def __handleCreateAccount(self):
        self.removeFocus()
        messenger.send(self.doneEvent, [{'mode': 'createAccount'}])

    def enterWaitForLoginResponse(self):
        self.cr.handler = self.handleWaitForLoginResponse
        self.cr.userName = self.userName
        self.cr.password = self.password
        try:
            error = self.loginInterface.authorize(self.userName, self.password)
        except TTAccount.TTAccountException as e:
            self.fsm.request('showConnectionProblemDialog', [str(e)])
            return

        if error:
            self.notify.info(error)
            freeTimeExpired = self.loginInterface.getErrorCode() == 10
            if freeTimeExpired:
                self.cr.logAccountInfo()
                messenger.send(self.doneEvent, [{'mode': 'freeTimeExpired'}])
            else:
                self.fsm.request('showLoginFailDialog', [error])
        else:
            self.loginInterface.sendLoginMsg()
            self.waitForDatabaseTimeout(requestName='WaitForLoginResponse')

    def exitWaitForLoginResponse(self):
        self.cleanupWaitingForDatabase()
        self.cr.handler = None
        return

    def enterShowConnectionProblemDialog(self, msg):
        self.connectionProblemDialog.setMessage(msg)
        self.connectionProblemDialog.show()
        self.acceptOnce(self.connectionProblemDialogDoneEvent, self.__handleConnectionProblemAck)

    def __handleConnectionProblemAck(self):
        self.connectionProblemDialog.hide()
        self.fsm.request('login')

    def exitShowConnectionProblemDialog(self):
        pass

    def handleWaitForLoginResponse(self, msgType, di):
        if msgType == CLIENT_LOGIN_2_RESP:
            self.handleLoginResponseMsg2(di)
        elif msgType == CLIENT_LOGIN_RESP:
            self.handleLoginResponseMsg(di)
        elif msgType == CLIENT_LOGIN_3_RESP:
            self.handleLoginResponseMsg3(di)
        elif msgType == CLIENT_LOGIN_TOONTOWN_RESP:
            self.handleLoginToontownResponse(di)
        else:
            self.cr.handleMessageType(msgType, di)

    def getExtendedErrorMsg(self, errorString):
        prefix = 'Bad DC Version Compare'
        if len(errorString) < len(prefix):
            return errorString
        if errorString[:len(prefix)] == prefix:
            return '%s%s' % (errorString, ', address=%s' % base.cr.getServerAddress())
        return errorString

    def handleLoginResponseMsg3(self, di):
        now = time.time()
        returnCode = di.getInt8()
        errorString = self.getExtendedErrorMsg(di.getString())
        self.notify.info('Login response return code %s' % returnCode)
        if returnCode != 0:
            self.notify.info('Login failed: %s' % errorString)
            messenger.send(self.doneEvent, [{'mode': 'reject'}])
            return
        accountDetailRecord = AccountDetailRecord()
        accountDetailRecord.openChatEnabled = di.getString() == 'YES'
        accountDetailRecord.createFriendsWithChat = di.getString() == 'YES'
        chatCodeCreation = di.getString()
        accountDetailRecord.chatCodeCreation = chatCodeCreation == 'YES'
        parentControlledChat = chatCodeCreation == 'PARENT'
        access = di.getString()
        if access == 'VELVET':
            access = OTPGlobals.AccessVelvetRope
        elif access == 'FULL':
            access = OTPGlobals.AccessFull
        else:
            self.notify.warning('Unknown access: %s' % access)
            access = OTPGlobals.AccessUnknown
        accountDetailRecord.piratesAccess = access
        accountDetailRecord.familyAccountId = di.getInt32()
        accountDetailRecord.playerAccountId = di.getInt32()
        accountDetailRecord.playerName = di.getString()
        accountDetailRecord.playerNameApproved = di.getInt8()
        accountDetailRecord.maxAvatars = di.getInt32()
        self.cr.openChatAllowed = accountDetailRecord.openChatEnabled
        if not accountDetailRecord.chatCodeCreation:
            self.cr.secretChatAllowed = parentControlledChat
            self.cr.setIsPaid(accountDetailRecord.piratesAccess)
            self.userName = accountDetailRecord.playerName
            self.cr.userName = accountDetailRecord.playerName
            accountDetailRecord.numSubs = di.getUint16()
            for i in range(accountDetailRecord.numSubs):
                subDetailRecord = SubDetailRecord()
                subDetailRecord.subId = di.getUint32()
                subDetailRecord.subOwnerId = di.getUint32()
                subDetailRecord.subName = di.getString()
                subDetailRecord.subActive = di.getString()
                access = di.getString()
                if access == 'VELVET':
                    access = OTPGlobals.AccessVelvetRope
                elif access == 'FULL':
                    access = OTPGlobals.AccessFull
                else:
                    access = OTPGlobals.AccessUnknown
                subDetailRecord.subAccess = access
                subDetailRecord.subLevel = di.getUint8()
                subDetailRecord.subNumAvatars = di.getUint8()
                subDetailRecord.subNumConcur = di.getUint8()
                subDetailRecord.subFounder = di.getString() == 'YES'
                accountDetailRecord.subDetails[subDetailRecord.subId] = subDetailRecord

            accountDetailRecord.WLChatEnabled = di.getString() == 'YES'
            if accountDetailRecord.WLChatEnabled:
                self.cr.whiteListChatEnabled = 1
            else:
                self.cr.whiteListChatEnabled = 0
            self.notify.info('End of DISL token parse')
            base.logPrivateInfo and self.notify.info('accountDetailRecord: %s' % accountDetailRecord)
        self.cr.accountDetailRecord = accountDetailRecord
        self.__handleLoginSuccess()

    def handleLoginResponseMsg2(self, di):
        self.notify.debug('handleLoginResponseMsg2')
        if base.logPrivateInfo:
            if self.notify.getDebug():
                dgram = di.getDatagram()
                dgram.dumpHex(ostream)
        now = time.time()
        returnCode = di.getUint8()
        errorString = self.getExtendedErrorMsg(di.getString())
        self.userName = di.getString()
        self.cr.userName = self.userName
        accountDetailRecord = AccountDetailRecord()
        self.cr.accountDetailRecord = accountDetailRecord
        canChat = di.getUint8()
        self.cr.secretChatAllowed = canChat
        if base.logPrivateInfo:
            self.notify.info('Chat from game server login: %s' % canChat)
        sec = di.getUint32()
        usec = di.getUint32()
        serverTime = sec + usec / 1000000.0
        self.cr.serverTimeUponLogin = serverTime
        self.cr.clientTimeUponLogin = now
        self.cr.globalClockRealTimeUponLogin = globalClock.getRealTime()
        if hasattr(self.cr, 'toontownTimeManager'):
            self.cr.toontownTimeManager.updateLoginTimes(serverTime, now, self.cr.globalClockRealTimeUponLogin)
        serverDelta = serverTime - now
        self.cr.setServerDelta(serverDelta)
        self.notify.setServerDelta(serverDelta, 28800)
        self.isPaid = di.getUint8()
        self.cr.setIsPaid(self.isPaid)
        if self.isPaid:
            launcher.setPaidUserLoggedIn()
        if base.logPrivateInfo:
            self.notify.info('Paid from game server login: %s' % self.isPaid)
        self.cr.resetPeriodTimer(None)
        if di.getRemainingSize() >= 4:
            minutesRemaining = di.getInt32()
            if base.logPrivateInfo:
                self.notify.info('Minutes remaining from server %s' % minutesRemaining)
            if base.logPrivateInfo:
                if minutesRemaining >= 0:
                    self.notify.info('Spawning period timer')
                    self.cr.resetPeriodTimer(minutesRemaining * 60)
                elif self.isPaid:
                    self.notify.warning('Negative minutes remaining for paid user (?)')
                else:
                    self.notify.warning('Not paid, but also negative minutes remaining (?)')
        elif base.logPrivateInfo:
            self.notify.info('Minutes remaining not returned from server; not spawning period timer')
        familyStr = di.getString()
        WhiteListResponse = di.getString()
        if WhiteListResponse == 'YES':
            self.cr.whiteListChatEnabled = 1
        else:
            self.cr.whiteListChatEnabled = 0
        if di.getRemainingSize() > 0:
            self.cr.accountDays = self.parseAccountDays(di.getInt32())
        else:
            self.cr.accountDays = 100000
        if di.getRemainingSize() > 0:
            self.lastLoggedInStr = di.getString()
            self.notify.info('last logged in = %s' % self.lastLoggedInStr)
        else:
            self.lastLoggedInStr = ''
        self.cr.lastLoggedIn = datetime.now()
        if hasattr(self.cr, 'toontownTimeManager'):
            self.cr.lastLoggedIn = self.cr.toontownTimeManager.convertStrToToontownTime(self.lastLoggedInStr)
        self.cr.withParentAccount = False
        self.notify.info('Login response return code %s' % returnCode)
        if returnCode == 0:
            self.__handleLoginSuccess()
        elif returnCode == -13:
            self.notify.info('Period Time Expired')
            self.fsm.request('showLoginFailDialog', [OTPLocalizer.LoginScreenPeriodTimeExpired])
        else:
            self.notify.info('Login failed: %s' % errorString)
            messenger.send(self.doneEvent, [{'mode': 'reject'}])
        return

    def handleLoginResponseMsg(self, di):
        self.notify.debug('handleLoginResponseMsg1')
        if base.logPrivateInfo:
            if self.notify.getDebug():
                dgram = di.getDatagram()
                dgram.dumpHex(ostream)
        now = time.time()
        accountDetailRecord = AccountDetailRecord()
        self.cr.accountDetailRecord = accountDetailRecord
        returnCode = di.getUint8()
        accountCode = di.getUint32()
        errorString = self.getExtendedErrorMsg(di.getString())
        sec = di.getUint32()
        usec = di.getUint32()
        serverTime = sec + usec / 1000000.0
        serverDelta = serverTime - now
        self.cr.serverTimeUponLogin = serverTime
        self.cr.clientTimeUponLogin = now
        self.cr.globalClockRealTimeUponLogin = globalClock.getRealTime()
        if hasattr(self.cr, 'toontownTimeManager'):
            self.cr.toontownTimeManager.updateLoginTimes(serverTime, now, self.cr.globalClockRealTimeUponLogin)
        self.cr.setServerDelta(serverDelta)
        self.notify.setServerDelta(serverDelta, 28800)
        if di.getRemainingSize() > 0:
            self.cr.accountDays = self.parseAccountDays(di.getInt32())
        else:
            self.cr.accountDays = 100000
        if di.getRemainingSize() > 0:
            WhiteListResponse = di.getString()
        else:
            WhiteListResponse = 'NO'
        if WhiteListResponse == 'YES':
            self.cr.whiteListChatEnabled = 1
        else:
            self.cr.whiteListChatEnabled = 0
        self.lastLoggedInStr = base.config.GetString('last-logged-in', '')
        self.cr.lastLoggedIn = datetime.now()
        if hasattr(self.cr, 'toontownTimeManager'):
            self.cr.lastLoggedIn = self.cr.toontownTimeManager.convertStrToToontownTime(self.lastLoggedInStr)
        self.cr.withParentAccount = base.config.GetBool('dev-with-parent-account', 0)
        self.notify.info('Login response return code %s' % returnCode)
        if returnCode == 0:
            self.__handleLoginSuccess()
        elif returnCode == 12:
            self.notify.info('Bad password')
            self.fsm.request('showLoginFailDialog', [OTPLocalizer.LoginScreenBadPassword])
        elif returnCode == 14:
            self.notify.info('Bad word in user name')
            self.fsm.request('showLoginFailDialog', [OTPLocalizer.LoginScreenInvalidUserName])
        elif returnCode == 129:
            self.notify.info('Username not found')
            self.fsm.request('showLoginFailDialog', [OTPLocalizer.LoginScreenUserNameNotFound])
        else:
            self.notify.info('Login failed: %s' % errorString)
            messenger.send(self.doneEvent, [{'mode': 'reject'}])

    def __handleLoginSuccess(self):
        self.cr.logAccountInfo()
        launcher.setGoUserName(self.userName)
        launcher.setLastLogin(self.userName)
        launcher.setUserLoggedIn()
        if self.loginInterface.freeTimeExpires == -1:
            launcher.setPaidUserLoggedIn()
        if self.loginInterface.needToSetParentPassword():
            messenger.send(self.doneEvent, [{'mode': 'getChatPassword'}])
        else:
            messenger.send(self.doneEvent, [{'mode': 'success'}])

    def __handleEnterLoginAck(self):
        self.dialog.hide()
        self.fsm.request('login')

    def __handleNoNewAccountsAck(self):
        self.dialog.hide()
        self.fsm.request('login')

    def parseAccountDays(self, accountDays):
        result = 100000
        if accountDays >= 0:
            result = accountDays
        else:
            self.notify.warning('account days is negative %s' % accountDays)
        self.notify.debug('result=%s' % result)
        return result

    def handleLoginToontownResponse--- This code section failed: ---

0	LOAD_FAST         'self'
3	LOAD_ATTR         'notify'
6	LOAD_ATTR         'debug'
9	LOAD_CONST        'handleLoginToontownResponse'
12	CALL_FUNCTION_1   None
15	POP_TOP           None

16	LOAD_GLOBAL       'base'
19	LOAD_ATTR         'logPrivateInfo'
22	JUMP_IF_FALSE     '53'

25	LOAD_FAST         'di'
28	LOAD_ATTR         'getDatagram'
31	CALL_FUNCTION_0   None
34	STORE_FAST        'dgram'

37	LOAD_FAST         'dgram'
40	LOAD_ATTR         'dumpHex'
43	LOAD_GLOBAL       'ostream'
46	CALL_FUNCTION_1   None
49	POP_TOP           None
50	JUMP_ABSOLUTE     '56'
53	JUMP_FORWARD      '56'
56_0	COME_FROM         '53'

56	LOAD_GLOBAL       'time'
59	LOAD_ATTR         'time'
62	CALL_FUNCTION_0   None
65	STORE_FAST        'now'

68	LOAD_FAST         'di'
71	LOAD_ATTR         'getUint8'
74	CALL_FUNCTION_0   None
77	STORE_FAST        'returnCode'

80	LOAD_FAST         'di'
83	LOAD_ATTR         'getString'
86	CALL_FUNCTION_0   None
89	STORE_FAST        'respString'

92	LOAD_FAST         'self'
95	LOAD_ATTR         'getExtendedErrorMsg'
98	LOAD_FAST         'respString'
101	CALL_FUNCTION_1   None
104	STORE_FAST        'errorString'

107	LOAD_FAST         'di'
110	LOAD_ATTR         'getUint32'
113	CALL_FUNCTION_0   None
116	LOAD_FAST         'self'
119	STORE_ATTR        'accountNumber'

122	LOAD_FAST         'self'
125	LOAD_ATTR         'accountNumber'
128	LOAD_FAST         'self'
131	LOAD_ATTR         'cr'
134	STORE_ATTR        'DISLIdFromLogin'

137	LOAD_FAST         'di'
140	LOAD_ATTR         'getString'
143	CALL_FUNCTION_0   None
146	LOAD_FAST         'self'
149	STORE_ATTR        'accountName'

152	LOAD_FAST         'di'
155	LOAD_ATTR         'getUint8'
158	CALL_FUNCTION_0   None
161	LOAD_FAST         'self'
164	STORE_ATTR        'accountNameApproved'

167	LOAD_GLOBAL       'AccountDetailRecord'
170	CALL_FUNCTION_0   None
173	STORE_FAST        'accountDetailRecord'

176	LOAD_FAST         'accountDetailRecord'
179	LOAD_FAST         'self'
182	LOAD_ATTR         'cr'
185	STORE_ATTR        'accountDetailRecord'

188	LOAD_FAST         'di'
191	LOAD_ATTR         'getString'
194	CALL_FUNCTION_0   None
197	LOAD_CONST        'YES'
200	COMPARE_OP        '=='
203	LOAD_FAST         'self'
206	STORE_ATTR        'openChatEnabled'

209	LOAD_FAST         'di'
212	LOAD_ATTR         'getString'
215	CALL_FUNCTION_0   None
218	STORE_FAST        'createFriendsWithChat'

221	LOAD_FAST         'createFriendsWithChat'
224	LOAD_CONST        'YES'
227	COMPARE_OP        '=='
230	JUMP_IF_TRUE      '242'
233	LOAD_FAST         'createFriendsWithChat'
236	LOAD_CONST        'CODE'
239	COMPARE_OP        '=='
242	STORE_FAST        'canChat'

245	LOAD_FAST         'canChat'
248	LOAD_FAST         'self'
251	LOAD_ATTR         'cr'
254	STORE_ATTR        'secretChatAllowed'

257	LOAD_GLOBAL       'base'
260	LOAD_ATTR         'logPrivateInfo'
263	JUMP_IF_FALSE     '295'

266	LOAD_FAST         'self'
269	LOAD_ATTR         'notify'
272	LOAD_ATTR         'info'
275	LOAD_CONST        'CREATE_FRIENDS_WITH_CHAT from game server login: %s %s'
278	LOAD_FAST         'createFriendsWithChat'
281	LOAD_FAST         'canChat'
284	BUILD_TUPLE_2     None
287	BINARY_MODULO     None
288	CALL_FUNCTION_1   None
291	POP_TOP           None
292	JUMP_FORWARD      '295'
295_0	COME_FROM         '292'

295	LOAD_FAST         'di'
298	LOAD_ATTR         'getString'
301	CALL_FUNCTION_0   None
304	LOAD_FAST         'self'
307	STORE_ATTR        'chatCodeCreationRule'

310	LOAD_FAST         'self'
313	LOAD_ATTR         'chatCodeCreationRule'
316	LOAD_FAST         'self'
319	LOAD_ATTR         'cr'
322	STORE_ATTR        'chatChatCodeCreationRule'

325	LOAD_GLOBAL       'base'
328	LOAD_ATTR         'logPrivateInfo'
331	JUMP_IF_FALSE     '360'

334	LOAD_FAST         'self'
337	LOAD_ATTR         'notify'
340	LOAD_ATTR         'info'
343	LOAD_CONST        'Chat code creation rule = %s'
346	LOAD_FAST         'self'
349	LOAD_ATTR         'chatCodeCreationRule'
352	BINARY_MODULO     None
353	CALL_FUNCTION_1   None
356	POP_TOP           None
357	JUMP_FORWARD      '360'
360_0	COME_FROM         '357'

360	LOAD_FAST         'self'
363	LOAD_ATTR         'chatCodeCreationRule'
366	LOAD_CONST        'PARENT'
369	COMPARE_OP        '=='
372	LOAD_FAST         'self'
375	LOAD_ATTR         'cr'
378	STORE_ATTR        'secretChatNeedsParentPassword'

381	LOAD_FAST         'di'
384	LOAD_ATTR         'getUint32'
387	CALL_FUNCTION_0   None
390	STORE_FAST        'sec'

393	LOAD_FAST         'di'
396	LOAD_ATTR         'getUint32'
399	CALL_FUNCTION_0   None
402	STORE_FAST        'usec'

405	LOAD_FAST         'sec'
408	LOAD_FAST         'usec'
411	LOAD_CONST        1000000.0
414	BINARY_DIVIDE     None
415	BINARY_ADD        None
416	STORE_FAST        'serverTime'

419	LOAD_FAST         'serverTime'
422	LOAD_FAST         'self'
425	LOAD_ATTR         'cr'
428	STORE_ATTR        'serverTimeUponLogin'

431	LOAD_FAST         'now'
434	LOAD_FAST         'self'
437	LOAD_ATTR         'cr'
440	STORE_ATTR        'clientTimeUponLogin'

443	LOAD_GLOBAL       'globalClock'
446	LOAD_ATTR         'getRealTime'
449	CALL_FUNCTION_0   None
452	LOAD_FAST         'self'
455	LOAD_ATTR         'cr'
458	STORE_ATTR        'globalClockRealTimeUponLogin'

461	LOAD_GLOBAL       'hasattr'
464	LOAD_FAST         'self'
467	LOAD_ATTR         'cr'
470	LOAD_CONST        'toontownTimeManager'
473	CALL_FUNCTION_2   None
476	JUMP_IF_FALSE     '513'

479	LOAD_FAST         'self'
482	LOAD_ATTR         'cr'
485	LOAD_ATTR         'toontownTimeManager'
488	LOAD_ATTR         'updateLoginTimes'
491	LOAD_FAST         'serverTime'
494	LOAD_FAST         'now'
497	LOAD_FAST         'self'
500	LOAD_ATTR         'cr'
503	LOAD_ATTR         'globalClockRealTimeUponLogin'
506	CALL_FUNCTION_3   None
509	POP_TOP           None
510	JUMP_FORWARD      '513'
513_0	COME_FROM         '510'

513	LOAD_FAST         'serverTime'
516	LOAD_FAST         'now'
519	BINARY_SUBTRACT   None
520	STORE_FAST        'serverDelta'

523	LOAD_FAST         'self'
526	LOAD_ATTR         'cr'
529	LOAD_ATTR         'setServerDelta'
532	LOAD_FAST         'serverDelta'
535	CALL_FUNCTION_1   None
538	POP_TOP           None

539	LOAD_FAST         'self'
542	LOAD_ATTR         'notify'
545	LOAD_ATTR         'setServerDelta'
548	LOAD_FAST         'serverDelta'
551	LOAD_CONST        28800
554	CALL_FUNCTION_2   None
557	POP_TOP           None

558	LOAD_FAST         'di'
561	LOAD_ATTR         'getString'
564	CALL_FUNCTION_0   None
567	STORE_FAST        'access'

570	LOAD_FAST         'access'
573	LOAD_CONST        'FULL'
576	COMPARE_OP        '=='
579	LOAD_FAST         'self'
582	STORE_ATTR        'isPaid'

585	LOAD_FAST         'self'
588	LOAD_ATTR         'isPaid'
591	LOAD_FAST         'self'
594	LOAD_ATTR         'cr'
597	STORE_ATTR        'parentPasswordSet'

600	LOAD_FAST         'self'
603	LOAD_ATTR         'cr'
606	LOAD_ATTR         'setIsPaid'
609	LOAD_FAST         'self'
612	LOAD_ATTR         'isPaid'
615	CALL_FUNCTION_1   None
618	POP_TOP           None

619	LOAD_FAST         'self'
622	LOAD_ATTR         'isPaid'
625	JUMP_IF_FALSE     '641'

628	LOAD_GLOBAL       'launcher'
631	LOAD_ATTR         'setPaidUserLoggedIn'
634	CALL_FUNCTION_0   None
637	POP_TOP           None
638	JUMP_FORWARD      '641'
641_0	COME_FROM         '638'

641	LOAD_GLOBAL       'base'
644	LOAD_ATTR         'logPrivateInfo'
647	JUMP_IF_FALSE     '676'

650	LOAD_FAST         'self'
653	LOAD_ATTR         'notify'
656	LOAD_ATTR         'info'
659	LOAD_CONST        'Paid from game server login: %s'
662	LOAD_FAST         'self'
665	LOAD_ATTR         'isPaid'
668	BINARY_MODULO     None
669	CALL_FUNCTION_1   None
672	POP_TOP           None
673	JUMP_FORWARD      '676'
676_0	COME_FROM         '673'

676	LOAD_FAST         'di'
679	LOAD_ATTR         'getString'
682	CALL_FUNCTION_0   None
685	STORE_FAST        'WhiteListResponse'

688	LOAD_FAST         'WhiteListResponse'
691	LOAD_CONST        'YES'
694	COMPARE_OP        '=='
697	JUMP_IF_FALSE     '715'

700	LOAD_CONST        1
703	LOAD_FAST         'self'
706	LOAD_ATTR         'cr'
709	STORE_ATTR        'whiteListChatEnabled'
712	JUMP_FORWARD      '727'

715	LOAD_CONST        0
718	LOAD_FAST         'self'
721	LOAD_ATTR         'cr'
724	STORE_ATTR        'whiteListChatEnabled'
727_0	COME_FROM         '712'

727	LOAD_FAST         'di'
730	LOAD_ATTR         'getString'
733	CALL_FUNCTION_0   None
736	LOAD_FAST         'self'
739	STORE_ATTR        'lastLoggedInStr'

742	LOAD_GLOBAL       'datetime'
745	LOAD_ATTR         'now'
748	CALL_FUNCTION_0   None
751	LOAD_FAST         'self'
754	LOAD_ATTR         'cr'
757	STORE_ATTR        'lastLoggedIn'

760	LOAD_GLOBAL       'hasattr'
763	LOAD_FAST         'self'
766	LOAD_ATTR         'cr'
769	LOAD_CONST        'toontownTimeManager'
772	CALL_FUNCTION_2   None
775	JUMP_IF_FALSE     '811'

778	LOAD_FAST         'self'
781	LOAD_ATTR         'cr'
784	LOAD_ATTR         'toontownTimeManager'
787	LOAD_ATTR         'convertStrToToontownTime'
790	LOAD_FAST         'self'
793	LOAD_ATTR         'lastLoggedInStr'
796	CALL_FUNCTION_1   None
799	LOAD_FAST         'self'
802	LOAD_ATTR         'cr'
805	STORE_ATTR        'lastLoggedIn'
808	JUMP_FORWARD      '811'
811_0	COME_FROM         '808'

811	LOAD_FAST         'di'
814	LOAD_ATTR         'getRemainingSize'
817	CALL_FUNCTION_0   None
820	LOAD_CONST        0
823	COMPARE_OP        '>'
826	JUMP_IF_FALSE     '859'

829	LOAD_FAST         'self'
832	LOAD_ATTR         'parseAccountDays'
835	LOAD_FAST         'di'
838	LOAD_ATTR         'getInt32'
841	CALL_FUNCTION_0   None
844	CALL_FUNCTION_1   None
847	LOAD_FAST         'self'
850	LOAD_ATTR         'cr'
853	STORE_ATTR        'accountDays'
856	JUMP_FORWARD      '871'

859	LOAD_CONST        100000
862	LOAD_FAST         'self'
865	LOAD_ATTR         'cr'
868	STORE_ATTR        'accountDays'
871_0	COME_FROM         '856'

871	LOAD_
# Can't uncompyle C:\Users\Maverick\Documents\Visual Studio 2010\Projects\Unfreezer\py2\otp\login\LoginScreen.pyc
Traceback (most recent call last):
  File "C:\python27\lib\uncompyle2\__init__.py", line 206, in main
    uncompyle_file(infile, outstream, showasm, showast)
  File "C:\python27\lib\uncompyle2\__init__.py", line 143, in uncompyle_file
    uncompyle(version, co, outstream, showasm, showast)
  File "C:\python27\lib\uncompyle2\__init__.py", line 132, in uncompyle
    raise walk.ERROR
ParserError: --- This code section failed: ---

0	LOAD_FAST         'self'
3	LOAD_ATTR         'notify'
6	LOAD_ATTR         'debug'
9	LOAD_CONST        'handleLoginToontownResponse'
12	CALL_FUNCTION_1   None
15	POP_TOP           None

16	LOAD_GLOBAL       'base'
19	LOAD_ATTR         'logPrivateInfo'
22	JUMP_IF_FALSE     '53'

25	LOAD_FAST         'di'
28	LOAD_ATTR         'getDatagram'
31	CALL_FUNCTION_0   None
34	STORE_FAST        'dgram'

37	LOAD_FAST         'dgram'
40	LOAD_ATTR         'dumpHex'
43	LOAD_GLOBAL       'ostream'
46	CALL_FUNCTION_1   None
49	POP_TOP           None
50	JUMP_ABSOLUTE     '56'
53	JUMP_FORWARD      '56'
56_0	COME_FROM         '53'

56	LOAD_GLOBAL       'time'
59	LOAD_ATTR         'time'
62	CALL_FUNCTION_0   None
65	STORE_FAST        'now'

68	LOAD_FAST         'di'
71	LOAD_ATTR         'getUint8'
74	CALL_FUNCTION_0   None
77	STORE_FAST        'returnCode'

80	LOAD_FAST         'di'
83	LOAD_ATTR         'getString'
86	CALL_FUNCTION_0   None
89	STORE_FAST        'respString'

92	LOAD_FAST         'self'
95	LOAD_ATTR         'getExtendedErrorMsg'
98	LOAD_FAST         'respString'
101	CALL_FUNCTION_1   None
104	STORE_FAST        'errorString'

107	LOAD_FAST         'di'
110	LOAD_ATTR         'getUint32'
113	CALL_FUNCTION_0   None
116	LOAD_FAST         'self'
119	STORE_ATTR        'accountNumber'

122	LOAD_FAST         'self'
125	LOAD_ATTR         'accountNumber'
128	LOAD_FAST         'self'
131	LOAD_ATTR         'cr'
134	STORE_ATTR        'DISLIdFromLogin'

137	LOAD_FAST         'di'
140	LOAD_ATTR         'getString'
143	CALL_FUNCTION_0   None
146	LOAD_FAST         'self'
149	STORE_ATTR        'accountName'

152	LOAD_FAST         'di'
155	LOAD_ATTR         'getUint8'
158	CALL_FUNCTION_0   None
161	LOAD_FAST         'self'
164	STORE_ATTR        'accountNameApproved'

167	LOAD_GLOBAL       'AccountDetailRecord'
170	CALL_FUNCTION_0   None
173	STORE_FAST        'accountDetailRecord'

176	LOAD_FAST         'accountDetailRecord'
179	LOAD_FAST         'self'
182	LOAD_ATTR         'cr'
185	STORE_ATTR        'accountDetailRecord'

188	LOAD_FAST         'di'
191	LOAD_ATTR         'getString'
194	CALL_FUNCTION_0   None
197	LOAD_CONST        'YES'
200	COMPARE_OP        '=='
203	LOAD_FAST         'self'
206	STORE_ATTR        'openChatEnabled'

209	LOAD_FAST         'di'
212	LOAD_ATTR         'getString'
215	CALL_FUNCTION_0   None
218	STORE_FAST        'createFriendsWithChat'

221	LOAD_FAST         'createFriendsWithChat'
224	LOAD_CONST        'YES'
227	COMPARE_OP        '=='
230	JUMP_IF_TRUE      '242'
233	LOAD_FAST         'createFriendsWithChat'
236	LOAD_CONST        'CODE'
239	COMPARE_OP        '=='
242	STORE_FAST        'canChat'

245	LOAD_FAST         'canChat'
248	LOAD_FAST         'self'
251	LOAD_ATTR         'cr'
254	STORE_ATTR        'secretChatAllowed'

257	LOAD_GLOBAL       'base'
260	LOAD_ATTR         'logPrivateInfo'
263	JUMP_IF_FALSE     '295'

266	LOAD_FAST         'self'
269	LOAD_ATTR         'notify'
272	LOAD_ATTR         'info'
275	LOAD_CONST        'CREATE_FRIENDS_WITH_CHAT from game server login: %s %s'
278	LOAD_FAST         'createFriendsWithChat'
281	LOAD_FAST         'canChat'
284	BUILD_TUPLE_2     None
287	BINARY_MODULO     None
288	CALL_FUNCTION_1   None
291	POP_TOP           None
292	JUMP_FORWARD      '295'
295_0	COME_FROM         '292'

295	LOAD_FAST         'di'
298	LOAD_ATTR         'getString'
301	CALL_FUNCTION_0   None
304	LOAD_FAST         'self'
307	STORE_ATTR        'chatCodeCreationRule'

310	LOAD_FAST         'self'
313	LOAD_ATTR         'chatCodeCreationRule'
316	LOAD_FAST         'self'
319	LOAD_ATTR         'cr'
322	STORE_ATTR        'chatChatCodeCreationRule'

325	LOAD_GLOBAL       'base'
328	LOAD_ATTR         'logPrivateInfo'
331	JUMP_IF_FALSE     '360'

334	LOAD_FAST         'self'
337	LOAD_ATTR         'notify'
340	LOAD_ATTR         'info'
343	LOAD_CONST        'Chat code creation rule = %s'
346	LOAD_FAST         'self'
349	LOAD_ATTR         'chatCodeCreationRule'
352	BINARY_MODULO     None
353	CALL_FUNCTION_1   None
356	POP_TOP           None
357	JUMP_FORWARD      '360'
360_0	COME_FROM         '357'

360	LOAD_FAST         'self'
363	LOAD_ATTR         'chatCodeCreationRule'
366	LOAD_CONST        'PARENT'
369	COMPARE_OP        '=='
372	LOAD_FAST         'self'
375	LOAD_ATTR         'cr'
378	STORE_ATTR        'secretChatNeedsParentPassword'

381	LOAD_FAST         'di'
384	LOAD_ATTR         'getUint32'
387	CALL_FUNCTION_0   None
390	STORE_FAST        'sec'

393	LOAD_FAST         'di'
396	LOAD_ATTR         'getUint32'
399	CALL_FUNCTION_0   None
402	STORE_FAST        'usec'

405	LOAD_FAST         'sec'
408	LOAD_FAST         'usec'
411	LOAD_CONST        1000000.0
414	BINARY_DIVIDE     None
415	BINARY_ADD        None
416	STORE_FAST        'serverTime'

419	LOAD_FAST         'serverTime'
422	LOAD_FAST         'self'
425	LOAD_ATTR         'cr'
428	STORE_ATTR        'serverTimeUponLogin'

431	LOAD_FAST         'now'
434	LOAD_FAST         'self'
437	LOAD_ATTR         'cr'
440	STORE_ATTR        'clientTimeUponLogin'

443	LOAD_GLOBAL       'globalClock'
446	LOAD_ATTR         'getRealTime'
449	CALL_FUNCTION_0   None
452	LOAD_FAST         'self'
455	LOAD_ATTR         'cr'
458	STORE_ATTR        'globalClockRealTimeUponLogin'

461	LOAD_GLOBAL       'hasattr'
464	LOAD_FAST         'self'
467	LOAD_ATTR         'cr'
470	LOAD_CONST        'toontownTimeManager'
473	CALL_FUNCTION_2   None
476	JUMP_IF_FALSE     '513'

479	LOAD_FAST         'self'
482	LOAD_ATTR         'cr'
485	LOAD_ATTR         'toontownTimeManager'
488	LOAD_ATTR         'updateLoginTimes'
491	LOAD_FAST         'serverTime'
494	LOAD_FAST         'now'
497	LOAD_FAST         'self'
500	LOAD_ATTR         'cr'
503	LOAD_ATTR         'globalClockRealTimeUponLogin'
506	CALL_FUNCTION_3   None
509	POP_TOP           None
510	JUMP_FORWARD      '513'
513_0	COME_FROM         '510'

513	LOAD_FAST         'serverTime'
516	LOAD_FAST         'now'
519	BINARY_SUBTRACT   None
520	STORE_FAST        'serverDelta'

523	LOAD_FAST         'self'
526	LOAD_ATTR         'cr'
529	LOAD_ATTR         'setServerDelta'
532	LOAD_FAST         'serverDelta'
535	CALL_FUNCTION_1   None
538	POP_TOP           None

539	LOAD_FAST         'self'
542	LOAD_ATTR         'notify'
545	LOAD_ATTR         'setServerDelta'
548	LOAD_FAST         'serverDelta'
551	LOAD_CONST        28800
554	CALL_FUNCTION_2   None
557	POP_TOP           None

558	LOAD_FAST         'di'
561	LOAD_ATTR         'getString'
564	CALL_FUNCTION_0   None
567	STORE_FAST        'access'

570	LOAD_FAST         'access'
573	LOAD_CONST        'FULL'
576	COMPARE_OP        '=='
579	LOAD_FAST         'self'
582	STORE_ATTR        'isPaid'

585	LOAD_FAST         'self'
588	LOAD_ATTR         'isPaid'
591	LOAD_FAST         'self'
594	LOAD_ATTR         'cr'
597	STORE_ATTR        'parentPasswordSet'

600	LOAD_FAST         'self'
603	LOAD_ATTR         'cr'
606	LOAD_ATTR         'setIsPaid'
609	LOAD_FAST         'self'
612	LOAD_ATTR         'isPaid'
615	CALL_FUNCTION_1   None
618	POP_TOP           None

619	LOAD_FAST         'self'
622	LOAD_ATTR         'isPaid'
625	JUMP_IF_FALSE     '641'

628	LOAD_GLOBAL       'launcher'
631	LOAD_ATTR         'setPaidUserLoggedIn'
634	CALL_FUNCTION_0   None
637	POP_TOP           None
638	JUMP_FORWARD      '641'
641_0	COME_FROM         '638'

641	LOAD_GLOBAL       'base'
644	LOAD_ATTR         'logPrivateInfo'
647	JUMP_IF_FALSE     '676'

650	LOAD_FAST         'self'
653	LOAD_ATTR         'notify'
656	LOAD_ATTR         'info'
659	LOAD_CONST        'Paid from game server login: %s'
662	LOAD_FAST         'self'
665	LOAD_ATTR         'isPaid'
668	BINARY_MODULO     None
669	CALL_FUNCTION_1   None
672	POP_TOP           None
673	JUMP_FORWARD      '676'
676_0	COME_FROM         '673'

676	LOAD_FAST         'di'
679	LOAD_ATTR         'getString'
682	CALL_FUNCTION_0   None
685	STORE_FAST        'WhiteListResponse'

688	LOAD_FAST         'WhiteListResponse'
691	LOAD_CONST        'YES'
694	COMPARE_OP        '=='
697	JUMP_IF_FALSE     '715'

700	LOAD_CONST        1
703	LOAD_FAST         'self'
706	LOAD_ATTR         'cr'
709	STORE_ATTR        'whiteListChatEnabled'
712	JUMP_FORWARD      '727'

715	LOAD_CONST        0
718	LOAD_FAST         'self'
721	LOAD_ATTR         'cr'
724	STORE_ATTR        'whiteListChatEnabled'
727_0	COME_FROM         '712'

727	LOAD_FAST         'di'
730	LOAD_ATTR         'getString'
733	CALL_FUNCTION_0   None
736	LOAD_FAST         'self'
739	STORE_ATTR        'lastLoggedInStr'

742	LOAD_GLOBAL       'datetime'
745	LOAD_ATTR         'now'
748	CALL_FUNCTION_0   None
751	LOAD_FAST         'self'
754	LOAD_ATTR         'cr'
757	STORE_ATTR        'lastLoggedIn'

760	LOAD_GLOBAL       'hasattr'
763	LOAD_FAST         'self'
766	LOAD_ATTR         'cr'
769	LOAD_CONST        'toontownTimeManager'
772	CALL_FUNCTION_2   None
775	JUMP_IF_FALSE     '811'

778	LOAD_FAST         'self'
781	LOAD_ATTR         'cr'
784	LOAD_ATTR         'toontownTimeManager'
787	LOAD_ATTR         'convertStrToToontownTime'
790	LOAD_FAST         'self'
793	LOAD_ATTR         'lastLoggedInStr'
796	CALL_FUNCTION_1   None
799	LOAD_FAST         'self'
802	LOAD_ATTR         'cr'
805	STORE_ATTR        'lastLoggedIn'
808	JUMP_FORWARD      '811'
811_0	COME_FROM         '808'

811	LOAD_FAST         'di'
814	LOAD_ATTR         'getRemainingSize'
817	CALL_FUNCTION_0   None
820	LOAD_CONST        0
823	COMPARE_OP        '>'
826	JUMP_IF_FALSE     '859'

829	LOAD_FAST         'self'
832	LOAD_ATTR         'parseAccountDays'
835	LOAD_FAST         'di'
838	LOAD_ATTR         'getInt32'
841	CALL_FUNCTION_0   None
844	CALL_FUNCTION_1   None
847	LOAD_FAST         'self'
850	LOAD_ATTR         'cr'
853	STORE_ATTR        'accountDays'
856	JUMP_FORWARD      '871'

859	LOAD_CONST        100000
862	LOAD_FAST         'self'
865	LOAD_ATTR         'cr'
868	STORE_ATTR        'accountDays'
871_0	COME_FROM         '856'

871	LOAD_FAST         'di'
874	LOAD_ATTR         'getString'
877	CALL_FUNCTION_0   None
880	LOAD_FAST         'self'
883	STORE_ATTR        'toonAccountType'

886	LOAD_FAST         'self'
889	LOAD_ATTR         'toonAccountType'
892	LOAD_CONST        'WITH_PARENT_ACCOUNT'
895	COMPARE_OP        '=='
898	JUMP_IF_FALSE     '916'

901	LOAD_GLOBAL       'True'
904	LOAD_FAST         'self'
907	LOAD_ATTR         'cr'
910	STORE_ATTR        'withParentAccount'
913	JUMP_FORWARD      '969'

916	LOAD_FAST         'self'
919	LOAD_ATTR         'toonAccountType'
922	LOAD_CONST        'NO_PARENT_ACCOUNT'
925	COMPARE_OP        '=='
928	JUMP_IF_FALSE     '946'

931	LOAD_GLOBAL       'False'
934	LOAD_FAST         'self'
937	LOAD_ATTR         'cr'
940	STORE_ATTR        'withParentAccount'
943	JUMP_FORWARD      '969'

946	LOAD_FAST         'self'
949	LOAD_ATTR         'notify'
952	LOAD_ATTR         'error'
955	LOAD_CONST        'unknown toon account type %s'
958	LOAD_FAST         'self'
961	LOAD_ATTR         'toonAccountType'
964	BINARY_MODULO     None
965	CALL_FUNCTION_1   None
968	POP_TOP           None
969_0	COME_FROM         '913'
969_1	COME_FROM         '943'

969	LOAD_GLOBAL       'base'
972	LOAD_ATTR         'logPrivateInfo'
975	JUMP_IF_FALSE     '1004'

978	LOAD_FAST         'self'
981	LOAD_ATTR         'notify'
984	LOAD_ATTR         'info'
987	LOAD_CONST        'toonAccountType=%s'
990	LOAD_FAST         'self'
993	LOAD_ATTR         'toonAccountType'
996	BINARY_MODULO     None
997	CALL_FUNCTION_1   None
1000	POP_TOP           None
1001	JUMP_FORWARD      '1004'
1004_0	COME_FROM         '1001'

1004	LOAD_FAST         'di'
1007	LOAD_ATTR         'getString'
1010	CALL_FUNCTION_0   None
1013	LOAD_FAST         'self'
1016	STORE_ATTR        'userName'

1019	LOAD_FAST         'self'
1022	LOAD_ATTR         'userName'
1025	LOAD_FAST         'self'
1028	LOAD_ATTR         'cr'
1031	STORE_ATTR       FAST         'di'
874	LOAD_ATTR         'getString'
877	CALL_FUNCTION_0   None
880	LOAD_FAST         'self'
883	STORE_ATTR        'toonAccountType'

886	LOAD_FAST         'self'
889	LOAD_ATTR         'toonAccountType'
892	LOAD_CONST        'WITH_PARENT_ACCOUNT'
895	COMPARE_OP        '=='
898	JUMP_IF_FALSE     '916'

901	LOAD_GLOBAL       'True'
904	LOAD_FAST         'self'
907	LOAD_ATTR         'cr'
910	STORE_ATTR        'withParentAccount'
913	JUMP_FORWARD      '969'

916	LOAD_FAST         'self'
919	LOAD_ATTR         'toonAccountType'
922	LOAD_CONST        'NO_PARENT_ACCOUNT'
925	COMPARE_OP        '=='
928	JUMP_IF_FALSE     '946'

931	LOAD_GLOBAL       'False'
934	LOAD_FAST         'self'
937	LOAD_ATTR         'cr'
940	STORE_ATTR        'withParentAccount'
943	JUMP_FORWARD      '969'

946	LOAD_FAST         'self'
949	LOAD_ATTR         'notify'
952	LOAD_ATTR         'error'
955	LOAD_CONST        'unknown toon account type %s'
958	LOAD_FAST         'self'
961	LOAD_ATTR         'toonAccountType'
964	BINARY_MODULO     None
965	CALL_FUNCTION_1   None
968	POP_TOP           None
969_0	COME_FROM         '913'
969_1	COME_FROM         '943'

969	LOAD_GLOBAL       'base'
972	LOAD_ATTR         'logPrivateInfo'
975	JUMP_IF_FALSE     '1004'

978	LOAD_FAST         'self'
981	LOAD_ATTR         'notify'
984	LOAD_ATTR         'info'
987	LOAD_CONST        'toonAccountType=%s'
990	LOAD_FAST         'self'
993	LOAD_ATTR         'toonAccountType'
996	BINARY_MODULO     None
997	CALL_FUNCTION_1   None
1000	POP_TOP           None
1001	JUMP_FORWARD      '1004'
1004_0	COME_FROM         '1001'

1004	LOAD_FAST         'di'
1007	LOAD_ATTR         'getString'
1010	CALL_FUNCTION_0   None
1013	LOAD_FAST         'self'
1016	STORE_ATTR        'userName'

1019	LOAD_FAST         'self'
1022	LOAD_ATTR         'userName'
1025	LOAD_FAST         'self'
1028	LOAD_ATTR         'cr'
1031	STORE_ATTR        'userName'

1034	LOAD_FAST         'self'
1037	LOAD_ATTR         'notify'
1040	LOAD_ATTR         'info'
1043	LOAD_CONST        'Login response return code %s'
1046	LOAD_FAST         'returnCode'
1049	BINARY_MODULO     None
1050	CALL_FUNCTION_1   None
1053	POP_TOP           None

1054	LOAD_FAST         'returnCode'
1057	LOAD_CONST        0
1060	COMPARE_OP        '=='
1063	JUMP_IF_FALSE     '1079'

1066	LOAD_FAST         'self'
1069	LOAD_ATTR         '__handleLoginSuccess'
1072	CALL_FUNCTION_0   None
1075	POP_TOP           None
1076	JUMP_FORWARD      '1186'

1079	LOAD_FAST         'returnCode'
1082	LOAD_CONST        -13
1085	COMPARE_OP        '=='
1088	JUMP_IF_FALSE     '1135'

1091	LOAD_FAST         'self'
1094	LOAD_ATTR         'notify'
1097	LOAD_ATTR         'info'
1100	LOAD_CONST        'Period Time Expired'
1103	CALL_FUNCTION_1   None
1106	POP_TOP           None

1107	LOAD_FAST         'self'
1110	LOAD_ATTR         'fsm'
1113	LOAD_ATTR         'request'
1116	LOAD_CONST        'showLoginFailDialog'

1119	LOAD_GLOBAL       'OTPLocalizer'
1122	LOAD_ATTR         'LoginScreenPeriodTimeExpired'
1125	BUILD_LIST_1      None
1128	CALL_FUNCTION_2   None
1131	POP_TOP           None
1132	JUMP_FORWARD      '1186'

1135	LOAD_FAST         'self'
1138	LOAD_ATTR         'notify'
1141	LOAD_ATTR         'info'
1144	LOAD_CONST        'Login failed: %s'
1147	LOAD_FAST         'errorString'
1150	BINARY_MODULO     None
1151	CALL_FUNCTION_1   None
1154	POP_TOP           None

1155	LOAD_GLOBAL       'messenger'
1158	LOAD_ATTR         'send'
1161	LOAD_FAST         'self'
1164	LOAD_ATTR         'doneEvent'
1167	BUILD_MAP         None
1170	DUP_TOP           None
1171	LOAD_CONST        'mode'
1174	LOAD_CONST        'reject'
1177	ROT_THREE         None
1178	STORE_SUBSCR      None
1179	BUILD_LIST_1      None
1182	CALL_FUNCTION_2   None
1185	POP_TOP           None
1186_0	COME_FROM         '1076'
1186_1	COME_FROM         '1132'

Syntax error at or near `JUMP_FORWARD' token at offset 53# decompiled 0 files: 0 okay, 1 failed, 0 verify failed
# 2013.08.22 22:15:38 Pacific Daylight Time
 'userName'

1034	LOAD_FAST         'self'
1037	LOAD_ATTR         'notify'
1040	LOAD_ATTR         'info'
1043	LOAD_CONST        'Login response return code %s'
1046	LOAD_FAST         'returnCode'
1049	BINARY_MODULO     None
1050	CALL_FUNCTION_1   None
1053	POP_TOP           None

1054	LOAD_FAST         'returnCode'
1057	LOAD_CONST        0
1060	COMPARE_OP        '=='
1063	JUMP_IF_FALSE     '1079'

1066	LOAD_FAST         'self'
1069	LOAD_ATTR         '__handleLoginSuccess'
1072	CALL_FUNCTION_0   None
1075	POP_TOP           None
1076	JUMP_FORWARD      '1186'

1079	LOAD_FAST         'returnCode'
1082	LOAD_CONST        -13
1085	COMPARE_OP        '=='
1088	JUMP_IF_FALSE     '1135'

1091	LOAD_FAST         'self'
1094	LOAD_ATTR         'notify'
1097	LOAD_ATTR         'info'
1100	LOAD_CONST        'Period Time Expired'
1103	CALL_FUNCTION_1   None
1106	POP_TOP           None

1107	LOAD_FAST         'self'
1110	LOAD_ATTR         'fsm'
1113	LOAD_ATTR         'request'
1116	LOAD_CONST        'showLoginFailDialog'

1119	LOAD_GLOBAL       'OTPLocalizer'
1122	LOAD_ATTR         'LoginScreenPeriodTimeExpired'
1125	BUILD_LIST_1      None
1128	CALL_FUNCTION_2   None
1131	POP_TOP           None
1132	JUMP_FORWARD      '1186'

1135	LOAD_FAST         'self'
1138	LOAD_ATTR         'notify'
1141	LOAD_ATTR         'info'
1144	LOAD_CONST        'Login failed: %s'
1147	LOAD_FAST         'errorString'
1150	BINARY_MODULO     None
1151	CALL_FUNCTION_1   None
1154	POP_TOP           None

1155	LOAD_GLOBAL       'messenger'
1158	LOAD_ATTR         'send'
1161	LOAD_FAST         'self'
1164	LOAD_ATTR         'doneEvent'
1167	BUILD_MAP         None
1170	DUP_TOP           None
1171	LOAD_CONST        'mode'
1174	LOAD_CONST        'reject'
1177	ROT_THREE         None
1178	STORE_SUBSCR      None
1179	BUILD_LIST_1      None
1182	CALL_FUNCTION_2   None
1185	POP_TOP           None
1186_0	COME_FROM         '1076'
1186_1	COME_FROM         '1132'

Syntax error at or near `JUMP_FORWARD' token at offset 53


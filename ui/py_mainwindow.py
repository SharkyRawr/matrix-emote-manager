import json
import typing
from typing import Dict, List, Optional, Union

from lib import MatrixAPI, MatrixRoom
from PyQt5.QtCore import (QAbstractListModel, QDir, QModelIndex, QObject,
                          QSortFilterProxyModel, Qt, QThread, QTimer, QVariant,
                          pyqtSlot, pyqtSignal)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QMessageBox
from PyQt5.QtSql import QSqlTableModel, QSqlDatabase
from requests.models import HTTPError

from .mainwindow import Ui_MainWindow
from .py_emojieditor import EmojiEditor
from .py_login_dialog import LoginForm

matrix = MatrixAPI()


        
class RoomTableModel(QSqlTableModel):
    
    def __init__(self, parent, db, rooms, *args, **kwargs) -> None:
        super().__init__(parent, db, *args, **kwargs)
        if not db.open() or db.isOpenError() or not db.isValid():
            raise Exception("Could not open database: " + db.lastError().text())
        self.setTable('rooms')
        if db.lastError().isValid():
            raise Exception(db.lastError().text())
        self.select()
        
        for room in rooms:
            try:
                r = self.record()
                r.setValue('room', room)
                r.setGenerated('room', True)
                self.insertRecord(-1, r)
            except Exception as ex:
                print(ex)
                
    
    def data(self, index: QModelIndex, role):
        if role == Qt.DisplayRole:
            roomid = super().data(self.index(index.row(), 0), role)
            name = super().data(self.index(index.row(), 1), role)    
            return name or roomid
        elif role == Qt.EditRole:
            return super().data(self.index(index.row(), 0), role)

class RoomListNameWorker(QThread):
    KeepWorking = True
    roomNameFetched = pyqtSignal(str, str, name="roomNameFetched")

    def __init__(self, parent: typing.Optional['QObject'], rooms: list) -> None:
        super().__init__(parent)
        self.KeepWorking = True
        self.rooms = rooms
        

    def abort_gracefully(self):
        self.KeepWorking = False

    def run(self):
        for r in self.rooms:
            if self.KeepWorking == False:
                break
            
            try:
                if (name := matrix.get_room_name(r)) is not None:
                    #print(roomid)
                    self.roomNameFetched.emit(r, name)
                    continue # wait for next cycle
            except HTTPError:
                # if the room doesn't have a name, try to fetch the members and give it their name
                try:
                    members = matrix.get_room_members(r, exclude_myself=True)
                    self.roomNameFetched.emit(r,
                        "{} with {}".format(r, ', '.join([str(m.name) for m in members]))
                    )
                except KeyError as kerr:
                    print(kerr)
                except HTTPError as herr:
                    print(herr)

            self.msleep(100)
        print("RoomListNameWorker is done!")


class MainWindow(Ui_MainWindow, QMainWindow):
    SETTING_DISPLAYNAME: str = r'display_name'
    SETTING_AVATARURL: str = r'avatar_url'
    SETTING_TAGS: str = r'tags'
    _t = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        from res import res
        self.setupUi(self)
        self.setWindowIcon(QIcon(":/icon.png"))
        
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('emojimanager.db')

        self.proxy = QSortFilterProxyModel(self)

        @pyqtSlot()
        def set_filter_text():
            self.proxy.setFilterRegExp(self.txtFilter.toPlainText())

        self.txtUserID.setText("<Please Login>")
        self.txtFilter.textChanged.connect(set_filter_text)
        self.cmdLogin.clicked.connect(self.show_login_window)
        self.cmdEmojis.clicked.connect(self.show_emoji_window)
        self.listRooms.doubleClicked.connect(self.open_roomedit)

        self.load_if_available()

    @pyqtSlot()
    def closeEvent(self, event):
        if self._t:
            self._t.abort_gracefully()
            self._t.wait(1000)
        event.accept()
        
    @pyqtSlot()
    def open_roomedit(self):
        # Get selected room ID
        items = self.listRooms.selectedIndexes()
        it = items[0]
        row = it.row()
        #a = self.model.index(it.row(), 2)
        room = self.proxy.data(it, Qt.EditRole)
        print('open emote editor for', room)
        editor = EmojiEditor(parent=self, matrixapi=matrix, db=QSqlDatabase.cloneDatabase(self.db, 'emojis'), room=room)
        editor.exec()
        

    def load_if_available(self) -> None:
        try:
            if matrix.load():
                if matrix.user_id and matrix.access_token:
                    self.txtUserID.setText(matrix.user_id)
                    self.matrix_test()

        except Exception as ex:
            QMessageBox.critical(
                self, "Error", "Could not restore settings from settings.json!\n" + str(type(ex)) + ": " + str(ex))

    def matrix_test(self) -> None:
        if (p := matrix.get_presence()) is not None:
            # WE ARE LOGGED IN
            self.statusbar.showMessage("Status: {}, last active: {} seconds ago".format(
                p['presence'], p['last_active_ago']
            ))

            m = matrix.get_user_profile(matrix.user_id)
            self.txtGlobalName.setText(m.name)

            # Populate room list
            if (rooms := matrix.get_rooms()) is not None:
                self.model = RoomTableModel(parent=self, db=QSqlDatabase.cloneDatabase(self.db, 'rooms'), rooms=rooms)

                self.proxy.setSourceModel(self.model)
                self.listRooms.setModel(self.proxy)

                # Start fetching room names
                self._t = RoomListNameWorker(self, rooms=rooms)
                self._t.roomNameFetched.connect(self.roomNameFetched)
                self._t.start()
                self.statusbar.showMessage("Fetching room/member names ...")

                def finished():
                    self.statusbar.showMessage("Status: {}, last active: {} seconds ago, {} rooms".format(
                        p['presence'], p['last_active_ago'], len(rooms)
                    ))

                self._t.finished.connect(finished)

        else:
            QMessageBox.critical(self, "Login failed",
                                 "Matrix login has failed, please login again...")

    @pyqtSlot(str, str)
    def roomNameFetched(self, roomid, name):
        print('roomNameFetched', roomid, name)
        self.updateRoomName(roomid, name)
        
    def updateRoomName(self, roomid, name):
        r = self.model.record()
        
        # get room
        roomrow = -1
        for i in range(0, self.model.rowCount()):
            r = self.model.record(i)
            if roomid == r.value('room'):
                roomrow = i
                #print('foundRowNumber', rownumber)
                break
        
        r.setValue('room', roomid)
        r.setGenerated('room', True)
        r.setValue('name', name)
        r.setGenerated('name', True)

        if roomrow < 0:
            result = self.model.insertRecord(-1, r)
            if result is False:
                print("insertRecord", self.model.lastError().text(), self.model.lastError().databaseText())
        else:
            result = self.model.setRecord(roomrow, r)
            if result is False:
                print("setRecord", self.model.lastError().text(), self.model.lastError().databaseText())
        
        self.model.submitAll()
        self.model.select()

    @pyqtSlot()
    def show_login_window(self) -> None:
        global matrix
        dlg = LoginForm(self)
        dlg.updateDefaultsFromMatrix(matrix)

        if dlg.exec_():
            matrix = MatrixAPI(dlg.access_token, dlg.homeserver, dlg.user_id)
            if dlg.chkSave.isChecked():
                matrix.save()
            self.txtUserID.setText(dlg.user_id)
            try:
                self.matrix_test()
            except Exception as ex:
                QMessageBox.critical(self, "Login failed",
                                     "Matrix login has failed:\n" + str(ex))


    @pyqtSlot()
    def show_emoji_window(self) -> None:
        dlg = EmojiEditor(parent=self, matrixapi=matrix, db=QSqlDatabase.cloneDatabase(self.db, 'emojis'))
        dlg.exec()

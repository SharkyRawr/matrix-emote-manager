import json
import typing
from typing import Dict, List, Optional, Union

from lib import MatrixAPI, MatrixRoom
from PyQt5.QtCore import (QAbstractListModel, QDir, QModelIndex, QObject,
                          QSortFilterProxyModel, Qt, QThread, QTimer, QVariant,
                          pyqtSlot)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QMessageBox
from requests.models import HTTPError

from .mainwindow import Ui_MainWindow
from .py_emojieditor import EmojiEditor
from .py_login_dialog import LoginForm

matrix = MatrixAPI()


class RoomListModel(QAbstractListModel):
    def __init__(self, parent: typing.Optional['QObject'], rooms: List[str]) -> None:
        super().__init__(parent)
        self.rooms: Dict[str, MatrixRoom] = {r: MatrixRoom(r) for r in rooms}

    def index_to_key(self, index: int) -> str:
        a = list(self.rooms)[index]
        return a

    def rowCount(self, parent: QModelIndex) -> int:
        return len(self.rooms)

    def data(self, index: QModelIndex, role: int) -> typing.Any:        
        if index.row() > len(self.rooms):
            return QVariant()

        item = self.rooms[self.index_to_key(index.row())]
        
        if role == Qt.DisplayRole:
            return item.name or item.room_id
        elif role == Qt.EditRole:
            return item
        
        return QVariant()

    def get_room_by_name(self, name: str) -> Optional[MatrixRoom]:
        for k, r in self.rooms.items():
            if r.name == name:
                return r

    def update_room_name(self, roomid: str) -> bool:
        room = self.rooms[roomid]
        try:
            if (name := matrix.get_room_name(roomid)) is not None:
                print(roomid)
                self.set_room_name(room, name)
                return True
        except HTTPError:
            pass

        return False

    def set_room_name(self, room: Union[MatrixRoom, str], name: str) -> None:
        roomid = room.room_id if type(room) is MatrixRoom else room
        room = self.rooms[roomid]
        room.set_name(name)
        self.rooms[roomid] = room

        row = list(self.rooms.keys()).index(roomid)

        self.dataChanged.emit(
            self.createIndex(row, 0),
            self.createIndex(row, 0)
        )


class RoomListNameWorker(QThread):
    KeepWorking = True

    def __init__(self, parent: typing.Optional['QObject'], roomlistmodel: RoomListModel) -> None:
        super().__init__(parent)
        self.model = roomlistmodel
        self.KeepWorking = True

    def abort_gracefully(self):
        self.KeepWorking = False

    def run(self):
        for r in self.model.rooms:
            if self.KeepWorking == False:
                break

            if not self.model.update_room_name(r):
                print(r)
                try:
                    members = matrix.get_room_members(r, exclude_myself=True)
                    self.model.set_room_name(
                        r, "{} with {}".format(r, ', '.join([str(m.name) for m in members])))
                except KeyError:
                    pass
                except HTTPError as herr:
                    print(herr)
                    pass

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

        self.proxy = QSortFilterProxyModel(self)

        @pyqtSlot()
        def set_filter_text():
            self.proxy.setFilterRegExp(self.txtFilter.toPlainText())

        self.txtFilter.textChanged.connect(set_filter_text)

        self.txtUserID.setText("<Please Login>")
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
        rooms = [self.proxy.data(it, Qt.EditRole) for it in items]
        room: MatrixRoom = rooms[0] # there should only be one
        print('open emote editor for', room)
        editor = EmojiEditor(parent=self, matrixapi=matrix, room=room.room_id)
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
            if (r := matrix.get_rooms()) is not None:
                self.model = RoomListModel(self, r)

                self.proxy.setSourceModel(self.model)
                self.listRooms.setModel(self.proxy)

                # Start fetching room names
                self._t = RoomListNameWorker(self, self.model)
                self._t.start()
                self.statusbar.showMessage("Fetching room/member names ...")

                def finished():
                    self.statusbar.showMessage("Status: {}, last active: {} seconds ago, {} rooms".format(
                        p['presence'], p['last_active_ago'], len(r)
                    ))

                self._t.finished.connect(finished)

        else:
            QMessageBox.critical(self, "Login failed",
                                 "Matrix login has failed, please login again...")

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
    def upload_avatar_dialog(self) -> None:
        dlg = QFileDialog(self, "Upload avatar")
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilter("Images (*.png *.jpg *.jpeg *.webp *.gif)")

        if dlg.exec_():
            filename = dlg.selectedFiles().pop()
            mxc = matrix.upload_media(filename)
            self.txtRoomAvatarMXC.setPlainText(mxc)

            pixmap = QPixmap(filename)
            self.picAvatar.setPixmap(pixmap)

    @pyqtSlot()
    def apply_room_stuff(self) -> None:
        items = self.listRooms.selectedIndexes()
        rooms = [self.proxy.data(it, Qt.DisplayRole) for it in items]

        roomnick = self.txtRoomNickname.toPlainText()
        roomavatar = self.txtRoomAvatarMXC.toPlainText()

        try:
            for room in rooms:
                if (room := self.model.get_room_by_name(room)) is not None:
                    self.statusbar.showMessage(
                        "Sending event to room {} ...".format(room))
                    if len(self.txtRoomNickname.toPlainText()) > 1 or len(self.txtRoomAvatarMXC .toPlainText()) > 1:
                        matrix.update_roomstate(
                            room=room, displayname=roomnick, avatarmxc=roomavatar)

                    tags = self.txtTags.toPlainText().split(',')
                    if len(tags) > 0:
                        for t in tags:
                            matrix.put_room_tag(
                                room=room, tag=t.strip()
                            )
                else:
                    print("Cannot send events to:", room)
        except Exception as ex:
            QMessageBox.critical(self, "Login failed", str(ex))

    @pyqtSlot()
    def show_emoji_window(self) -> None:
        dlg = EmojiEditor(parent=self, matrixapi=matrix)
        dlg.exec()

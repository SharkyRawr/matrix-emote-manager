import mimetypes
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from requests.exceptions import HTTPError

from lib.matrix import MXC_RE, MatrixAPI
from PyQt5 import QtCore
from PyQt5.QtCore import (QCoreApplication, QMutex, QObject, Qt,
                          QThread, QTimer, pyqtSignal, pyqtSlot, QModelIndex,
                          QVariant, QTimer, QByteArray, QSortFilterProxyModel,
                          QPoint)
from PyQt5.QtGui import QIcon, QMovie, QPixmap, QImage
from PyQt5.QtWidgets import (QDialog, QFileDialog, QLabel,
                             QMessageBox, QPlainTextEdit, QProgressBar,
                             QVBoxLayout, QTableView, QItemDelegate, QLabel,
                             QHeaderView, QMenu, QAction)
from PyQt5.QtSql import QSqlRelationalTableModel, QSqlDatabase, QSqlRelation, QSqlTableModel

from .emojieditor import Ui_EmojiEditor
from .ImportExportHandlerAndProgressDialog import \
    Ui_ImportExportHandlerAndProgressDialog


from .const import CACHE_DIR, EMOJI_DIR


class EmojiDownloadThread(QThread):
    emojiFinished = pyqtSignal(int, str, str, bytes, str, name="emojiFinished")
    emojiError = pyqtSignal(int, str, str, str, name='emojiError')
    keepRunning = True

    def __init__(self, parent: Optional[QObject], matrix: MatrixAPI, emojilist: Dict) -> None:
        super().__init__(parent)
        self.emojilist = emojilist
        self.matrix = matrix
        self.keepRunning = True

    def abort_gracefully(self):
        self.keepRunning = False

    def run(self):
        for shortcode, mxc in self.emojilist.items():
            if self.keepRunning == False:
                break
            
            rowindex = list(self.emojilist.keys()).index(shortcode)

            try:
                emojiBytes, mimetype, filepath = self.getCachedEmoji(mxc['url'], width=128, height=128)
                # i, shortcode, mxc, emojiBytes, mimetype
                self.emojiFinished.emit(rowindex, shortcode, mxc['url'], emojiBytes, mimetype)
            except HTTPError as herr:
                print(herr)
                self.emojiError.emit(rowindex, shortcode, mxc['url'], str(herr))


    def getCachedEmoji(self, mxcurl, width: int, height: int) -> Tuple[bytes, str, str]:
        m = MXC_RE.search(mxcurl)
        if m is None:
            raise Exception("MXC url could not be parsed")
        if len(m.groups()) == 2:
            _, mediaid = m.groups()
            mediapath = Path()
            mediapath = mediapath.joinpath(EMOJI_DIR, mediaid)

            # check if the file is already cached locally
            for p in os.listdir(EMOJI_DIR):
                pm = re.match(r'(.+)\.(.+)', p)
                if pm:
                    filename, ext = pm.groups()
                    if mediaid in filename:
                        #print("Cached emoji", mediaid)
                        mimetype, _ = mimetypes.guess_type(p)
                        mimetype = mimetype or 'application/octet-stream'
                        with open(os.path.join(EMOJI_DIR, p), 'rb') as f:
                            return f.read(), mimetype, os.path.join(EMOJI_DIR, p),

            print("Downloading emoji", mediaid)
            emojiBytes, content_type = self.matrix.media_get_thumbnail(mxcurl, width=width, height=height)
            ext = mimetypes.guess_extension(content_type) or '.bin'
            mediapath = mediapath.with_suffix(ext)

            with open(str(mediapath), 'wb') as f:
                f.write(emojiBytes)
            return emojiBytes, content_type, str(mediapath)
        raise Exception("we fell through, what are we doing here??")


class ImportExportAction(object):
    EXPORT = 0
    IMPORT = 1
    IMPORT_OVERWRITE = 2
    directory: Optional[str] = ""

    def __init__(self, action: int, directory: Optional[str]) -> None:
        self.action = action
        self.directory = directory

    def __str__(self) -> str:
        action = "unkn"
        if self.action == ImportExportAction.EXPORT:
            action = "Export"
        elif self.action == ImportExportAction.IMPORT:
            action = "Import"
        elif self.action == ImportExportAction.IMPORT_OVERWRITE:
            action = "Import (overwrite)"
        return f"{action} on {self.directory}"


class ImportExportHandlerAndProgressDialog(Ui_ImportExportHandlerAndProgressDialog, QDialog):
    def __init__(self, matrixapi: MatrixAPI, action: ImportExportAction, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowIcon(QIcon(":/icon.png"))

        self.myAction = action

        self.txtLog.append(str(self.myAction) + "\n")
        self.txtLog.append("We are working on it, please stand by!\n")

        #user_emotes = self.matrix.get_account_data(self.matrix.user_id or '', "im.ponies.user_emotes")
        #emoticons: Dict = user_emotes['emoticons']
        # todo: actually download


class EmojiUploaderTask(QDialog):
    shouldWork = True
    append = False
    matrix = None

    def __init__(self, filenames: List[str], append: bool, matrix: MatrixAPI, room: Optional[str] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.emoji_filenames_to_upload = filenames
        self.shouldWork = True
        self.append = append
        self.matrix = matrix
        self.room = room

        if self.room:
            try:
                self.emotes = self.matrix.get_room_state(self.room, 'im.ponies.room_emotes')
            except Exception as ex:
                print(ex)
                self.emotes = dict()
                
        else:
            self.emotes = self.matrix.get_account_data(
                self.matrix.user_id or '', "im.ponies.user_emotes"
            )
        
        if not 'images' in self.emotes:
            self.emotes['images'] = dict()

        self.setupUI()

    def setupUI(self):
        self.setFixedSize(320, 200)
        self.setWindowTitle("Uploading emojis ...")
        self.setModal(True)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.work)
        self.timer.start()

        self.pb = QProgressBar(self)
        self.pb.setMinimum(0)
        self.pb.setMaximum(len(self.emoji_filenames_to_upload))
        layout.addWidget(self.pb)

    @pyqtSlot()
    def work(self):
        if len(self.emoji_filenames_to_upload) <= 0:
            self.work_done()
            return

        file = self.emoji_filenames_to_upload.pop()

        # update progress
        self.pb.setValue(self.pb.maximum() -
                         len(self.emoji_filenames_to_upload))

        basename = os.path.basename(file)
        nakedfilename, _ = os.path.splitext(basename)
        
        # Apparently shortcodes should be without :: ?? or it breaks certain clients
        #emojiname = ':' + nakedfilename + ':'
        emojiname = nakedfilename

        if self.append and emojiname in self.emotes:
            return

        while True:
            try:
                mxc = self.matrix.upload_media(file)
                self.emotes['images'][emojiname] = {
                    'url': mxc
                }
                break
            except Exception as ex:
                r = QMessageBox.critical(self, "Error uploading emoji", str(ex), QMessageBox.Ignore | QMessageBox.Retry)
                if r == QMessageBox.Ignore:
                    break

    @pyqtSlot()
    def work_done(self):
        self.timer.stop()
        if self.room:
            self.matrix.put_room_state(
                self.room, 'im.ponies.room_emotes', self.emotes
            )
        else:
            self.matrix.put_account_data(
                self.matrix.user_id or '', 'im.ponies.user_emotes', self.emotes
            )
        self.accept()
        

class EmojiTableModel(QSqlRelationalTableModel):
    def __init__(self, parent, room: Optional[str], db, *args, **kwargs) -> None:
        super().__init__(parent, db, *args, **kwargs)
        if not db.open() or db.isOpenError() or not db.isValid():
            raise Exception("Could not open database: " + db.lastError().text())
        
        self.setEditStrategy(QSqlTableModel.OnRowChange)
        self.setTable('emojis')
        if db.lastError().isValid():
            raise Exception(db.lastError().text())
        
        if room:
            self.setJoinMode(QSqlRelationalTableModel.LeftJoin)
            self.setRelation(1, QSqlRelation("rooms", "room", "name"))
        self.select()
        


class EmojiTableDelegate(QItemDelegate):
    def __init__(self, parent = None, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        
    def paint(self, painter, option, index):
        if index.column() != 0: # todo: update after reorder?
            return super().paint(painter, option, index)
        
        blob = index.model().data(index, Qt.DisplayRole)
        pm = QPixmap()
        
        if type(blob) is not QByteArray or not pm.loadFromData(blob):
            print("Error loading emoji:", index.row())
            img = QImage(":/SadMac.png")
            pm = QPixmap.fromImage(img)
        
        drawable = pm.scaled(option.rect.width(), option.rect.height(), Qt.KeepAspectRatio)
        
        painter.save()
        painter.translate(option.rect.topLeft())
        painter.drawPixmap(int((option.rect.width() / 2) - (drawable.width() / 2)), 0, drawable)
        painter.restore()
        

class EmojiEditor(Ui_EmojiEditor, QDialog):
    updateRowMutex = QMutex()
    room: str = None

    def __init__(self, matrixapi: MatrixAPI, db, room: Optional[str] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowIcon(QIcon(":/icon.png"))
        self.updateRowMutex = QMutex()
        vheader = self.tableView.verticalHeader()
        vheader.setDefaultSectionSize(64)
        vheader.sectionResizeMode(QHeaderView.Fixed)
        
        if room:
            self.room = room

        def select_files() -> List[str]:
            fd = QFileDialog(self, "Choose emojis", QCoreApplication.applicationDirPath())
            fd.setNameFilter('*.png *.jpg *.gif')
            fd.setFileMode(QFileDialog.FileMode.ExistingFiles)
            if fd.exec_():
                return fd.selectedFiles()
            return []

        def importOverwrite():
            files = select_files()
            if len(files) <= 0: return
            dlg = EmojiUploaderTask(
                files, append=False, matrix=self.matrix, room=self.room, parent=self)
            if dlg.exec_():
                self.refreshEmojis()

        # @todo: simplify this and extract a method or something? i dunno im just a dumb fox 🦊
        def importAppend():
            files = select_files()
            if len(files) <= 0: return
            dlg = EmojiUploaderTask(
                files, append=True, matrix=self.matrix,  room=self.room, parent=self)
            if dlg.exec_():
                self.refreshEmojis()

        self.actionImport_overwrite.triggered.connect(importOverwrite)
        self.actionImport_append.triggered.connect(importAppend)
        self.actionExport.triggered.connect(self.exportEmojis)
        self.cmdPushEmojis.clicked.connect(self.pushEmojis)

        for p in (CACHE_DIR, EMOJI_DIR):
            if not os.path.lexists(p) and not os.path.isdir(p):
                os.mkdir(p)

        self.matrix = matrixapi
        
        t: QTableView = self.tableView
        self.tableView.customContextMenuRequested.connect(self.emojiContextMenuRequested)
        self.db = db
        self.m = EmojiTableModel(parent=self, db=self.db, room=room or None)
        if room:
            self.m.setFilter(f"emojis.room == '{room}'")
        else:
            self.m.setFilter("emojis.room is NULL")
        self.m.select()
        t.setModel(self.m)
        d = EmojiTableDelegate(self)
        t.setItemDelegate(d)
        
        self.emojiContextMenu = QMenu(self)
        delAction = QAction('Delete', self)
        delAction.triggered.connect(self.emojiDelete)
        self.emojiContextMenu.addAction(delAction)
        
        self.refreshEmojis()
        
    
    def refreshEmojis(self):
        if self.room:
            try:
                emotes = self.matrix.get_room_state(self.room, 'im.ponies.room_emotes')
            except Exception as ex:
                print(ex)
                emotes = dict()
                
        else:
            emotes = self.matrix.get_account_data(
                self.matrix.user_id or '', "im.ponies.user_emotes"
            )

        emoticons: Dict = dict()
        if 'images' in emotes:
            emoticons = emotes['images']
        
        
        self.downloadThread = EmojiDownloadThread(self, self.matrix, emoticons)
        self.downloadThread.start()
        self.downloadThread.emojiFinished.connect(self.emojiDownloadCompleted)
        self.downloadThread.emojiError.connect(self.emojiError)
        
        
        """This function saves the emojis to the Matrix homeserver
        """
    @pyqtSlot()
    def pushEmojis(self):
        emotes = dict()
        
        for i in range(0, self.m.rowCount()):
            r = self.m.record(i)
            shortcode = r.value(2)
            mxc = r.value(3)
            emotes[shortcode] = dict(url=mxc)
        
        try:
            if self.room:
                # Push im.ponies.room_emotes
                self.matrix.put_room_state(self.room, 'im.ponies.room_emotes', dict(images=emotes))
            else:
                self.matrix.put_account_data(self.matrix.user_id or '' , 'im.ponies.user_emotes', dict(images=emotes))
        except Exception as ex:
            print(ex)
            QMessageBox.critical(self, "Error", str(ex))
                
        self.refreshEmojis()
        QMessageBox.information(self, "Success", "Emojis succesfully saved to homeserver.")
        
    
    @pyqtSlot(QPoint)
    def emojiContextMenuRequested(self, point: QPoint):
        self.emojiContextMenu.popup(self.tableView.viewport().mapToGlobal(point))
        
    
    @pyqtSlot()
    def emojiDelete(self):
        selectedIndexes = self.tableView.selectedIndexes()
        rows = set(index.row() for index in selectedIndexes)
        for row in rows:
            if not self.m.removeRows(row, 1):
                err = self.m.lastError()
                print(f"Emoji Row {row} was NOT removed!", err.text(), err.driverText(), err.databaseText())
        
        self.m.submitAll()
        self.m.select()


    @pyqtSlot()
    def closeEvent(self, event):
        self.downloadThread.abort_gracefully()
        self.downloadThread.wait(1000)
        event.accept()
        
    
    @pyqtSlot(int, str, str, str)
    def emojiError(self, i, shortcode, mxc, errmsg):
        self.insertOrUpdateEmoji(i, shortcode, mxc, None, errmsg)
        
    
    @pyqtSlot(int, str, str, bytes, str)
    def emojiDownloadCompleted(self, i, shortcode, mxc, emojiBytes, mimetype):
        self.insertOrUpdateEmoji(i, shortcode, mxc, emojiBytes, mimetype)
        
        
    def insertOrUpdateEmoji(self, i, shortcode, mxc, emojiBytes, mimetype):
        r = self.m.record()
        rownumber = -1
        result = None
        # find emoji if it exists
        rowcount = self.m.rowCount()
        if rowcount < 0:
            raise Exception('Rowcount error ' + rowcount)
        for i in range(0, self.m.rowCount()):
            r = self.m.record(i)
            if shortcode in r.value(2):
                rownumber = i
                #print('foundRowNumber', rownumber)
                break
        
        r.setValue(2, shortcode)
        r.setGenerated(2, True)
        r.setValue(1, self.room)
        r.setGenerated(1, True)
        r.setValue(3, mxc)
        r.setGenerated(3, True)
        if emojiBytes:
            r.setValue(0, QByteArray(emojiBytes))
            r.setGenerated(0, True)
        else:
            r.setNull(0)
            r.setGenerated(0, True)
        
        if rownumber < 0:
            result = self.m.insertRecord(-1, r)
            if result is False:
                print("insertRecord", self.m.lastError().text(), self.m.lastError().databaseText())
        else:
            result = self.m.setRecord(rownumber, r)
            if result is False:
                print("setRecord", self.m.lastError().text(), self.m.lastError().databaseText())
        
        self.m.submitAll()
        self.m.select()
        

    @pyqtSlot()
    def exportEmojis(self):
        export_dir = QFileDialog.getExistingDirectory(
            self, "Choose export destination directory", "", QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly)
        if export_dir == "":
            return
        print("Export dir:", export_dir)

        # check for existing files in directory
        # todo: check if listdir also contains "." and ".." which may throw off the len()
        if len(os.listdir(export_dir)) > 0:
            result = QMessageBox.warning(self, "Directory contains existing files",
                                         "Warning! The directory you picked already contains files. If you continue some of your files may get overwritten by emojis of the same name.\nDo you wish to continue?", QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.No:
                # No, don't continue
                return

        d = ImportExportHandlerAndProgressDialog(self.matrix, action=ImportExportAction(
            ImportExportAction.EXPORT, directory=export_dir), parent=self)
        d.exec_()
        

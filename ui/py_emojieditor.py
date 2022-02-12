import mimetypes
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from lib.matrix import MXC_RE, MatrixAPI
from PyQt5 import QtCore
from PyQt5.QtCore import (QCoreApplication, QMutex, QObject, Qt,
                          QThread, QTimer, pyqtSignal, pyqtSlot, QAbstractTableModel, QModelIndex,
                          QVariant, QTimer)
from PyQt5.QtGui import QIcon, QMovie, QPixmap
from PyQt5.QtWidgets import (QDialog, QFileDialog, QLabel,
                             QMessageBox, QPlainTextEdit, QProgressBar,
                             QVBoxLayout, QTableView, QItemDelegate, QLabel)

from .emojieditor import Ui_EmojiEditor
from .ImportExportHandlerAndProgressDialog import \
    Ui_ImportExportHandlerAndProgressDialog

EMOJI_DIR = r'emojis'


class EmojiDownloadThread(QThread):
    emojiFinished = pyqtSignal(int, bytes, str, str, name="emojiFinished")
    keepRunning = True

    def __init__(self, parent: Optional[QObject], matrix: MatrixAPI, emojilist: Dict) -> None:
        super().__init__(parent)
        self.emojilist = emojilist
        self.matrix = matrix
        self.keepRunning = True

    def abort_gracefully(self):
        self.keepRunning = False

    def run(self):
        for i, mxc in self.emojilist.items():
            if self.keepRunning == False:
                break

            emojiBytes, mimetype, filepath = self.getCachedEmoji(
                mxc, width=128, height=128)
            self.emojiFinished.emit(i, emojiBytes, mimetype, filepath)

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
                        print("Cached emoji", mediaid)
                        mimetype, _ = mimetypes.guess_type(p)
                        mimetype = mimetype or 'application/octet-stream'
                        with open(os.path.join(EMOJI_DIR, p), 'rb') as f:
                            return f.read(), mimetype, os.path.join(EMOJI_DIR, p),

            print("Downloading emoji", mediaid)
            emojiBytes, content_type = self.matrix.media_get_thumbnail(
                mxcurl, width=width, height=height)
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
        emojiname = ':' + nakedfilename + ':'

        if self.append and emojiname in self.emotes:
            return

        mxc = self.matrix.upload_media(file)
        self.emotes['images'][emojiname] = {
            'url': mxc
        }

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
        

class EmojiTableModel(QAbstractTableModel):
    matrix: MatrixAPI
    emoticons: dict
    
    def __init__(self, emotes, *args, **kwargs) -> None:
        super().__init__()
        self.emoticons = emotes
        
    def index_to_key(self, index: int) -> str:
        a = list(self.emoticons)[index]
        return a
        
    def rowCount(self, parent: QModelIndex) -> int:
        return len(self.emoticons)
    
    def columnCount(self, index: QModelIndex):
        return 3
    
    def headerData(self, column, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            if column == 0:
                return QVariant('Preview')
            elif column == 1:
                return QVariant('Short Code')
            elif column == 2:
                return QVariant('MXC URL')

    def data(self, index: QModelIndex, role: int) -> Any:        
        if index.row() > len(self.emoticons):
            return QVariant()

        item = self.emoticons[self.index_to_key(index.row())]
        #print(item)
        
        if role == Qt.DisplayRole:
            keys = list(item.keys())
            shortcode = self.index_to_key(index.row())
            if index.column() == 2:
                return str(shortcode)
            elif index.column() == 1:
                return item['url']
            elif index.column() == 0:
                return "Preview goes here :3"
            else: return QVariant()
        elif role == Qt.EditRole and index.column() == 0:
            return index.data(role)
        
        return QVariant()
    
    
    def setData(self, index, value, role=Qt.EditRole):
        #self.emoticons[index.row()]
        #print("Update", index, value)
        emkey = self.index_to_key(index.row())
        self.emoticons[emkey] = value
        self.dataChanged.emit(index, index)


class EmojiTableDelegate(QItemDelegate):
    def __init__(self, parent = None, *args, **kwargs) -> None:
        super().__init__(parent=parent, *args, **kwargs)
        
    def paint(self, painter, option, index):
        if index.column() != 0:
            return super().paint(painter, option, index)
        
        emotes = self.parent().emoticons
        
        emote = emotes[list(emotes)[index.row()]]
        #print(emote)
        pm: QPixmap = None
        if 'pixmap' in emote:
            pm = emote['pixmap']
        elif 'movie' in emote:
            movie = emote['movie']
            pm = movie.currentPixmap()
        else:
            return super().paint(painter, option, index)
        
        drawable = pm.scaled(option.rect.width(), option.rect.height(), Qt.KeepAspectRatio)
        
        painter.save()
        painter.translate(option.rect.topLeft())
        #w.render(painter)
        #drawable.render(painter)
        painter.drawPixmap(0, 0, drawable)
        painter.restore()
        

class EmojiEditor(Ui_EmojiEditor, QDialog):
    updateRowMutex = QMutex()
    room: str = None

    def __init__(self, matrixapi: MatrixAPI, room: Optional[str] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowIcon(QIcon(":/icon.png"))
        self.updateRowMutex = QMutex()
        self.emoteDownloadInterval = QTimer(parent=self)
        self.emoteDownloadInterval.setInterval(100)
        self.emoteDownloadInterval.stop()
        self.emoteDownloadInterval.timeout.connect(self.downloadAnotherEmoji)
        
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
                self.populateForm()

        # @todo: simplify this and extract a method or something? i dunno im just a dumb fox 🦊
        def importAppend():
            files = select_files()
            if len(files) <= 0: return
            dlg = EmojiUploaderTask(
                files, append=True, matrix=self.matrix,  room=self.room, parent=self)
            if dlg.exec_():
                self.populateForm()

        self.actionImport_overwrite.triggered.connect(importOverwrite)
        self.actionImport_append.triggered.connect(importAppend)
        self.actionExport.triggered.connect(self.exportEmojis)

        if not os.path.lexists(EMOJI_DIR) and not os.path.isdir(EMOJI_DIR):
            os.mkdir(EMOJI_DIR)

        self.matrix = matrixapi
        self.populateForm()

    @pyqtSlot()
    def closeEvent(self, event):
        #self.emoji_dl_thr.abort_gracefully()
        #self.emoji_dl_thr.wait(1000)
        event.accept()

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

    def populateForm(self):
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
        
        self.emoticons = emoticons
        self.emoteDownloadInterval.start()
        #print(self.emoticons)        
        
        t: QTableView = self.tableView
        self.m = EmojiTableModel(self.emoticons)
        d = EmojiTableDelegate(self)
        t.setModel(self.m)
        t.setItemDelegate(d)
    
    
    def downloadAnotherEmoji(self):
        for emotekey in self.emoticons:
            emoticon = self.emoticons[emotekey]
            row = list(self.emoticons.keys()).index(emotekey)
            if 'localpath' in emoticon:
                # already locally cached
                
                if 'pixmap' not in emoticon:
                    # create the pixmap    
            
                    if 'image/gif' in emoticon['mime']:
                        movie = QMovie(emoticon['localpath'])
                        # @todo: movie.setScaledSize() to something aspect ratio correct
                        movie.start()
                        emoticon['movie'] = movie
                    else:
                        pm = QPixmap(emoticon['localpath'])
                        pm = pm.scaled(128, 128, Qt.KeepAspectRatio)
                        #preview.setPixmap(pm)
                        emoticon['pixmap'] = pm
                    self.emoticons[emotekey] = emoticon
                    self.m.setData(
                        self.m.createIndex(row, 0),
                        emoticon
                    )
                continue
            
            # download emoticon
            #print(emoticon)
            m = MXC_RE.search(emoticon['url'])
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
                            print("Cached emoji", mediaid)
                            mimetype, _ = mimetypes.guess_type(p)
                            mimetype = mimetype or 'application/octet-stream'
                            emoticon['mime'] = mimetype
                            emoticon['localpath'] = os.path.join(EMOJI_DIR, p)
                            self.emoticons[emotekey] = emoticon
                            continue

                return
                print("Downloading emoji", mediaid)
                emojiBytes, content_type = self.matrix.media_get_thumbnail(
                    emoticon['url'], width=128, height=128
                )
                ext = mimetypes.guess_extension(content_type) or '.bin'
                mediapath = mediapath.with_suffix(ext)

                with open(str(mediapath), 'wb') as f:
                    f.write(emojiBytes)
                emoticon['localpath'] = str(mediapath)
                self.emoticons[emotekey] = emoticon
                return

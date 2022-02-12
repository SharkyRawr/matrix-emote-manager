import sys

from PyQt5.QtWidgets import QApplication


def compileUI():
    from PyQt5.uic import compileUiDir
    compileUiDir('ui')
    from PyQt5.pyrcc_main import processResourceFile
    processResourceFile(['res/res.qrc'], 'res/res.py', False)


if __name__ == "__main__":

    if not 'frozen' in dir(sys):
        compileUI()
    from ui.py_mainwindow import MainWindow
    
    # init db
    from lib.db import init_db
    init_db()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

import sys

import os
from os import path

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5 import QtGui

from TransferFiles import Ui_MainWindow
from ADB import ADB, ADBException


class MyResources():
    icons = {}

    @staticmethod
    def init():
        MyResources.addIcon('dir', ":/img/img/directory.png")
        MyResources.addIcon('file', ":/img/img/file.png")


    @staticmethod
    def addIcon(key, file):
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(file), QtGui.QIcon.Normal, QtGui.QIcon.On)
        MyResources.icons[key] = icon


class MyForm(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, initLocalDir='/', initRemoteDir='/'):
        super(MyForm, self).__init__()
        self.setupUi(self)
        self.__initLocalFileView(initLocalDir)
        self.__initRemoteFileView(initRemoteDir)
        self.btnToRemote.clicked.connect(self.transferFilesToRemote)
        self.btnToLocal.clicked.connect(self.transferFilesToLocal)
        self.txtLocalPath.returnPressed.connect(lambda: self.changeLocalDir(self.txtLocalPath.text()))
        self.txtRemotePath.returnPressed.connect(lambda: self.changeRemoteDir(self.txtRemotePath.text()))


    def __initLocalFileView(self, initLocalDir):
        """ 初始化本地文件浏览器"""
        self.__curLocalDir = None
        self.__localDirStack = []
        # 转到初始本地目录
        self.changeLocalDir(initLocalDir)

        self.lstLocal.itemDoubleClicked.connect(
            lambda li: self.changeLocalDir(path.join(self.curLocalDir, li.text())))
        self.btnLocalUp.clicked.connect(lambda: self.changeLocalDir(path.dirname(self.curLocalDir)))
        self.btnLocalRefresh.clicked.connect(lambda: self.changeLocalDir(self.curLocalDir))

    def changeLocalDir(self, directory):
        """修改当前的本地目录"""
        try:
            directory = directory or '/'
            if not path.isdir(directory):
                return
            dirs = [m for m in os.scandir(directory) if m.is_dir()]
            files = [m for m in os.scandir(directory) if m.is_file()]
            self.lstLocal.clear()
            for d in dirs:
                li = QListWidgetItem()
                li.setIcon(MyResources.icons['dir'])
                li.setText(d.name)
                li.fileType = 1
                self.lstLocal.addItem(li)
            for f in files:
                li = QListWidgetItem()
                li.setIcon(MyResources.icons['file'])
                li.setText(f.name)
                li.fileType = 0
                self.lstLocal.addItem(li)
            self.curLocalDir = directory
        except Exception:
            pass

    def __initRemoteFileView(self, initRemoteDir):
        """初始化本地文件浏览器"""
        self.__curRemoteDir = None
        self.__remoteDirStack = []
        self.__adb = ADB()
        # 转到初始远程目录
        self.changeRemoteDir(initRemoteDir)

        self.lstRemote.itemDoubleClicked.connect(
            lambda li: self.changeRemoteDir(self.curRemoteDir and path.join(self.curRemoteDir, li.text())))
        self.btnRemoteUp.clicked.connect(lambda: self.curRemoteDir and self.changeRemoteDir(path.dirname(self.curRemoteDir)))
        self.btnRemoteRefresh.clicked.connect(lambda: self.changeRemoteDir(self.curRemoteDir))

    def changeRemoteDir(self, directory):
        """修改当前的本地目录"""
        # if not path.isdir(directory):
        #     return
        directory = directory or '/'
        self.lstRemote.clear()
        try:
            dirs, files = self.__adb.ls(directory)
            if dirs is None or files is None:
                self.setStatusTip('没有连接设备')
                return
        except ADBException as e:
            self.setStatusTip(e.msg)
            return

        for d in dirs:
            li = QListWidgetItem()
            li.setIcon(MyResources.icons['dir'])
            li.setText(d.name)
            li.fileType = 1
            self.lstRemote.addItem(li)
        for f in files:
            li = QListWidgetItem()
            li.setIcon(MyResources.icons['file'])
            li.setText(f.name)
            li.fileType = 0
            self.lstRemote.addItem(li)
        self.curRemoteDir = directory

    def transferFilesToRemote(self):
        """传送文件到远程"""
        selected = self.lstLocal.selectedItems()
        if len(selected) > 0:
            files = [path.join(self.curLocalDir, x.text()) for x in selected]
            result = self.__adb.push(files, self.curRemoteDir)
            self.btnRemoteRefresh.click()
            if result == 0:
                self.lstLocal.clearSelection()
            else:
                self.setStatusBar("传输错误! 错误码:" + str(result))

    def transferFilesToLocal(self):
        """传送文件到本地"""
        selected = self.lstRemote.selectedItems()
        if len(selected) > 0:
            files = [path.join(self.curRemoteDir, x.text()) for x in selected]
            result = self.__adb.pull(files, self.curLocalDir)
            self.btnLocalRefresh.click()
            if result == 0:
                self.lstRemote.clearSelection()
            else:
                self.setStatusBar("传输错误! 错误码:" + str(result))

    @property
    def curLocalDir(self):
        return self.__curLocalDir

    @curLocalDir.setter
    def curLocalDir(self, directory):
        self.__curLocalDir = directory
        self.txtLocalPath.setText(directory)

    @property
    def curRemoteDir(self):
        return self.__curRemoteDir

    @curRemoteDir.setter
    def curRemoteDir(self, directory):
        self.__curRemoteDir = directory
        self.txtRemotePath.setText(directory)


def main():
    app = QtWidgets.QApplication(sys.argv)
    MyResources.init()
    initLocalDir = len(sys.argv) > 1 and sys.argv[1] or '/'
    initRemoteDir = len(sys.argv) > 2 and sys.argv[2] or '/'

    f = MyForm(initLocalDir, initRemoteDir)
    f.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


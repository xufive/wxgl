#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QToolBar, QHBoxLayout
from PyQt6.QtGui import QIcon, QAction, QScreen, QImage, QPixmap
from PyQt6.QtCore import Qt, QByteArray

from . qtscene import QtScene
from . import imgres

app = QApplication(sys.argv)

class QtFigure(QMainWindow):
    """基于qt的画布类"""

    def __init__(self, scheme, **kwds):
        """构造函数

        kwds        - 关键字参数
            size        - 窗口分辨率，默认960×640
            bg          - 画布背景色，默认(0.0, 0.0, 0.0)
            haxis       - 高度轴，默认y轴，可选z轴，不支持x轴
            fovy        - 相机水平视野角度，默认50°
            azim        - 方位角，默认0°
            elev        - 高度角，默认0°
            azim_range  - 方位角变化范围，默认-180°～180°
            elev_range  - 高度角变化范围，默认-180°～180°
            smooth      - 直线和点的反走样，默认True
        """

        super().__init__()

        self.setWindowTitle('GLTK')
        self.setWindowIcon(self.get_qicon('appicon', 'ico'))
        self.statusBar()

        size = kwds.get('size', (960,640))
        self.resize(*size)
        screen = self.screen().availableGeometry()
        self.move((screen.width() - size[0])//2, (screen.height() - size[1])//2)

        self.scene = QtScene(self, scheme, **kwds)

        saveAction = QAction(self.get_qicon('save', 'png'), '&保存', self)
        saveAction.setStatusTip('保存画布')
        saveAction.triggered.connect(self.on_save)
 
        homeAction = QAction(self.get_qicon('home', 'png'), '&复位', self)
        homeAction.setStatusTip('初始位置')
        homeAction.triggered.connect(self.on_home)
 
        self.icon_play = self.get_qicon('play', 'png')
        self.icon_pause = self.get_qicon('pause', 'png')
        self.animateAction = QAction(self.icon_play, '&动画', self)
        self.animateAction.setStatusTip('动画')
        self.animateAction.triggered.connect(self.on_pause)
 
        if scheme.alive:
            self.animateAction.setIcon(self.icon_pause)
            self.animateAction.setToolTip('暂停')
        else:
            self.animateAction.setEnabled(False)

        tb = QToolBar(self)
        tb.addAction(saveAction)
        tb.addAction(homeAction)
        tb.addAction(self.animateAction)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, tb)

        box = QHBoxLayout()
        box.addWidget(self.scene)

        main_widget = QWidget()
        main_widget.setLayout(box)
        self.setCentralWidget(main_widget)

    def closeEvent(self, evt):
        """重写关闭事件函数"""

        self.scene.clear_buffer()

    def get_qicon(self, name, ext):
        """返回qicon对象"""

        image = QImage()
        image.loadFromData(QByteArray().fromBase64(imgres.data[name].encode()), ext)

        return QIcon(QPixmap.fromImage(image))

    def on_home(self):
        """恢复初始位置和姿态"""

        self.scene.home()

    def on_save(self):
        """将缓冲区保存为图像文件"""

        self.scene.save()

    def on_pause(self):
        """动画/暂停"""

        self.scene.pause()

        self.animateAction.setIcon(self.icon_pause)
        self.animateAction.setToolTip('暂停')

        if self.scene.playing:
            self.animateAction.setIcon(self.icon_pause)
            self.animateAction.setToolTip('暂停')
        else:
            self.animateAction.setIcon(self.icon_play)
            self.animateAction.setToolTip('动画')

    def loop(self):
        """显示画布，侦听事件"""

        self.show() # 显示窗口
        app.exec()


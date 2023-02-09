#!/usr/bin/env python3

import sys, os, time
import numpy as np
import threading
import imageio
import webp
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QToolBar, QHBoxLayout, QFileDialog
from PyQt6.QtGui import QIcon, QAction, QImage, QPixmap
from PyQt6.QtCore import Qt, QByteArray, pyqtSignal, QThread

from . qtscene import QtScene
from . import imgres

class FileCreator(QThread):
    """图像或动画文件生成器"""

    shoot = pyqtSignal(str, bool)
    finish = pyqtSignal()

    def __init__(self, fig):
        """构造函数"""

        super(FileCreator, self).__init__()
        self.fig = fig

    def run(self):
        """启动服务"""

        self.fig.scene.increment = False
        self.fig.scene.duration = 0

        ft = round(1000/self.fig.fps)
        while not self.fig.scene.gl_init_done:
            time.sleep(0.1)
        
        #time.sleep(0.5)

        if self.fig.ext in ('.png', '.jpg', '.jpeg'):
            self.shoot.emit('RGBA' if self.fig.ext=='.png' else 'RGB', False)
            time.sleep(0.1)
            
            if isinstance(self.fig.dpi, (int, float)):
                self.fig.scene.im_pil.save(self.fig.outfile, dpi=(self.fig.dpi, self.fig.dpi))
            else:
                self.fig.scene.im_pil.save(self.fig.outfile)
        elif self.fig.ext == '.webp':
            w, h = self.fig.scene.csize
            enc = webp.WebPAnimEncoder.new(w-49, h-31)
            cfg = webp.WebPConfig.new(quality=100)
            timestamp_ms = 0
            while self.fig.cn < self.fig.frames:
                self.fig.scene.duration = self.fig.cn * ft
                self.shoot.emit('RGBA', False)
                time.sleep(0.1)

                pic = webp.WebPPicture.from_pil(self.fig.scene.im_pil)
                enc.encode_frame(pic, timestamp_ms, cfg)
                timestamp_ms += ft
                self.fig.cn += 1
 
            anim_data = enc.assemble(timestamp_ms)
            with open(self.fig.outfile, 'wb') as fp:
                fp.write(anim_data.buffer())
        else:
            if self.fig.ext == '.gif':
                writer = imageio.get_writer(self.fig.outfile, fps=self.fig.fps, loop=self.fig.loop)
            else:
                writer = imageio.get_writer(self.fig.outfile, fps=self.fig.fps)

            while self.fig.cn < self.fig.frames:
                self.fig.scene.duration = self.fig.cn * ft
                self.shoot.emit('RGBA', True)
                time.sleep(0.1)

                im = np.array(self.fig.scene.im_pil)
                writer.append_data(im)
                self.fig.cn +=1
 
            writer.close()

        self.finish.emit()

class QtFigure(QMainWindow):
    """基于qt的画布类"""

    def __init__(self, scheme, **kwds):
        """构造函数

        scheme      - 展示方案
        kwds        - 关键字参数
            outfile     - 输出文件名
            ext         - 输出文件扩展名
            dpi         - 图像文件每英寸像素数
            fps         - 动画文件帧率
            frames      - 动画文件总帧数
            loop        - gif文件播放次数，0表示循环播放
            quality     - webp文件质量，100表示最高品质
        """

        self.outfile = kwds.get('outfile')
        self.ext = kwds.get('ext')
        self.dpi = kwds.get('dpi')
        self.fps = kwds.get('fps')
        self.frames = kwds.get('frames')
        self.loop = kwds.get('loop')
        self.quality = kwds.get('quality')

        super().__init__()

        self.setWindowTitle('WxGL')
        self.setWindowIcon(self.get_qicon('appicon', 'ico'))
        self.statusBar()

        size = scheme.kwds.get('size', (960,640))
        self.resize(*size)
        screen = self.screen().availableGeometry()
        self.move((screen.width() - size[0])//2, (screen.height() - size[1])//2)

        self.scene = QtScene(self, scheme, **scheme.kwds)

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

        if not self.outfile is None:
            self.cn = 0
            self.creator = FileCreator(self)
            self.creator.shoot.connect(self.capture)
            self.creator.finish.connect(self.close)
            self.creator.start()

    def closeEvent(self, evt):
        """重写关闭事件函数"""

        self.scene.clear_buffer()

    def keyPressEvent(self, evt):
        """重写键盘按下事件函数"""
        
        if evt.key() == Qt.Key.Key_Control.value:
            self.scene.ctrl_down = True

    def keyReleaseEvent(self, evt):
        """重写键盘弹起事件函数"""
        
        if evt.key() == Qt.Key.Key_Escape.value:
            self.scene.home()
        if evt.key() == Qt.Key.Key_Control.value:
            self.scene.ctrl_down = False

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

        self.scene.stop_idle()
        im = self.scene.get_buffer()

        file_type = 'PNG files (*.png);;JPEG file (*.jpg)'
        fname, fext = QFileDialog.getSaveFileName(self, '保存文件', directory=os.getcwd(), filter=file_type)
        name, ext = os.path.splitext(fname)

        if name:
            if ext != '.png' and ext != '.jpg':
                ext = '.png' if fext == 'PNG files (*.png)' else '.jpg'

            if ext == '.jpg':
                im.convert('RGB').save('%s%s'%(name, ext))
            else:
                im.save('%s%s'%(name, ext))

        self.scene.start_idle()

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

    def capture(self, mode, crop):
        """捕捉缓冲区数据"""

        self.scene.update()
        self.scene.capture(mode=mode, crop=crop)

def show_qtfigure(scheme, **kwds):
    """保存画布为图像文件或动画文件

    kwds        - 关键字参数
        outfile     - 输出文件名
        ext         - 输出文件扩展名
        dpi         - 图像文件每英寸像素数
        fps         - 动画文件帧率
        frames      - 动画文件总帧数
        loop        - gif文件播放次数，0表示循环播放
        quality     - webp文件质量，100表示最高品质
    """

    app = QApplication(sys.argv)
    fig = QtFigure(scheme, **kwds)
    fig.show()
    app.exec()
    app.quit()
    scheme.reset()


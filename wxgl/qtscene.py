#!/usr/bin/env python3

from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt

from . scene import BaseScene

class QtScene(BaseScene, QOpenGLWidget):
    """从QOpenGLWidget类和BaseScene类派生的场景类"""

    def __init__(self, parent, scheme, **kwds):
        """构造函数"""
        
        super(QtScene, self).__init__(scheme, **kwds)
        super(BaseScene, self).__init__(parent)

        self.timer_id = self.startTimer(0, Qt.TimerType.CoarseTimer)

    def timerEvent(self, evt):
        """重写定时事件函数"""

        self.update()
 
    def paintGL(self):
        """重写绘制函数"""
 
        if not self.gl_init_done:
            self._initialize_gl()
            self._assemble()

        self._paint()

    def resizeGL(self, width, height):
        """重写改变窗口事件函数"""
 
        self.csize = (width, height)
        self._resize()
        self.update()

    def home(self):
        """恢复初始位置和姿态"""

        self._home()
        self.update()

    def pause(self):
        """动画/暂停"""

        self._pause()

    def capture(self, mode='RGBA', crop=False, buffer='front'):
        """捕捉缓冲区数据
 
        mode        - 'RGB'或'RGBA'
        crop        - 是否将宽高裁切为16的倍数
        buffer      - 'front'（前缓冲区）或'back'（后缓冲区）
        """

        self.im_pil = self._get_buffer(mode=mode, crop=crop, buffer=buffer, qt=True)

    def get_buffer(self, mode='RGBA', crop=False, buffer='front'):
        """以PIL对象的格式返回场景缓冲区数据
 
        mode        - 'RGB'或'RGBA'
        crop        - 是否将宽高裁切为16的倍数
        buffer      - 'front'（前缓冲区）或'back'（后缓冲区）
        """

        return self._get_buffer(mode=mode, crop=crop, buffer=buffer, qt=True)

    def mousePressEvent(self, evt):
        """重写鼠标按键被按下事件函数"""
        
        if evt.buttons() == Qt.MouseButton.LeftButton:
            self.left_down = True
            self.mouse_pos = evt.position()
    
    def mouseReleaseEvent(self, evt):
        """重写鼠标按键被释放事件函数"""
        
        if evt.buttons() == Qt.MouseButton.LeftButton:
            self.left_down = False
        elif evt.buttons() == Qt.MouseButton.RightButton:
            self.home()
        
    def mouseMoveEvent(self, evt):
        """重写鼠标移动事件函数"""
        
        if self.left_down:
            pos = evt.position()
            dx, dy = pos.x()-self.mouse_pos.x(), pos.y()-self.mouse_pos.y()
            self.mouse_pos = pos
            
            self._drag(dx, dy)
            self.update()
        
    def wheelEvent(self, evt):
        """重写鼠标滚轮事件函数"""
        
        self._wheel(evt.angleDelta().y())
        self.update()

    def start_idle(self):
        """启动idle"""
        
        self.timer_id = self.startTimer(0, Qt.TimerType.CoarseTimer)

    def stop_idle(self):
        """停止idle"""
        
        self.killTimer(self.timer_id)


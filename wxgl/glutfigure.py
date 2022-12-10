#!/usr/bin/env python3

import time
import uuid
import numpy as np

from OpenGL.GLUT import *

from . scene import BaseScene

class GlutFigure(BaseScene):
    """基于OpenGl.GLUT的画布类"""

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

        super().__init__(scheme, **kwds)

    def _init_gl(self):
        """初始化GL"""

        glutInit() # 初始化glut库

        sw, sh = glutGet(GLUT_SCREEN_WIDTH), glutGet(GLUT_SCREEN_HEIGHT)
        left, top = (sw-self.csize[0])//2, (sh-self.csize[1])//2

        glutInitWindowSize(*self.csize) # 设置窗口大小
        glutInitWindowPosition(left, top) # 设置窗口位置
        glutCreateWindow('OpenGL Toolkit') # 创建窗口
 
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH) # 设置显示模式
        self._initialize_gl()

    def reshape(self, w, h):
        """改变窗口大小事件函数"""
 
        self.csize = (w, h)
        self._resize()
        glutPostRedisplay()

    def click(self, btn, state, x, y):
        """鼠标按键和滚轮事件函数"""
 
        if btn == 0: # 左键
            if state == 0: # 按下
                self.left_down = True
                self.mouse_pos = (x, y)
            else: # 弹起
                self.left_down = False 
        elif btn == 2 and state ==1: # 右键弹起
            if self.scheme.alive: # 恢复初始位置和姿态
                self.fovy = self.origin['fovy']
                self._update_cam_and_up(dist=self.origin['dist'], azim=self.origin['azim'], elev=self.origin['elev'])
                self._update_view_matrix()
                self._update_proj_matrix()
            elif self.playing: # 暂停
                self.playing = False
                self.tbase = self.duration
            else: # 动画
                self.start = 1000 * time.time()
                self.playing = True
        elif btn == 3 and state == 0: # 滚轮前滚
            self.fovy *= 0.95
            self._update_proj_matrix()
        elif btn == 4 and state == 0: # 滚轮后滚
            self.fovy += (180 - self.fovy) / 180
            self._update_proj_matrix()
 
        glutPostRedisplay()

    def drag(self, x, y):
        """鼠标拖拽事件函数"""
 
        dx, dy = x - self.mouse_pos[0], y - self.mouse_pos[1]
        self.mouse_pos = (x, y)
        self._drag(dx, dy)
        glutPostRedisplay()

    def draw(self):
        """重绘事件函数"""

        self._paint()
        glutSwapBuffers() # 交换缓冲区

    def idle(self):
        """idle事件函数"""

        self._timer()
        glutPostRedisplay()

    def loop(self):
        """显示画布，侦听事件"""

        self._init_gl()
        self.reshape(*self.csize)
        self._assemble()

        glutDisplayFunc(self.draw)
        glutIdleFunc(self.idle)
        glutReshapeFunc(self.reshape)
        glutMouseFunc(self.click)
        glutMotionFunc(self.drag)
        glutMainLoop()


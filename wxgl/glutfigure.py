#!/usr/bin/env python3

import time
import numpy as np
import threading
import imageio
import webp
import queue

from OpenGL.GLUT import *

from . scene import BaseScene

class GlutFigure(BaseScene):
    """基于OpenGl.GLUT的画布类"""

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
        self.fps = kwds.get('fps', 25)
        self.frames = kwds.get('frames', 100)
        self.loop = kwds.get('loop', 0)
        self.quality = kwds.get('quality', 100)
        self.ft = None

        super().__init__(scheme, **scheme.kwds)
        
        if not self.outfile is None and self.ext not in ('.png', '.jpg', '.jpeg'):
            self.cn = 0
            self.q = queue.Queue()
            self.finished = False
            self.ft = round(1000/self.fps)
            
            threading_record = threading.Thread(target=self.create_animation)
            threading_record.setDaemon(True)
            threading_record.start()

    def _init_gl(self):
        """初始化GL"""

        glutInit() # 初始化glut库

        sw, sh = glutGet(GLUT_SCREEN_WIDTH), glutGet(GLUT_SCREEN_HEIGHT)
        left, top = (sw-self.csize[0])//2, (sh-self.csize[1])//2

        glutInitWindowSize(*self.csize) # 设置窗口大小
        glutInitWindowPosition(left, top) # 设置窗口位置
        glutCreateWindow('WxGL') # 创建窗口
 
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
                self._home()
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

        self._timer(delta=self.ft)
        glutPostRedisplay()

        if not self.outfile is None:
            if self.ext in ('.png', '.jpg', '.jpeg'):
                im = self._get_buffer(mode='RGBA' if self.ext=='.png' else 'RGB')
                if isinstance(self.dpi, (int, float)):
                    im.save(self.outfile, dpi=(self.dpi, self.dpi))
                else:
                    im.save(self.outfile)
                glutDestroyWindow(glutGetWindow())
            elif self.finished:
                glutDestroyWindow(glutGetWindow())
            else:
                if self.cn < self.frames:
                    im = self._get_buffer(crop=True)
                    self.q.put(im)

    def create_animation(self):
        """生成动画文件的线程函数"""
 
        if self.ext == '.webp':
            enc = webp.WebPAnimEncoder.new(*self.csize)
            cfg = webp.WebPConfig.new(quality=100)
            timestamp_ms = 0
            while self.cn < self.frames:
                pic = webp.WebPPicture.from_pil(self.q.get())
                enc.encode_frame(pic, timestamp_ms, cfg)
                timestamp_ms += int(1000/self.fps)
                self.cn += 1

            anim_data = enc.assemble(timestamp_ms)
            with open(self.outfile, 'wb') as fp:
                fp.write(anim_data.buffer())
        else:
            if self.ext == '.gif':
                writer = imageio.get_writer(self.outfile, fps=self.fps, loop=self.loop)
            else:
                writer = imageio.get_writer(self.outfile, fps=self.fps)
 
            while self.cn < self.frames:
                im = np.array(self.q.get())
                writer.append_data(im)
                self.cn +=1
 
            writer.close()
        
        self.finished = True

def xx_show_figure(scheme):
    """显示画布"""

    fig = GlutFigure(scheme)
    fig._init_gl()
    fig.reshape(*fig.csize)
    fig._assemble()

    glutDisplayFunc(fig.draw)
    glutIdleFunc(fig.idle)
    glutReshapeFunc(fig.reshape)
    glutMouseFunc(fig.click)
    glutMotionFunc(fig.drag)
    glutMainLoop()
    
    scheme.reset()

def show_figure(scheme, **kwds):
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

    fig = GlutFigure(scheme, **kwds)
    fig._init_gl()
    fig.reshape(*fig.csize)
    fig._assemble()

    glutDisplayFunc(fig.draw)
    glutIdleFunc(fig.idle)
    glutReshapeFunc(fig.reshape)
    glutMouseFunc(fig.click)
    glutMotionFunc(fig.drag)
    glutMainLoop()
    
    scheme.reset()


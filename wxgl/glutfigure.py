#!/usr/bin/env python3

import time
import numpy as np
import threading
import imageio
import webp

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
        self.fps = kwds.get('fps')
        self.frames = kwds.get('frames')
        self.loop = kwds.get('loop')
        self.quality = kwds.get('quality')

        super().__init__(scheme, **scheme.kwds)
        
        if not self.outfile is None:
            self.cn = 0
            self.finished = False
            
            threading_record = threading.Thread(target=self.create_file)
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

        if self.outfile:
            mode = 'RGB' if self.ext in ('.jpg', '.jpeg') else 'RGBA'
            crop = True if self.ext in ('.mp4', '.avi', '.wmv', '.mov') else False
            self.im_pil = self._get_buffer(mode=mode, crop=crop)

    def idle(self):
        """idle事件函数"""

        glutPostRedisplay()
        if self.outfile and self.finished:
            glutDestroyWindow(glutGetWindow())

    def create_file(self):
        """生成图像或动画文件的线程函数"""
 
        self.increment = False
        self.duration = 0
        ft = round(1000/self.fps)

        while not self.gl_init_done:
            time.sleep(0.01)

        if self.ext in ('.png', '.jpg', '.jpeg'):
            self.duration = 0
            time.sleep(0.05)

            self.im_pil = None
            while self.im_pil is None:
                time.sleep(0.01)

            if isinstance(self.dpi, (int, float)):
                self.im_pil.save(self.outfile, dpi=(self.dpi, self.dpi))
            else:
                self.im_pil.save(self.outfile)
        elif self.ext == '.webp':
            enc = webp.WebPAnimEncoder.new(*self.csize)
            cfg = webp.WebPConfig.new(quality=100)
            timestamp_ms = 0
            while self.cn < self.frames:
                self.duration = self.cn * ft 
                time.sleep(0.05)

                self.im_pil = None
                while self.im_pil is None:
                    time.sleep(0.01)

                pic = webp.WebPPicture.from_pil(self.im_pil)
                enc.encode_frame(pic, timestamp_ms, cfg)
                timestamp_ms += ft
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
                self.duration = self.cn * ft
                time.sleep(0.05)

                self.im_pil = None
                while self.im_pil is None:
                    time.sleep(0.01)

                im = np.array(self.im_pil)
                writer.append_data(im)
                self.cn +=1
 
            writer.close()
        
        self.finished = True

def show_figure(scheme, **kwds):
    """显示或保存画布

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


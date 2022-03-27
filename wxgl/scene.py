# -*- coding: utf-8 -*-
#
# MIT License
# 
# Copyright (c) 2021 Tianyuan Langzi
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


"""
WxGL: 基于pyopengl的三维数据可视化库

WxGL以wx为显示后端，提供matplotlib风格的交互绘图模式
同时，也可以和wxpython无缝结合，在wx的窗体上绘制三维模型
"""


import os, time
from pynput import keyboard
import wx
from wx import glcanvas
import numpy as np
from PIL import Image
import imageio
import queue
import threading
from OpenGL.GL import *

from . import region
from . import util


class Scene(glcanvas.GLCanvas):
    """GL场景类"""
    
    def __init__(self, parent, smooth=True, style='blue'):
        """构造函数
        
        parent      - 父级窗口对象
        smooth      - 直线、多边形和点的反走样开关
        style       - 场景风格，默认太空蓝
            'white'     - 珍珠白
            'black'     - 石墨黑
            'gray'      - 国际灰
            'blue'      - 太空蓝
            'royal'     - 宝石蓝
        """
        
        self.parent = parent
        glcanvas.GLCanvas.__init__(self, self.parent, -1, style=glcanvas.WX_GL_RGBA|glcanvas.WX_GL_DOUBLEBUFFER|glcanvas.WX_GL_DEPTH_SIZE)
        
        self.smooth = smooth                                                # 反走样开关
        self.style = self._set_style(style)                                 # 设置风格（背景和文本颜色）
        
        self.csize = self.GetClientSize()                                   # OpenGL窗口的大小
        self.context = glcanvas.GLContext(self)                             # OpenGL上下文
        self.regions = list()                                               # 视区列表
        self.selected = list()                                              # 选中的模型列表
        
        self.leftdown = False                                               # 鼠标左键按下
        self.mpos = wx._core.Point()                                        # 鼠标位置
        self.ctr = False                                                    # Ctr键按下
        
        self.tn = 0                                                         # 计数器
        self.tstamp = None                                                  # 开始渲染时的时间戳
        self.tbase = 0                                                      # 开始渲染时的累计时长
        self.duration = 0;                                                  # 累计渲染时长，单位毫秒
        self.islive = False                                                 # 存在动画模型
        self.playing = False                                                # 动画播放中
        self.creating = False                                               # 动画文件生成中
        self.capturing = False                                              # 截屏中
        self.ft = 0                                                         # 录制和输出的帧间隔，单位毫秒
        self.fn = 0                                                         # 录屏总帧数
        self.cn = 0                                                         # 已完成帧数
        self.q = None                                                       # PIL对象数据队列
        
        self._init_gl()                                                     # 画布初始化
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)                   # 绑定canvas销毁事件
        self.Bind(wx.EVT_SIZE, self.on_resize)                              # 绑定canvas大小改变事件
        
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)                      # 绑定鼠标左键按下事件
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)                          # 绑定鼠标左键弹起事件                   
        self.Bind(wx.EVT_RIGHT_UP, self.on_right_up)                        # 绑定鼠标右键弹起事件                   
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)                      # 绑定鼠标移动事件
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)                   # 绑定鼠标滚轮事件
        
        monitor_k = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        monitor_k.start()
    
    def _set_style(self, style):
        """设置风格，返回背景色和前景色"""
        
        if not style in ('black', 'white', 'gray', 'blue', 'royal'):
            raise ValueError('不支持的风格选项：%s'%style)
        
        if style == 'black':
            return (0.0, 0.0, 0.0, 1.0), (0.9, 0.9, 0.9)
        if style == 'white':
            return (1.0, 1.0, 1.0, 1.0), (0.0, 0.0, 0.0)
        if style == 'gray':
            return (0.9, 0.9, 0.9, 1.0), (0.0, 0.0, 0.3)
        if style == 'blue':
            return (0.0, 0.0, 0.2, 1.0), (0.9, 1.0, 1.0)
        if style == 'royal':
            return (0.133, 0.302, 0.361, 1.0), (1.0, 1.0, 0.7)
    
    def _init_gl(self):
        """初始化GL"""
        
        self.SetCurrent(self.context)
        
        glClearColor(*self.style[0],)                                       # 设置画布背景色
        glEnable(GL_DEPTH_TEST)                                             # 开启深度测试，实现遮挡关系        
        glDepthFunc(GL_LEQUAL)                                              # 设置深度测试函数
        glShadeModel(GL_SMOOTH)                                             # GL_SMOOTH(光滑着色)/GL_FLAT(恒定着色)
        glEnable(GL_BLEND)                                                  # 开启混合        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)                   # 设置混合函数
        glEnable(GL_ALPHA_TEST)                                             # 启用Alpha测试 
        glAlphaFunc(GL_GREATER, 0.05)                                       # 设置Alpha测试条件为大于0.05则通过
        
        if self.smooth:
            glEnable(GL_POINT_SMOOTH)                                       # 开启点反走样
            glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)                         # 最高质量点反走样
            glEnable(GL_POLYGON_SMOOTH)                                     # 开启多边形反走样
            glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)                       # 最高质量多边形反走样
            glEnable(GL_LINE_SMOOTH)                                        # 开启直线反走样
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)                          # 最高质量直线反走样
    
    def on_destroy(self, evt):
        """canvas销毁事件函数"""
        
        for reg in self.regions:
            reg.clear_buffer()
        
        evt.Skip()
    
    def on_resize(self, evt):
        """窗口改变事件函数"""
        
        self.SetCurrent(self.context)
        self.csize = self.GetClientSize()
        
        for reg in self.regions:
            reg.update_size()
        
        self.render()
        evt.Skip()
        
    def on_left_down(self, evt):
        """响应鼠标左键按下事件"""
        
        self.leftdown = True
        self.mpos = evt.GetPosition()
        
    def on_left_up(self, evt):
        """响应鼠标左键弹起事件"""
        
        self.leftdown = False
        
    def on_right_up(self, evt):
        """响应鼠标右键弹起事件"""
        
        x, y = evt.GetPosition()
        self.render_pick(x, self.csize[1]-y)
        
    def on_mouse_motion(self, evt):
        """响应鼠标移动事件"""
        
        if evt.Dragging() and self.leftdown:
            pos = evt.GetPosition()
            dx, dy = pos - self.mpos
            self.mpos = pos
            
            for reg in self.regions:
                reg.motion(self.ctr, dx, dy)
            
            self.render()
        
    def on_mouse_wheel(self, evt):
        """响应鼠标滚轮事件"""
        
        for reg in self.regions:
            reg.wheel(self.ctr, evt.WheelRotation)
            
        self.render()
    
    def on_press(self, key):
        """键按下"""
        
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctr = True
    
    def on_release(self, key):
        """键弹起"""
        
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctr = False
        elif key == keyboard.Key.esc:
            wx.CallAfter(self.restore_posture)
    
    def render(self):
        """模型渲染器"""
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT) # 清除屏幕及深度缓存
        
        for reg in self.regions:
            glViewport(*reg.pos, *reg.size) # 设置视口
            
            if reg.cam_cruise:
                v = reg.cam_cruise(self.duration)
                reg.update_cam_and_up(azim=v.get('azim'), elev=v.get('elev'), dist=v.get('dist'))
            
            for name, idx, zmean in reg.mnames[0]:
                self._render_core(reg.models[name][idx], reg.cam, reg.azim, reg.elev)
            
            glDepthMask(False) # 对于半透明模型，禁用深度缓冲（锁定）
            if reg.up[1] > 0 and -90 <= reg.azim < 90 or reg.up[1] < 0 and (reg.azim < -90 or reg.azim >= 90):
                for name, idx, zmean in reg.mnames[1]:
                    self._render_core(reg.models[name][idx], reg.cam, reg.azim, reg.elev)
            else:
                for name, idx, zmean in reg.mnames[1][::-1]:
                    self._render_core(reg.models[name][idx], reg.cam, reg.azim, reg.elev)
            glDepthMask(True) # 释放深度缓冲区
        
        self.SwapBuffers() # 切换缓冲区，以显示绘制内容
        
        if self.capturing:
            if self.cn < self.fn:
                im = self.get_scene_buffer(alpha=True, crop=True)
                self.q.put(im)
                self.cn += 1
            else:
                self.stop_record()
    
    def _render_core(self, m, campos, azim, elev):
        """模型渲染核函数"""
        
        if not m.visible or m.slide and not m.slide(self.duration):
            return
        
        glUseProgram(m.program)
        tsid = 0
        
        for key in m.attribute:
            loc = m.attribute[key].get('loc')
            bo = m.attribute[key]['bo']
            un = m.attribute[key]['un']
            usize = m.attribute[key]['usize']
            bo.bind()
            glVertexAttribPointer(loc, un, GL_FLOAT, GL_FALSE, un*usize, bo)
            glEnableVertexAttribArray(loc)
            bo.unbind()
        
        for key in m.uniform:
            tag = m.uniform[key]['tag']
            loc = m.uniform[key].get('loc')
            
            if tag == 'pmat' or tag == 'vmat':
                if 'v' in m.uniform[key]:
                    glUniformMatrix4fv(loc, 1, GL_FALSE, m.uniform[key]['v'], None)
                else:
                    glUniformMatrix4fv(loc, 1, GL_FALSE, m.uniform[key]['f'](self.duration), None)
            elif tag == 'mmat':
                if 'v' in m.uniform[key]:
                    glUniformMatrix4fv(loc, 1, GL_FALSE, m.uniform[key]['v'], None)
                else:
                    args = m.uniform[key]['f'](self.duration)
                    mmat = util.model_matrix(*args)
                    glUniformMatrix4fv(loc, 1, GL_FALSE, mmat, None)
            elif tag == 'texture':
                eval('glActiveTexture(GL_TEXTURE%d)'%tsid)
                glBindTexture(m.uniform[key]['data'].ttype, m.uniform[key]['tid'])
                glUniform1i(loc, tsid)
                tsid += 1
            elif tag == 'picked':
                glUniform1i(loc, m.picked)
            elif tag == 'campos':
                glUniform3f(loc, *campos)
            elif tag == 'ae':
                glUniform2f(loc, azim, elev)
            else:
                value = m.uniform[key].get('v')
                if value is None:
                    value = m.uniform[key].get('f')(self.duration)
                
                dtype = m.uniform[key]['dtype']
                ndim = m.uniform[key]['ndim']
                if ndim is None:
                    try:
                        eval('glUniform%s(loc, value)'%dtype)
                    except:
                        print('渲染函数出现异常，请通知xufive@gmail.com，如可能的话，请提供shader源码。')
                else:
                    eval('glUniform%s(loc, ndim, value)'%dtype)

        for glcmd, args in m.before:
            glcmd(*args)
        
        if m.indices:
            m.indices['ibo'].bind()
            glDrawElements(m.gltype, m.indices['n'], GL_UNSIGNED_INT, None)
            m.indices['ibo'].unbind()
        else:
            glDrawArrays(m.gltype, 0, m.vshape[0])
        
        for glcmd, args in m.after:
            glcmd(*args)
        
        glUseProgram(0)
    
    def render_pick(self, x, y):
        """拾取渲染器"""
        
        for reg in self.regions:
            if reg.fixed:
                continue
            
            glViewport(*reg.pos, *reg.size)
            
            if reg.cam_cruise:
                v = reg.cam_cruise(self.duration)
                reg.update_cam_and_up(azim=v.get('azim'), elev=v.get('elev'), dist=v.get('dist'))
            
            name_hit, depth_hit, idx_hit = None, 1, 0
            
            for i in (0, 1):
                for name, idx, zmean in reg.mnames[i]:
                    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
                    self._render_core(reg.models[name][idx], reg.cam, reg.azim, reg.elev)
                    
                    d = glReadPixels(x, y, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT, outputType=None)[0,0]
                    if d < depth_hit:
                        name_hit, depth_hit, idx_hit = name, d, idx
            
            if name_hit:
                for m in reg.models[name_hit]:
                    m.picked = not m.picked
                
                if reg.models[name_hit][idx_hit].picked:
                    self.selected.append((reg, name_hit))
                else:
                    self.selected.remove((reg, name_hit))
                
                break
        
        self.render()
    
    def render_on_timer(self):
        """定时器事件函数"""
        
        self.tn += 1
        if self.capturing:
            self.duration = self.tbase + self.ft * self.cn
        else:
            self.duration = self.tbase + int((time.time() - self.tstamp) * 1000)
        
        wx.CallAfter(self.render)
        
        if self.playing:
            wx.CallLater(10, self.render_on_timer)
    
    def start_animate(self):
        """开始动画"""
        
        self.render()
        if self.islive:
            self.tstamp = time.time()
            self.tbase = self.duration
            self.playing = True
            self.render_on_timer()
    
    def stop_animate(self):
        """停止动画"""
        
        self.playing = False
    
    def pause_animate(self):
        """暂停/重启动画"""
        
        if self.playing:
            self.stop_animate()
        else:
            self.start_animate()
    
    def reset_timer(self):
        """复位和定时器相关的参数"""
        
        self.playing = False
        self.capturing = False
        self.creating = False
        self.cn = 0
        self.tn = 0 
        self.tbase = 0
        self.duration = 0
    
    def estimate(self):
        """动画渲染帧频评估"""
        
        return 0 if self.duration == 0 else 1000*self.tn/self.duration
    
    def set_style(self, style):
        """设置风格"""
        
        self.style = self._set_style(style)
        self._init_gl()
        self.render()
    
    def restore_posture(self):
        """还原各视区观察姿态"""
        
        for reg in self.regions:
            reg.restore_posture()
        
        self.reset_timer()
        self.render()
        
    def get_scene_buffer(self, alpha=True, buffer='FRONT', crop=False):
        """以PIL对象的格式返回场景缓冲区数据
        
        alpha       - 是否使用透明通道
        buffer      - 显示缓冲区。默认使用前缓冲区（当前显示内容）
        crop        - 是否将宽高裁切为16的倍数
        """
        
        if alpha:
            gl_mode = GL_RGBA
            pil_mode = 'RGBA'
        else:
            gl_mode = GL_RGB
            pil_mode = 'RGB'
        
        if buffer == 'FRONT':
            glReadBuffer(GL_FRONT)
        elif buffer == 'BACK':
            glReadBuffer(GL_BACK)
        
        data = glReadPixels(0, 0, self.csize[0], self.csize[1], gl_mode, GL_UNSIGNED_BYTE, outputType=None)
        im = Image.fromarray(data.reshape(data.shape[1], data.shape[0], -1), mode=pil_mode)
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
        
        if crop:
            w, h = im.size
            nw, nh = 16*(w//16), 16*(h//16)
            x0, y0 = (w-nw)//2, (h-nh)//2
            x1, y1 = x0+nw, y0+nh
            im = im.crop((x0, y0, x1, y1))
        
        return im
        
    def save_scene(self, fn, alpha=True, buffer='FRONT', crop=False):
        """保存场景为图像文件
        
        fn          - 保存的文件名
        alpha       - 是否使用透明通道
        buffer      - 显示缓冲区。默认使用前缓冲区（当前显示内容）
        crop        - 是否将宽高裁切为16的倍数
        """
        
        im = self.get_scene_buffer(alpha=alpha, buffer=buffer, crop=crop)
        im.save(fn)
    
    def _create_gif_or_video(self, out_file, fps, loop):
        """生成gif或视频文件的线程函数"""
        
        if os.path.splitext(out_file)[1] == '.gif':
            writer = imageio.get_writer(out_file, fps=fps, loop=loop)
        else:
            writer = imageio.get_writer(out_file, fps=fps)
        
        while True:
            if self.q.empty():
                if not self.capturing:
                    break
                else:
                    time.sleep(0.1)
            else:
                im = np.array(self.q.get())
                writer.append_data(im)
        
        writer.close()
        self.creating = False
    
    def start_record(self, out_file, fps, fn, loop):
        """生成gif或视频文件
        
        out_file    - 文件名，支持gif和mp4、avi、wmv等格式
        fps         - 每秒帧数
        fn          - 总帧数
        loop        - 循环播放次数（仅gif格式有效，0表示无限循环）
        """
        
        self.cn = 0
        self.fn = fn
        self.ft = round(1000/fps)
        self.q = queue.Queue()
        self.capturing = True
        self.start_animate()
        
        self.threading_record = threading.Thread(target=self._create_gif_or_video, args=(out_file, fps, loop))
        self.threading_record.setDaemon(True)
        self.threading_record.start()
    
    def stop_record(self):
        """"""
        
        self.cn = 0
        self.capturing = False
        self.stop_animate()
    
    def add_region(self, box, **kwds):
        """添加视区
        
        box         - 视区位置四元组：四个元素分别表示视区左下角坐标、宽度、高度，元素值域[0,1]
        proj        - 投影模式：'O' - 正射投影，'P' - 透视投影（默认）
        fixed       - 锁定模式：固定ECS原点、相机位置和角度，以及视口缩放因子等。布尔型，默认False
        kwds        - 关键字参数
            proj        - 投影模式：'O' - 正射投影，'P' - 透视投影（默认）
            fixed       - 锁定模式：固定ECS原点、相机位置和角度，以及视口缩放因子等。布尔型，默认False
            azim        - 方位角：-180°~180°范围内的浮点数，默认0°
            elev        - 高度角：-180°~180°范围内的浮点数，默认0°
            azim_range  - 方位角限位器：默认-180°~180°
            elev_range  - 仰角限位器：默认-180°~180°
            zoom        - 视口缩放因子：默认1.0
            name        - 视区名
        """
        
        reg = region.Region(self, box, **kwds)
        self.regions.append(reg)
        
        return reg

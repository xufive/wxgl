#!/usr/bin/env python3

import wx
from wx import glcanvas as glc

from . scene import BaseScene

class WxScene(BaseScene, glc.GLCanvas):
    """使用wx作为后端的场景类"""

    def __init__(self, parent, scheme, **kwds):
        """构造函数"""

        super(WxScene, self).__init__(scheme, **kwds)
        super(BaseScene, self).__init__(parent, attribList=(glc.WX_GL_RGBA, glc.WX_GL_DOUBLEBUFFER, glc.WX_GL_DEPTH_SIZE, 24))

        self.context = glc.GLContext(self)
        self.SetCurrent(self.context)

        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)           # 绑定窗口销毁事件
        self.Bind(wx.EVT_SIZE, self.on_resize)                      # 绑定canvas大小改变事件
        self.Bind(wx.EVT_PAINT, self.on_paint)                      # 绑定重绘事件
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase)           # 绑定背景擦除事件
        self.Bind(wx.EVT_IDLE, self.on_idle)                        # 绑定idle事件
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)              # 绑定鼠标左键按下事件
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)                  # 绑定鼠标左键弹起事件                   
        self.Bind(wx.EVT_RIGHT_UP, self.on_right_up)                # 绑定鼠标右键弹起事件                   
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)              # 绑定鼠标移动事件
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)           # 绑定鼠标滚轮事件

    def on_destroy(self, evt):
        """窗口销毁事件函数"""
 
        self.SetCurrent(self.context)
        self.clear_buffer()
        evt.Skip()
 
    def on_resize(self, evt):
        """窗口改变事件函数"""
 
        self.csize = self.GetClientSize()
        self._resize()
        self.Refresh(False) 
        evt.Skip()

    def on_left_down(self, evt):
        """响应鼠标左键按下"""
 
        self.left_down = True
        self.mouse_pos = evt.GetPosition()
        evt.Skip()
 
    def on_left_up(self, evt):
        """响应鼠标左键弹起"""
 
        self.left_down = False
        evt.Skip()
 
    def on_right_up(self, evt):
        """响应鼠标右键弹起"""
 
        self.home()
        evt.Skip()
 
    def on_mouse_motion(self, evt):
        """响应鼠标移动"""
 
        if evt.Dragging() and self.left_down:
            pos = evt.GetPosition()
            dx, dy = pos - self.mouse_pos
            self.mouse_pos = pos

            self._drag(dx, dy)
            self.Refresh(False)

        evt.Skip()
 
    def on_mouse_wheel(self, evt):
        """响应鼠标滚轮"""
 
        self._wheel(evt.WheelRotation)
        self.Refresh(False)
        evt.Skip()

    def on_erase(self, evt):
        """背景擦除事件函数"""

        pass

    def on_paint(self, evt):
        """重绘事件函数"""
        
        self.SetCurrent(self.context)

        if not self.gl_init_done:
            self._initialize_gl()
            self._assemble()
            self.gl_init_done = True

        self._paint()
        self.SwapBuffers()

    def on_idle(self, evt):
        """idle事件函数"""

        self._timer() 
        wx.CallAfter(self.Refresh, False)

    def home(self):
        """恢复初始位置和姿态"""

        self._home()
        self.Refresh(False)

    def pause(self):
        """动画/暂停"""

        self._pause()

    def get_buffer(self, mode='RGBA', crop=False, buffer='front'):
        """以PIL对象的格式返回场景缓冲区数据
 
        mode        - 'RGB'或'RGBA'
        crop        - 是否将宽高裁切为16的倍数
        buffer      - 'front'（前缓冲区）或'back'（后缓冲区）
        """

        self.SetCurrent(self.context)
        return self._get_buffer(mode=mode, crop=crop, buffer=buffer)

        #wildcard = 'PNG files (*.png)|*.png|JPEG file (*.jpg)|*.jpg'
        #dlg = wx.FileDialog(self, message='保存为文件', wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        #dlg.SetFilterIndex(0)
 
        #if dlg.ShowModal() == wx.ID_OK:
        #    fn = dlg.GetPath()
        #    name, ext = os.path.splitext(fn)
        #    
        #    if ext != '.png' and ext != '.jpg':
        #        ext = ['.png', '.jpg'][dlg.GetFilterIndex()]

        #    if ext == '.jpg':
        #        im.convert('RGB').save('%s%s'%(name, ext))
        #    else:
        #        im.save('%s%s'%(name, ext))
        #
        #dlg.Destroy()


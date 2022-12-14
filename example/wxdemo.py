#!/usr/bin/env python3

import wx
import numpy as np
import wxgl
import wxgl.wxscene

class MainFrame(wx.Frame):
    """桌面程序主窗口类"""
 
    def __init__(self):
        """构造函数"""
 
        wx.Frame.__init__(self, None, -1, '多场景演示', style=wx.DEFAULT_FRAME_STYLE)
        self.Maximize()
        self.SetBackgroundColour((224, 224, 224))

        canvas_1 = wxgl.wxscene.WxScene(self, self.draw_scatter())
        canvas_2 = wxgl.wxscene.WxScene(self, self.draw_line(), menu=False)
        canvas_3 = wxgl.wxscene.WxScene(self, self.draw_mesh())
        canvas_4 = wxgl.wxscene.WxScene(self, self.draw_surface())

        sizer_u = wx.BoxSizer()
        sizer_u.Add(canvas_1, 1, wx.EXPAND|wx.ALL, 5)
        sizer_u.Add(canvas_2, 1, wx.EXPAND|wx.ALL, 5)

        sizer_d = wx.BoxSizer()
        sizer_d.Add(canvas_3, 1, wx.EXPAND|wx.ALL, 5)
        sizer_d.Add(canvas_4, 1, wx.EXPAND|wx.ALL, 5)

        sizer_cav = wx.BoxSizer(wx.VERTICAL)
        sizer_cav.Add(sizer_u, 1, wx.EXPAND|wx.ALL, 0)
        sizer_cav.Add(sizer_d, 1, wx.EXPAND|wx.ALL, 0)

        btn_home = wx.Button(self, -1, '复位', size=(100, -1))
        btn_animate = wx.Button(self, -1, '动画', size=(100, -1))

        sizer_btn = wx.BoxSizer(wx.VERTICAL)
        sizer_btn.Add(btn_home, 0, wx.ALL, 20)
        sizer_btn.Add(btn_animate, 0, wx.ALL, 20)

        sizer_max = wx.BoxSizer()
        sizer_max.Add(sizer_cav, 1, wx.EXPAND|wx.LEFT|wx.TOP|wx.BOTTOM, 5)
        sizer_max.Add(sizer_btn, 0, wx.ALL, 20)
        
        self.SetAutoLayout(True)
        self.SetSizer(sizer_max)
        self.Layout()

    def draw_scatter(self):
        vs = np.random.random((30, 3))*2-1
        data = np.arange(30)

        sch = wxgl.Scheme()
        sch.scatter(vs, data=data, size=50, alpha=0.8, texture='res/snow.png')
        
        return sch

    def draw_surface(self):
        vs = np.array([
            [-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5],
            [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5], [0.5, -0.5, -0.5], [-0.5, -0.5, -0.5]
        ], dtype=np.float32)

        indices = np.array([
            0, 3, 1, 1, 3, 2, 4, 0, 5, 5, 0, 1, 3, 7, 2, 2, 7, 6, 
            7, 4, 6, 6, 4, 5, 1, 2, 5, 5, 2, 6, 4, 7, 0, 0, 7, 3  
        ], dtype=np.int32)

        texcoord = np.tile(np.array([[0,0],[0,1],[1,0],[1,0],[0,1],[1,1]], dtype=np.float32), (6,1))
        #light = wxgl.SunLight(direction=(0.2,-0.5,-1))
        tf = lambda t : ((1,0,0,(0.05*t)%360),)
        cf = lambda t : {'azim': (0.05*t)%360}

        sch = wxgl.Scheme()
        ########sch.cruise(cf)
        sch.surface(vs[indices], texture='res/earth.jpg', texcoord=texcoord, transform=None)
        
        return sch

    def draw_line(self):
        vs = np.array([
            [-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5],
            [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5], [0.5, -0.5, -0.5], [-0.5, -0.5, -0.5]
        ], dtype=np.float32)
        data = np.arange(8)

        sch = wxgl.Scheme()
        sch.line(vs, data=data, alpha=1, method='loop')
        sch.text('2D文字Hello', [0.5,0,0], size=64)
        
        return sch

    def draw_mesh(self):
        v, u = np.mgrid[-0.5*np.pi:0.5*np.pi:30j, 0:2*np.pi:60j]
        x = np.cos(v)*np.cos(u)
        y = np.cos(v)*np.sin(u)
        z = np.sin(v)

        light_y = wxgl.SunLight(direction=(0.2, -0.5, -1))
        light_z = wxgl.SunLight(direction=(0.2, 1, -0.5))
        cf = lambda t : {'azim': (0.05*t)%360}

        sch = wxgl.Scheme()
        sch.cruise(cf)
        sch.mesh(x, z, y, data=z, light=light_y, ccw=False, fill=False)

        return sch

if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()

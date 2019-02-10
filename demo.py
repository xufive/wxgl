# -*- coding: utf-8 -*-


import wx
import numpy as np
from OpenGL.GL import *
from OpenGL.arrays import vbo

from scene import *
from colormap import *

FONT_FILE = r"C:\Windows\Fonts\simfang.ttf"

class mainFrame(wx.Frame):
    """程序主窗口类，继承自wx.Frame"""

    def __init__(self):
        """构造函数"""

        wx.Frame.__init__(self, None, -1, u'WxGL项目演示', style=wx.DEFAULT_FRAME_STYLE)
        self.Maximize()
        
        self.layers = list()
        self.curr = 0
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        
        self.cm = ColorMap()
        
        # 操作区
        opp = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
        btn = wx.Button(opp, -1, u'切换投影模式', pos=(50, 100), size=(120, 25))
        self.Bind(wx.EVT_BUTTON, self.onChangeMode, btn)
        btn = wx.Button(opp, -1, u'启动分层显示', pos=(50, 150), size=(120, 25))
        self.Bind(wx.EVT_BUTTON, self.onAnimation, btn)
        
        # 准备数据
        rows, cols = 50, 50
        x, y = np.mgrid[-1:1:complex(0,cols),-1:1:complex(0,rows)]
        z = x*np.exp(-x**2-y**2)
        
        v = np.dstack((x,y,z)).reshape(rows*cols,3)
        c0 = self.cm.map(z, 'jet', mode='RGB')
        c1 = self.cm.map(z, 'hsv', mode='RGB')
        c2 = self.cm.map(z, 'winter', mode='RGB')
        c3 = self.cm.map(z, 'rainbow', mode='RGB')
        
        # 创建场景，并设置
        self.scene = GLScene(self)
        #self.scene.setHead('z+')
        #self.scene.setEye([10,0,0])
        self.scene.setEye([0,0,10])
        self.scene.setView([-1,1,-1,1,5,500])
        self.scene.setScale([1.5,1.5,1.5])
        
        sizer_max = wx.BoxSizer() 
        sizer_max.Add(opp, 2, wx.EXPAND|wx.ALL, 0) 
        sizer_max.Add(self.scene, 5, wx.EXPAND|wx.ALL, 0)
        
        self.SetAutoLayout(True) 
        self.SetSizer(sizer_max)
        self.Layout()
        
        # 创建master视区，并添加模型
        master = self.scene.addRegion('master', (0,0,0.85,1), FONT_FILE)
        
        self.layers.append(master.drawSurface(x, y, z-0.4, c0, mode=2))
        self.layers.append(master.drawSurface(x, y, z-0.2, c2, mode=1))
        self.layers.append(master.drawSurface(x, y, z, c1, mode=2))
        self.layers.append(master.drawSurface(x, y, z+0.2, c2, mode=4))
        self.layers.append(master.drawSurface(x, y, z+0.4, c0, mode=3))
        self.layers.append(master.drawSurface(x, y, z+0.6, c1, mode=2))
        self.layers.append(master.drawSurface(x, y, z+0.8, c3, mode=2))
        
        #master.drawText(u'温度35°C,adCDF汉字', [-0.5,1.0,0.0], 50, [1,0,0], FONT_FILE)
        master.plotAxes(k=1.5, half=True, xlabel='x轴', ylabel='y轴', zlabel='z轴')
        
        # 创建axes视区，并添加部件
        axes = self.scene.addRegion('axes', (0,0,0.2,0.2), FONT_FILE, scale=[0.8,0.8,0.8])
        #axes = self.scene.addRegion('axes', (0,0,0.2,0.2), FONT_FILE)
        axes.plotAxes(xlabel='x轴', ylabel='y轴', zlabel='z轴')
        
        # 创建cm视区，并添加模型
        cm = self.scene.addRegion('cm', (0.85,0,0.15,1), FONT_FILE, lookat=[0,0,5,0,0,0,0,1,0], scale=[1,1,1], mode='ortho')
        #cm = self.scene.addRegion('cm', (0.9,0,0.1,1), FONT_FILE, scale=[1,1,1], mode='ortho')
        '''
        x = np.array([[-0.9,-0.2],[-0.9,-0.2],[-0.9,-0.2],[-0.9,-0.2],[-0.9,-0.2],[-0.9,-0.2]])
        y = np.array([[5,5],[3,3],[1,1],[-1,-1],[-3,-3],[-5,-5]])
        z = np.array([[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]])
        c = np.array([[[1,0,0],[1,0,0]],[[0.79,1,0],[0.79,1,0]],[[0,1,0.22],[0,1,0.22]],[[0,0.28,1],[0,0.28,1]],[[0.75,0,1],[0.75,0,1]],[[1,0,1],[1,0,1]]])
        
        cm.drawSurface(x, y, z, c, method=0, mode=1)
        cm.drawText(u'温度', [-1.0,5.5,0.0], 42, [1,1,1])
        cm.drawText(u'-20°C', [-0.1,-5,0.0], 32, [1,1,1])
        cm.drawText(u'-10°C', [-0.1,-3,0.0], 32, [1,1,1])
        cm.drawText(u'0°C', [-0.1,-1,0.0], 32, [1,1,1])
        cm.drawText(u'10°C', [-0.1,1,0.0], 32, [1,1,1])
        cm.drawText(u'30°C', [-0.1,3,0.0], 32, [1,1,1])
        cm.drawText(u'50°C', [-0.1,5,0.0], 32, [1,1,1])
        '''
        
        cb_value = [-20,-10,0,10,30,50]
        cb_color = [[0.75,0,1],[0,0.28,1],[0,1,0.22],[0.79,1,0],[1,0,0]]
        #cb_color = [[1,0,1],[0.75,0,1],[0,0.28,1],[0,1,0.22],[0.79,1,0],[1,0,0]]
        cm.plotColorBar(cb_value, cb_color, 'right', title=u'温度', title_offset=(-0.25,0.2), label_offset=(0.2,-0.05))
        # ----------------------------------------------------
        
        
    def onChangeMode(self, evt):
        
        if self.scene.getMode() == 'ortho':
            mode = 'cone'
        else:
            mode = 'ortho'
        
        self.scene.setMode(mode)
        
    def onAnimation(self, evt):
        
        obj = evt.GetEventObject()
        if obj.GetLabel() == u'启动分层显示':
            self.timer.Start(200)
            obj.SetLabel(u'停止分层显示')
        else:
            self.timer.Stop()
            obj.SetLabel(u'启动分层显示')
        
    def onTimer(self, evt):
        
        self.scene.regions['master'].clearCmd()
        layer = self.layers[self.curr]
        self.curr += 1
        self.curr %= (len(self.layers))
        
        self.scene.regions['master'].setPolygonMode(layer[4])
        self.scene.regions['master'].drawElements(layer[0], layer[1], layer[2], layer[3])
        self.scene.Refresh(False)


if __name__ == "__main__":
    """测试代码"""
    
    app = wx.App()
    frame = mainFrame()
    frame.Show(True)
    app.MainLoop()
    
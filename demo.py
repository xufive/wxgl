# -*- coding: utf-8 -*-


import wx
import time
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
        
        self.models = dict()            # 所有模型
        self.selected = list()          # 选中显示的模型
        self.curr = 0                   # 动画显示时当前显示的模型索引
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        
        self.cm = ColorMap()
        
        # 操作区
        opp = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
        btn = wx.Button(opp, -1, u'切换投影模式', pos=(50, 100), size=(120, 25))
        self.Bind(wx.EVT_BUTTON, self.onChangeMode, btn)
        btn = wx.Button(opp, -1, u'启动分层显示', pos=(50, 150), size=(120, 25))
        self.Bind(wx.EVT_BUTTON, self.onAnimation, btn)
        btn = wx.Button(opp, -1, u'截屏', pos=(50, 200), size=(120, 25))
        self.Bind(wx.EVT_BUTTON, self.onCapture, btn)
        
        cb1 = wx.CheckBox(opp, -1, 'Layer1', pos=(50, 260), size=(120, -1)) 
        cb2 = wx.CheckBox(opp, -1, 'Layer2', pos=(50, 300), size=(120, -1)) 
        cb3 = wx.CheckBox(opp, -1, 'Layer3', pos=(50, 340), size=(120, -1)) 
        cb4 = wx.CheckBox(opp, -1, 'Layer4', pos=(50, 380), size=(120, -1)) 
        cb5 = wx.CheckBox(opp, -1, 'Layer5', pos=(50, 420), size=(120, -1)) 
        cb6 = wx.CheckBox(opp, -1, 'Layer6', pos=(50, 460), size=(120, -1)) 
        cb7 = wx.CheckBox(opp, -1, 'Layer7', pos=(50, 500), size=(120, -1))
        self.Bind(wx.EVT_CHECKBOX, self.onCheckBox) 
        
        btn = wx.Button(opp, -1, u'删除模型Layer7', pos=(50, 550), size=(120, 25))
        self.Bind(wx.EVT_BUTTON, self.onDeleteModel, btn)
        
        # 创建场景，并设置
        self.scene = GLScene(self)
        self.scene.setHead('z+')
        self.scene.setEye([3,-8,4])
        #self.scene.setAim([0.5,0,0])
        #self.scene.setEye([0,0,10])
        self.scene.setView([-1,1,-1,1,5,500])
        self.scene.setScale([1.2,1.2,1.2])
        
        sizer_max = wx.BoxSizer() 
        sizer_max.Add(opp, 2, wx.EXPAND|wx.ALL, 0) 
        sizer_max.Add(self.scene, 5, wx.EXPAND|wx.ALL, 0)
        
        self.SetAutoLayout(True) 
        self.SetSizer(sizer_max)
        self.Layout()
        
        # 准备数据
        rows, cols = 50, 50
        x, y = np.mgrid[-1:1:complex(0,cols),-1:1:complex(0,rows)]
        z = x*np.exp(-x**2-y**2)
        
        v = np.dstack((x,y,z)).reshape(rows*cols,3)
        c0 = self.cm.map(z, 'jet', mode='RGB')
        c1 = self.cm.map(z, 'hsv', mode='RGB')
        c2 = self.cm.map(z, 'winter', mode='RGB')
        c3 = self.cm.map(z, 'rainbow', mode='RGB')
        
        # 创建master视区，并添加模型
        master = self.scene.addRegion('master', (0,0,0.85,1), FONT_FILE)
        
        # 管理模式
        master.addSurface('Layer1', x, y, z-0.4, c0, mode=2, display=2)
        master.addSurface('Layer2', x, y, z-0.2, c2, mode=1, display=0)
        master.addSurface('Layer3', x, y, z, c1, mode=2, display=0)
        master.addSurface('Layer4', x, y, z+0.2, c2, mode=4, display=0)
        master.addSurface('Layer5', x, y, z+0.4, c0, mode=3, display=0)
        master.addSurface('Layer6', x, y, z+0.6, c1, mode=2, display=0)
        master.addSurface('Layer7', x, y, z+0.8, c3, mode=2, display=0)
        
        v = np.array([[-1,0,0],[1,0,0],[0,-1,0],[0,1,0],[0,0,-1],[0,0,1]])
        c = np.array([[1,0,0],[1,0,0],[0,1,0],[0,1,0],[0,0,1],[0,0,1]])
        master.addLine('Axes', v, c, method=0, display=2)
        
        master.addText('X', 'X', [1,0,0], 40, [1,0,0], display=2)
        master.addText('Y', 'Y', [0,1,0], 40, [0,1,0], display=2)
        master.addText('Z', 'Z', [0,0,1], 40, [0,0,1], display=2)
        
        master.update()
        
        '''
        # 即时模式
        master.drawSurface(x, y, z-0.4, c0, mode=2)
        master.drawSurface(x, y, z-0.2, c2, mode=1)
        master.drawSurface(x, y, z, c1, mode=2)
        master.drawSurface(x, y, z+0.2, c2, mode=4)
        master.drawSurface(x, y, z+0.4, c0, mode=3)
        master.drawSurface(x, y, z+0.6, c1, mode=2)
        master.drawSurface(x, y, z+0.8, c3, mode=2)
        '''
        master.plotAxes(k=1.5, half=True, xlabel='x轴', ylabel='y轴', zlabel='z轴')
        
        # 创建axes视区，并添加部件
        axes = self.scene.addRegion('axes', (0,0,0.1,0.1), FONT_FILE, scale=[1.2,1.2,1.2])
        #axes = self.scene.addRegion('axes', (0,0,0.2,0.2), FONT_FILE)
        axes.plotAxes(xlabel='x轴', ylabel='y轴', zlabel='z轴', size=32)
        
        # 创建cm视区，并添加模型
        cm = self.scene.addRegion('cm', (0.85,0,0.15,1), FONT_FILE, lookat=[0,0,5,0,0,0,0,1,0], scale=[1,1,1], mode='ortho')
        #cm = self.scene.addRegion('cm', (0.9,0,0.1,1), FONT_FILE, scale=[1,1,1], mode='ortho')
        
        cb_value = [-20,-10,0,10,30,50]
        #cb_color = [[0.75,0,1],[0,0.28,1],[0,1,0.22],[0.79,1,0],[1,0,0]]
        cb_color = [[1,0,1],[0.75,0,1],[0,0.28,1],[0,1,0.22],[0.79,1,0],[1,0,0]]
        cm.plotColorBar(cb_value, cb_color, 'right', title=u'温度', title_offset=(-0.25,0.2), label_offset=(0.2,-0.05))
        
    def onChangeMode(self, evt):
        
        if self.scene.getMode() == 'ortho':
            mode = 'cone'
        else:
            mode = 'ortho'
        
        self.scene.setMode(mode)
        
    def onAnimation(self, evt):
        
        obj = evt.GetEventObject()
        if obj.GetLabel() == u'启动分层显示':
            self.scene.regions['master'].startAnimation(reverse=True)
            self.timer.Start(200)
            obj.SetLabel(u'停止分层显示')
        else:
            self.timer.Stop()
            obj.SetLabel(u'启动分层显示')
            self.scene.regions['master'].stopAnimation()
            self.scene.regions['master'].update()
        
    def onCapture(self, evt):
        
        fn = 'capture/%d.png'%int(time.time()*1000)
        self.scene.screenshot(fn, alpha=True) 
        
    def onDeleteModel(self, evt):
        
        self.scene.regions['master'].deleteModel('Layer7')
        self.scene.regions['master'].update()
        
    def onTimer(self, evt):
        
        if self.scene.regions['master'].animation:
            animation = self.scene.regions['master'].animation[0]
        else:
            animation = None
        
        if animation:
            i = self.scene.regions['master'].shown_models.index(animation)
            i += 1
            i %= len(self.scene.regions['master'].shown_models)
            self.scene.regions['master'].animation = [self.scene.regions['master'].shown_models[i]]
        else:
            self.scene.regions['master'].animation = [self.scene.regions['master'].shown_models[0]]
            
        self.scene.regions['master'].update()
        
    def onCheckBox(self, evt):
        
        obj = evt.GetEventObject()
        key = obj.GetLabel()
        
        if obj.IsChecked():
            self.scene.regions['master'].showModel(key)
        else:
            self.scene.regions['master'].hideModel(key)
        
        self.scene.regions['master'].update()


if __name__ == "__main__":
    """测试代码"""
    
    app = wx.App()
    frame = mainFrame()
    frame.Show(True)
    app.MainLoop()
    
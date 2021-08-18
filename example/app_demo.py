# -*- coding: utf-8 -*-

import time
import threading
import wx
import wx.lib.buttons as wxbtn
import numpy as np

from wxgl.scene import *

class mainFrame(wx.Frame):
    """程序主窗口类"""
    
    def __init__(self):
        """构造函数"""
        
        wx.Frame.__init__(self, None, -1, 'WxGL App Demo', style=wx.DEFAULT_FRAME_STYLE)
        self.SetBackgroundColour(wx.Colour(240,240,240))
        self.SetSize((1200, 800))
        self.Center()
        
        icon = wx.Icon('res/wxplot.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        
        # 创建场景，并设置视区
        # -----------------------------------------------------------
        self.scene = WxGLScene(self, elevation=10, azimuth=30)
        #self.cm = self.scene.cm
        #self.cm_list = list(self.cm.cms.keys())     # 系统支持的调色板列表
        #self.cm_curr = 'hsv'                        # 当前选中的调色板
        #self.render = 'FCBC'                        # 渲染方式
        #self.cm_is_show = False                     # ColorBar显示开关
        self.model_curr = '球和六面体'              # 当前选中的模型。默认正弦波
        
        # 创建master视区
        self.master = self.scene.add_region((0, 0, 0.85, 1))
        
        # 创建colorbar视区
        self.cbar = self.scene.add_region((0.85, 0, 0.15, 1), fixed=True)
        
        # 创建坐标轴视区
        self.xyz = self.scene.add_region((0,0,0.15,0.15))
        self.xyz.coordinate(name='xyz')
        
        # 模型选择区
        rb_mold_0 = wx.RadioButton(self, id=-1, size=(120,-1), label='球和六面体', style=wx.RB_GROUP)
        rb_mold_1 = wx.RadioButton(self, id=-1, size=(120,-1), label='圆管曲线')
        rb_mold_2 = wx.RadioButton(self, id=-1, size=(120,-1), label='曲面')
        rb_mold_3 = wx.RadioButton(self, id=-1, size=(120,-1), label='地球')
        rb_mold_0.SetValue(True)
        
        sizer_rb_mold = wx.GridBagSizer(10, 40)
        sizer_rb_mold.Add(rb_mold_0, (0, 0), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_mold.Add(rb_mold_1, (0, 1), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_mold.Add(rb_mold_2, (1, 0), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_mold.Add(rb_mold_3, (1, 1), (1, 1), flag=wx.ALL, border=0)
        
        sizer_mold = wx.StaticBoxSizer(wx.StaticBox(self, -1, '模型'), wx.VERTICAL)
        sizer_mold.Add(sizer_rb_mold, 0, wx.ALIGN_CENTER|wx.ALL, 15)
        
        # 调色板和ColorBar设置
        self.ch_cm = wx.Choice(self, id=-1, choices=self.cm_list)
        self.ch_cm.SetStringSelection(self.cm_curr)
        
        self.cb_cm = wx.CheckBox(self, id=-1, label='显示ColorBar')
        self.cb_cm.SetValue(self.cm_is_show)
        
        sizer_cm = wx.BoxSizer()
        sizer_cm.Add(self.ch_cm, 1, wx.EXPAND|wx.LEFT, 20)
        sizer_cm.Add(self.cb_cm, 1, wx.EXPAND|wx.LEFT, 20)
        
        sizer_cm_box = wx.StaticBoxSizer(wx.StaticBox(self, -1, "调色板和ColorBar"), wx.VERTICAL)
        sizer_cm_box.Add(sizer_cm, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 15)
        
        # 渲染方式选择区
        self.rb_render_0 = wx.RadioButton(self, id=-1, size=(110,-1), label='前后面填充颜色', style=wx.RB_GROUP)
        self.rb_render_1 = wx.RadioButton(self, id=-1, size=(110,-1), label='前后面显示线条')
        self.rb_render_2 = wx.RadioButton(self, id=-1, size=(130,-1), label='前面颜色后面线条')
        self.rb_render_3 = wx.RadioButton(self, id=-1, size=(130,-1), label='前面线条后面颜色')
        self.rb_render_0.SetValue(True)
        
        sizer_rb_render = wx.GridBagSizer(10, 40)
        sizer_rb_render.Add(self.rb_render_0, (0, 0), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_render.Add(self.rb_render_2, (0, 1), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_render.Add(self.rb_render_1, (1, 0), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_render.Add(self.rb_render_3, (1, 1), (1, 1), flag=wx.ALL, border=0)
        
        sizer_show = wx.StaticBoxSizer(wx.StaticBox(self, -1, '渲染方式'), wx.VERTICAL)
        sizer_show.Add(sizer_rb_render, 0, wx.ALIGN_CENTER|wx.ALL, 15)
        
        # 按钮区
        sizer_btn = wx.GridBagSizer(10, 40)
        btns = [
            [('显示/隐藏坐标系', 'xyz', (246, 225, 208)), ('显示/隐藏网格', 'grid', (246, 225, 208))],
            [('水平顺时针旋转', 'rh+', (217, 228, 241)), ('水平逆时针旋转', 'rh-', (217, 228, 241))],
            [('向前连续翻转', 'rv+', (217, 228, 241)), ('向后连续翻转', 'rv-', (217, 228, 241))],
            [('恢复初始状态', 'reset', (246, 225, 208)), ('屏幕截图', 'capture', (245, 227, 129))]
        ]
        
        for i in range(len(btns)):
            for j in range(len(btns[i])):
                label, name, bg = btns[i][j]
                btn = wxbtn.GenButton(self, -1, label, size=(140, 30), name=name)
                btn.SetBezelWidth(2)
                btn.SetBackgroundColour(wx.Colour(*bg))
                btn.Bind(wx.EVT_BUTTON, self.OnButton)
                sizer_btn.Add(btn, (i, j), (1, 1), flag=wx.ALL, border=0)
        
        # 组装
        sizer_left = wx.BoxSizer(wx.VERTICAL)
        sizer_left.Add(sizer_mold, 0, wx.EXPAND|wx.ALL, 10)
        sizer_left.Add(sizer_cm_box, 0, wx.EXPAND|wx.ALL, 10)
        sizer_left.Add(sizer_show, 0, wx.EXPAND|wx.ALL, 10)
        sizer_left.Add(sizer_btn, 0, wx.ALIGN_CENTER|wx.ALL, 15)
        
        sizer_max = wx.BoxSizer() 
        sizer_max.Add(sizer_left, 0, wx.EXPAND|wx.ALL, 10) 
        sizer_max.Add(self.scene, 1, wx.EXPAND|wx.ALL, 0)
        
        self.SetAutoLayout(True) 
        self.SetSizer(sizer_max)
        self.Layout()
        
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButton)
        self.Bind(wx.EVT_CHOICE, self.OnChoice)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)
        
        self.waiting = None
        self.draw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.draw_timer)
        
        self.DrawScene()
        
    def OnTimer(self, evt):
        """定时器事件函数"""
        
        if self.waiting:
            self.waiting.Pulse()
        
    def OnButton(self, evt):
        """响应按钮事件"""
        
        name = evt.GetEventObject().GetName()
        if name == 'xyz':
            self.xyz.set_model_visible('xyz', not self.xyz.get_model_visible('xyz'))
            self.xyz.refresh()
        elif name == 'grid':
            if self.master.grid_tick:
                self.master.hide_ticks()
            else:
                self.master.ticks(**self.master.grid_tick_kwds)
        elif name == 'rh+':
            self.scene.auto_rotate(rotation='h+')
        elif name == 'rh-':
            self.scene.auto_rotate(rotation='h-')
        elif name == 'rv+':
            self.scene.auto_rotate(rotation='v+')
        elif name == 'rv-':
            self.scene.auto_rotate(rotation='v-')
        elif name == 'reset':
            self.scene.reset_posture()
        elif name == 'capture':
            fn = 'res/%s.png'%time.strftime('%Y%m%d-%H%M%S')
            self.scene.save_scene(fn, alpha=False)
            wx.MessageBox('已保存至res文件夹内', '操作提示', wx.OK | wx.ICON_INFORMATION)
        
    def OnRadioButton(self, evt):
        """响应RadioData事件"""
        
        label = evt.GetEventObject().GetLabel()
        if label in ['球和六面体', '圆管曲线', '曲面', '地球']:
            self.model_curr = label
        elif label == '前后面填充颜色':
            self.render = 'FCBC'
        elif label == '前后面显示线条':
            self.render = 'FLBL'
        elif label == '前面颜色后面线条':
            self.render = 'FCBL'
        elif label == '前面线条后面颜色':
            self.render = 'FLBC'
        
        self.ClearScene() # 清空场景
        self.DrawScene() # 重绘场景
        
    def OnChoice(self, evt):
        """选择调色板"""
        
        self.cm_curr = evt.GetString()
        self.ClearScene() # 清空场景
        self.DrawScene() # 重绘场景
        
    def OnCheckBox(self, evt):
        """响应CheckBox事件"""
        
        obj = evt.GetEventObject()
        label = obj.GetLabel()
        if label == '显示ColorBar':
            self.cm_is_show = obj.IsChecked()
            self.ClearScene() # 清空场景
            self.DrawScene() # 重绘场景
        
    def ClearScene(self):
        """清空场景"""
        
        self.xyz.delete_model('xyz')
        self.cbar.delete_model('cb')
        for model_name in list(self.master.models.keys()):
            self.master.delete_model(model_name)
        
        self.xyz.refresh()
        self.cbar.refresh()
        self.master.refresh()
        
    def DrawScene(self):
        """重绘场景"""
        
        if self.model_curr == '地球':
            thread_task = threading.Thread(target=self._DrawScene)
            thread_task.setDaemon(True)
            thread_task.start()
            
            self.waiting = wx.ProgressDialog('请稍候...', '', 1000, parent=self.scene, style=wx.PD_ELAPSED_TIME)
            self.draw_timer.Start(100)
        else:
            self._DrawScene()
        
    def _DrawScene(self):
        """重绘场景的线程函数"""
        
        if self.model_curr == '球和六面体':
            # 重置视区尺寸
            self.master.reset_box((0, 0, 1, 1), clear=True)
            
            # 绘制模型
            self.master.sphere((0,0,0), 1, 'cyan', mode=self.render)
            self.master.cube((0,0,0), 1.6, 'green', mode=self.render)
            self.xyz.coordinate(name='xyz', length=1.5)
            
            # 控件可用性设置
            self.cb_cm.Enable(False)
            self.ch_cm.Enable(False)
            self.rb_render_0.Enable(True)
            self.rb_render_1.Enable(True)
            self.rb_render_2.Enable(True)
            self.rb_render_3.Enable(True)
        elif self.model_curr == '圆管曲线':
            # 生成数据，绘制模型
            y = np.linspace(0, 2*np.pi, 200)
            z = np.sin(y)
            x = np.zeros(200)
            vs = np.stack((x, y, z), axis=1)
            color = self.cm.cmap(y, self.cm_curr)
            
            # 重置视区尺寸
            if self.cm_is_show:
                self.master.reset_box((0, 0, 0.85, 1), clear=True)
            else:
                self.master.reset_box((0, 0, 1, 1), clear=True)
            
            # 绘制模型
            self.master.pipe(vs, 0.3, color)
            self.xyz.coordinate(name='xyz', length=1.5)
            if self.cm_is_show:
                self.cbar.colorbar((z.min(), z.max()), self.cm_curr, name='cb')
            
            # 控件可用性设置
            self.cb_cm.Enable(True)
            self.ch_cm.Enable(True)
            self.rb_render_0.Enable(True)
            self.rb_render_1.Enable(True)
            self.rb_render_2.Enable(True)
            self.rb_render_3.Enable(True)
        elif self.model_curr == '曲面':
            # 生成数据，绘制模型
            x, y = np.mgrid[-2:2:50j,-2:2:50j]
            z = 2*x*np.exp(-x**2-y**2)
            c = self.cm.cmap(z, self.cm_curr)
            
            # 重置视区尺寸
            if self.cm_is_show:
                self.master.reset_box((0, 0, 0.85, 1), clear=True)
            else:
                self.master.reset_box((0, 0, 1, 1), clear=True)
            
            # 绘制模型
            self.master.mesh(x, y, z, c, mode=self.render)
            self.xyz.coordinate(name='xyz', length=1.5)
            if self.cm_is_show:
                self.cbar.colorbar((z.min(), z.max()), self.cm_curr, name='cb')
            
            # 控件可用性设置
            self.cb_cm.Enable(True)
            self.ch_cm.Enable(True)
            self.rb_render_0.Enable(True)
            self.rb_render_1.Enable(True)
            self.rb_render_2.Enable(True)
            self.rb_render_3.Enable(True)
        elif self.model_curr == '地球':
            # 从等经纬地图上读取经纬度网格上的每一个格点的颜色
            c = np.array(Image.open('res/earth.png'))/255
            
            # 生成和等经纬地图分辨率一致的经纬度网格，计算经纬度网格上的每一个格点的空间坐标(x,y,z)
            lats, lons = np.mgrid[np.pi/2:-np.pi/2:complex(0,c.shape[0]), 0:2*np.pi:complex(0,c.shape[1])]
            x = np.cos(lats)*np.cos(lons)
            y = np.cos(lats)*np.sin(lons)
            z = np.sin(lats)
            
            # 重置视区尺寸
            self.master.reset_box((0, 0, 1, 1), clear=True)
            
            self.master.mesh(x, y, z, c)
            self.xyz.coordinate(name='xyz', length=1.5)
            
            # 控件可用性设置
            self.cb_cm.Enable(False)
            self.ch_cm.Enable(False)
            self.rb_render_0.Enable(False)
            self.rb_render_1.Enable(False)
            self.rb_render_2.Enable(False)
            self.rb_render_3.Enable(False)
        
            self.draw_timer.Stop()
            if self.waiting:
                self.waiting.Destroy()
                self.waiting = None
            
class mainApp(wx.App):
    def OnInit(self):
        self.Frame = mainFrame()
        self.Frame.Show()
        return True

if __name__ == "__main__":
    app = mainApp()
    app.MainLoop()
    
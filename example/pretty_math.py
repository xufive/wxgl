# -*- coding: utf-8 -*-

import time
import wx
import wx.lib.buttons as wxbtn
import numpy as np
from wxgl.scene import *
from wxgl.colormap import WxGLColorMap

class mainFrame(wx.Frame):
    """程序主窗口类"""
    
    def __init__(self):
        """构造函数"""
        
        wx.Frame.__init__(self, None, -1, 'WxGL Demo', style=wx.DEFAULT_FRAME_STYLE)
        self.SetBackgroundColour(wx.Colour(240,240,240))
        self.Maximize()
        
        icon = wx.Icon('res/wxgl.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        
        self.cm = WxGLColorMap()                    # 创建调色板对象
        self.cm_list = list(self.cm.getColorMaps()) # 系统支持的调色板列表
        self.cm_is_show = True                      # ColorBar显示开关
        self.cm_curr = 'rainbow'                    # 当前选中的调色板。默认为rainbow
        self.model_curr = '正弦波'                  # 当前选中的模型。默认正弦波
        self.render = 'FLBC'                        # 渲染方式。默认前面显示线条后面填充颜色
        
        # 创建场景，并设置
        self.scene = WxGLScene(self, r'C:\Windows\Fonts\simfang.ttf', bg=[0,0,0,0])
        
        # 创建master视区
        self.master = self.scene.addRegion((0, 0, 0.85, 1))
        
        # 创建colorbar视区
        self.cbar = self.scene.addRegion(
            (0.85, 0, 0.15, 1), 
            lookat = [0, 0, 5, 0, 0, 0, 0, 1, 0], 
            scale = [1,1,1], 
            view = [-1,1,-5,5,3.5,10], 
            projection = 'ortho'
        )
        
        # 创建axes视区
        self.axes = self.scene.addRegion((0, 0, 0.15, 0.15), scale=[1.2, 1.2, 1.2])
        
        # 信息显示区
        info_p = wx.Panel(self, -1, size=(350,240), style=wx.BORDER_SUNKEN)
        info_p.SetBackgroundColour(wx.Colour(192,255,255))
        
        text = wx.StaticText(info_p, -1, '投影方式：', pos=(0,10), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, '视景体：', pos=(0,30), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, '模型缩放：', pos=(0,50), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, '视口缩放：', pos=(0,70), size=(90,-1), style=wx.ALIGN_RIGHT)
        
        text = wx.StaticText(info_p, -1, '相机位置：', pos=(0,100), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, '焦点位置：', pos=(0,120), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, '头部指向：', pos=(0,140), size=(90,-1), style=wx.ALIGN_RIGHT)
        
        text = wx.StaticText(info_p, -1, '仰角：', pos=(0,170), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, '方位角：', pos=(0,190), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, '距离：', pos=(0,210), size=(90,-1), style=wx.ALIGN_RIGHT)
        
        proj = '透视投影' if self.scene.projection == 'cone' else '平行投影'
        view = '[%.2f, %.2f, %.2f, %.2f, %.2f, %.2f]'%(*list(self.scene.view),)
        scale = '[%.2f, %.2f, %.2f]'%(*list(self.scene.scale),)
        zoom = '%.2f'%(1/self.scene.zoom)
        self.st_mode = wx.StaticText(info_p, -1, proj, pos=(90,10), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_view = wx.StaticText(info_p, -1, view, pos=(90,30), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_scale = wx.StaticText(info_p, -1, scale, pos=(90,50), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_zoom = wx.StaticText(info_p, -1, zoom, pos=(90,70), size=(230,-1), style=wx.ALIGN_LEFT)
        
        cam = '[%.2f, %.2f, %.2f]'%(*list(self.scene.cam),)
        aim = '[%.2f, %.2f, %.2f]'%(*list(self.scene.aim),)
        self.st_cam = wx.StaticText(info_p, -1, cam, pos=(90,100), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_aim = wx.StaticText(info_p, -1, aim, pos=(90,120), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_head = wx.StaticText(info_p, -1, self.scene.head, pos=(90,140), size=(230,-1), style=wx.ALIGN_LEFT)
        
        elevation, azimuth, dist = np.degrees(self.scene.elevation), np.degrees(self.scene.azimuth), np.degrees(self.scene.dist)
        self.st_elevation = wx.StaticText(info_p, -1, '%.2f°'%elevation, pos=(90,170), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_azimuth = wx.StaticText(info_p, -1, '%.2f°'%azimuth, pos=(90,190), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_dist = wx.StaticText(info_p, -1, '%.2f'%dist, pos=(90,210), size=(230,-1), style=wx.ALIGN_LEFT)
        
        # 按钮区
        sizer_btn = wx.GridBagSizer(10, 40)
        btns = [
            [('切换投影模式', 'proj', (246, 225, 208)), ('设置视景体', 'view', (246, 225, 208))],
            [('设置模型缩放', 'scale', (217, 228, 241)), ('设置视口缩放', 'zoom', (217, 228, 241))],
            [('设置相机位置', 'cam', (217, 228, 241)), ('设置焦点位置', 'aim', (217, 228, 241))],
            [('设置头部指向', 'head', (217, 228, 241)), ('设置相机姿态', 'posture', (217, 228, 241))],
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
        
        # 模型选择区
        rb_mold_0 = wx.RadioButton(self, id=-1, size=(120,-1), label='正弦波', style=wx.RB_GROUP)
        rb_mold_1 = wx.RadioButton(self, id=-1, size=(120,-1), label='球和六面体')
        rb_mold_2 = wx.RadioButton(self, id=-1, size=(120,-1), label='曲面A')
        rb_mold_3 = wx.RadioButton(self, id=-1, size=(120,-1), label='曲面B')
        rb_mold_4 = wx.RadioButton(self, id=-1, size=(120,-1), label='曲面C')
        rb_mold_5 = wx.RadioButton(self, id=-1, size=(120,-1), label='体数据绘制')
        rb_mold_6 = wx.RadioButton(self, id=-1, size=(120,-1), label='地球')
        rb_mold_7 = wx.RadioButton(self, id=-1, size=(120,-1), label='三维重建')
        rb_mold_0.SetValue(True)
        
        self.cb_axes = wx.CheckBox(self, id=-1, label='显示坐标轴')
        self.cb_axes.SetValue(True)
        
        sizer_rb_mold = wx.GridBagSizer(10, 40)
        sizer_rb_mold.Add(rb_mold_0, (0, 0), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_mold.Add(rb_mold_1, (0, 1), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_mold.Add(rb_mold_2, (1, 0), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_mold.Add(rb_mold_3, (1, 1), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_mold.Add(rb_mold_4, (2, 0), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_mold.Add(rb_mold_5, (2, 1), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_mold.Add(rb_mold_6, (3, 0), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_mold.Add(rb_mold_7, (3, 1), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_mold.Add(self.cb_axes, (4, 0), (0, 0), flag=wx.TOP, border=5)
        
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
        self.rb_render_3.SetValue(True)
        
        sizer_rb_render = wx.GridBagSizer(10, 40)
        sizer_rb_render.Add(self.rb_render_0, (0, 0), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_render.Add(self.rb_render_2, (0, 1), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_render.Add(self.rb_render_1, (1, 0), (1, 1), flag=wx.ALL, border=0)
        sizer_rb_render.Add(self.rb_render_3, (1, 1), (1, 1), flag=wx.ALL, border=0)
        
        sizer_show = wx.StaticBoxSizer(wx.StaticBox(self, -1, '渲染方式'), wx.VERTICAL)
        sizer_show.Add(sizer_rb_render, 0, wx.ALIGN_CENTER|wx.ALL, 15)
        
        # 分割线
        line_p = wx.Panel(self, -1, size=(350,1))
        line_p.SetBackgroundColour(wx.Colour(192,192,192))
        
        # 组装
        sizer_left = wx.BoxSizer(wx.VERTICAL)
        sizer_left.Add(info_p, 0, wx.EXPAND|wx.BOTTOM, 5)
        sizer_left.Add(sizer_btn, 0, wx.ALIGN_CENTER|wx.ALL, 15)
        sizer_left.Add(line_p, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 10)
        sizer_left.Add(sizer_mold, 0, wx.EXPAND|wx.ALL, 10)
        sizer_left.Add(sizer_cm_box, 0, wx.EXPAND|wx.ALL, 10)
        sizer_left.Add(sizer_show, 0, wx.EXPAND|wx.ALL, 10)
        
        sizer_max = wx.BoxSizer() 
        sizer_max.Add(sizer_left, 0, wx.EXPAND|wx.ALL, 10) 
        sizer_max.Add(self.scene, 1, wx.EXPAND|wx.ALL, 0)
        
        self.SetAutoLayout(True) 
        self.SetSizer(sizer_max)
        self.Layout()
        
        self.scene.Bind(wx.EVT_MOTION, self.OnUpdatePostureInfo)
        self.scene.Bind(wx.EVT_MOUSEWHEEL, self.OnUpdateViewPortInfo)
        
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButton)
        self.Bind(wx.EVT_CHOICE, self.OnChoice)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)
        
        self.DrawScene()
        
    def OnRadioButton(self, evt):
        """响应RadioData事件"""
        
        label = evt.GetEventObject().GetLabel()
        if label in ['正弦波', '球和六面体', '曲面A', '曲面B', '曲面C', '体数据绘制', '地球', '三维重建']:
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
        elif label == '显示坐标轴':
            if obj.IsChecked():
                self.axes.showModel('xyz')
            else:
                self.axes.hideModel('xyz')
            self.axes.update()
        
    def OnButton(self, evt):
        """响应按钮事件"""
        
        name = evt.GetEventObject().GetName()
        if name == 'proj':
            if self.scene.projection == 'cone':
                projection = 'ortho'
                self.st_mode.SetLabel('平行投影')
            else:
                projection = 'cone'
                self.st_mode.SetLabel('透视投影')
            self.scene.setProjection(projection)
        elif name == 'head':
            dlg = wx.TextEntryDialog(self, '请输入头部指向（z+|y+|x+）：', u'设置头部指向')
            dlg.SetValue(self.scene.head)
            if dlg.ShowModal() == wx.ID_OK:
                self.scene.setCamera(head=dlg.GetValue().strip())
            dlg.Destroy()
            self.UpdateAllInfo()
        elif name == 'scale':
            dlg = wx.TextEntryDialog(self, '请输入模型缩放比例（3个参数，以半角逗号分隔）：', u'设置模型缩放比例')
            dlg.SetValue('%.2f, %.2f, %.2f'%(*list(self.scene.scale),))
            if dlg.ShowModal() == wx.ID_OK:
                self.scene.setScale([float(item.strip()) for item in dlg.GetValue().split(',')])
            dlg.Destroy()
            self.UpdateAllInfo()
        elif name == 'zoom':
            dlg = wx.TextEntryDialog(self, '请输入视口缩放比例：', u'设置视口缩放比例')
            dlg.SetValue('%.2f'%(1/self.scene.zoom))
            if dlg.ShowModal() == wx.ID_OK:
                self.scene.setZoom(1/float(dlg.GetValue().strip()))
            dlg.Destroy()
            self.UpdateAllInfo()
        elif name == 'cam':
            dlg = wx.TextEntryDialog(self, '请输入相机位置（3个参数，以半角逗号分隔）：', u'设置相机')
            dlg.SetValue('%.2f, %.2f, %.2f'%(*list(self.scene.cam),))
            if dlg.ShowModal() == wx.ID_OK:
                self.scene.setCamera(cam=[float(item.strip()) for item in dlg.GetValue().split(',')])
            dlg.Destroy()
            self.UpdateAllInfo()
        elif name == 'aim':
            dlg = wx.TextEntryDialog(self, '请输入焦点位置（3个参数，以半角逗号分隔）：', u'设置焦点位置')
            dlg.SetValue('%.2f, %.2f, %.2f'%(*list(self.scene.aim),))
            if dlg.ShowModal() == wx.ID_OK:
                self.scene.setCamera(aim=[float(item.strip()) for item in dlg.GetValue().split(',')])
            dlg.Destroy()
            self.UpdateAllInfo()
        elif name == 'posture':
            dlg = wx.TextEntryDialog(self, '请输入依次输入仰角、方位角和距离，以半角逗号分隔：', u'设置相机姿态')
            pos = self.scene.getCamera()
            dlg.SetValue('%.2f°, %.2f°, %.2f°'%(pos['elevation'], pos['azimuth'], pos['dist']))
            if dlg.ShowModal() == wx.ID_OK:
                elevation, azimuth, dist = [item.strip()[:-1] for item in dlg.GetValue().split(',')]
                elevation = float(elevation) if elevation else None
                azimuth = float(azimuth) if azimuth else None
                dist = float(dist) if dist else None
                self.scene.setPosture(elevation=elevation, azimuth=azimuth, dist=dist,)
            dlg.Destroy()
            self.UpdateAllInfo()
        elif name == 'view':
            dlg = wx.TextEntryDialog(self, '请输入视景体6个参数，以半角逗号分隔：', u'设置视景体')
            dlg.SetValue('%.2f, %.2f, %.2f, %.2f, %.2f, %.2f'%(*list(self.scene.view),))
            if dlg.ShowModal() == wx.ID_OK:
                self.scene.setView([float(item.strip()) for item in dlg.GetValue().split(',')])
            dlg.Destroy()
            self.UpdateAllInfo()
        elif name == 'reset':
            self.scene.restorePosture()
            self.UpdateAllInfo()
        elif name == 'capture':
            fn = 'res/%d.png'%int(time.time()*1000)
            self.scene.screenshot(fn, alpha=False)
        
    def OnUpdatePostureInfo(self, evt):
        """响应鼠标拖拽事件"""
        
        if evt.Dragging() and evt.LeftIsDown():
            pos = self.scene.getCamera()
            self.st_elevation.SetLabel('%.2f°'%pos['elevation'])
            self.st_azimuth.SetLabel('%.2f°'%pos['azimuth'])
            self.st_dist.SetLabel('%.2f'%pos['dist'])
            self.st_cam.SetLabel('[%.2f, %.2f, %.2f]'%(*pos['cam'],))
            self.st_aim.SetLabel('[%.2f, %.2f, %.2f]'%(*pos['aim'],))
        evt.Skip()
        
    def OnUpdateViewPortInfo(self, evt):
        """响应鼠标滚轮事件"""
        
        self.st_zoom.SetLabel('%.2f'%(1/self.scene.zoom))
        evt.Skip()
        
    def UpdateAllInfo(self):
        """更新全部状态信息"""
        
        pos = self.scene.getCamera()
        self.st_elevation.SetLabel('%.2f°'%pos['elevation'])
        self.st_azimuth.SetLabel('%.2f°'%pos['azimuth'])
        self.st_dist.SetLabel('%.2f'%pos['dist'])
        self.st_cam.SetLabel('[%.2f, %.2f, %.2f]'%(*pos['cam'],))
        self.st_aim.SetLabel('[%.2f, %.2f, %.2f]'%(*pos['aim'],))
        
        self.st_zoom.SetLabel('%.2f'%(1/self.scene.zoom))
        self.st_view.SetLabel('[%.2f, %.2f, %.2f, %.2f, %.2f, %.2f]'%(*list(self.scene.view),))
        
        self.st_head.SetLabel(self.scene.head)
        self.st_scale.SetLabel('[%.2f, %.2f, %.2f]'%(*list(self.scene.scale),))
        
    def ClearScene(self):
        """清空场景"""
        
        self.axes.deleteModel('xyz')
        self.cbar.deleteModel('cb')
        for model_name in list(self.master.models.keys()):
            self.master.deleteModel(model_name)
        
        self.axes.update()
        self.cbar.update()
        self.master.update()
        
    def DrawScene(self):
        """重绘场景"""
        
        if self.model_curr == '正弦波':
            # 场景设置：Y轴向上
            self.scene.setCamera(cam=[0, 0, 10], head='y+', save=True)
            self.scene.setView([-7, 7, -7, 7, 7, 25], save=True)
            self.scene.setScale([2, 2, 2], save=True)
            self.scene.setZoom(1.0, save=True)
            self.UpdateAllInfo()
            
            # 重置视区尺寸
            self.master.resetBox((0, 0, 1, 1))
            
            # 生成数据，绘制模型
            x = np.linspace(-2*np.pi, 2*np.pi, 1000)
            y = np.sin(x)
            z = np.zeros(1000)
            v = np.dstack((x,y,z))[0]
            c = self.cm.map(y, self.cm_curr, mode='RGBA')
            
            y_grid, x_grid = np.mgrid[-1.0:1.0:5j, -2*np.pi:2*np.pi:25j]
            z_grid = np.zeros((5, 25))
            c_grid = np.array([0.8, 1.0, 1.0, 0.3])
            
            self.master.drawLine('sin', v, c, method='SINGLE')
            self.master.drawMesh('grid', x_grid, y_grid, z_grid, c=c_grid, mode='FLBL')
            self.master.update()
            
            # 坐标轴
            self.axes.drawAxes('xyz', k=6)
            self.axes.update()
            
            # 控件可用性设置
            self.cb_axes.SetValue(True)
            self.cb_cm.Enable(False)
            self.ch_cm.Enable(True)
            self.rb_render_0.Enable(False)
            self.rb_render_1.Enable(False)
            self.rb_render_2.Enable(False)
            self.rb_render_3.Enable(False)
        elif self.model_curr == '球和六面体':
            # 场景设置：Z轴向上
            self.scene.setCamera(cam=[0, -3.5, 0], head='z+', save=True)
            self.scene.setView([-1, 1, -1, 1, 2, 6], save=True)
            self.scene.setScale([1, 1, 1], save=True)
            self.scene.setZoom(1.0, save=True)
            self.UpdateAllInfo()
            
            # 重置视区尺寸
            self.master.resetBox((0, 0, 1, 1))
            
            # 生成数据，绘制模型
            lat, lon = np.mgrid[-0.5*np.pi:0.5*np.pi:51j, -np.pi:np.pi:101j]
            z = np.sin(lat)
            x = np.cos(lat)*np.cos(lon)
            y = np.cos(lat)*np.sin(lon)
            c = self.cm.map(x*y, self.cm_curr, mode='RGBA')
            self.master.drawMesh('ball', x, y, z, c=c, mode=self.render)
            
            v0, v1, v2, v3 = [1,1,-1], [-1,1,-1], [-1,-1,-1], [1,-1,-1]
            v4, v5, v6, v7 = [1,1,1], [-1,1,1], [-1,-1,1], [1,-1,1]
            
            bottom = np.array([v0, v3, v2, v1])*0.75
            top = np.array([v4, v5, v6, v7])*0.75
            front = np.array([v7, v6, v2, v3])*0.75
            back = np.array([v4, v0, v1, v5])*0.75
            right = np.array([v4, v7, v3, v0])*0.75
            left = np.array([v6, v5, v1, v2])*0.75
            
            self.master.drawSurface('cubo', bottom, c=np.random.random(3), mode=self.render)
            self.master.drawSurface('cubo', top, c=np.random.random(3), mode=self.render)
            self.master.drawSurface('cubo', front, c=np.random.random(3), mode=self.render)
            self.master.drawSurface('cubo', back, c=np.random.random(3), mode=self.render)
            self.master.drawSurface('cubo', right, c=np.random.random(3), mode=self.render)
            self.master.drawSurface('cubo', left, c=np.random.random(3), mode=self.render)
            self.master.update()
            
            # 坐标轴
            self.axes.drawAxes('xyz', k=1.2)
            self.axes.update()
            
            # 控件可用性设置
            self.cb_axes.SetValue(True)
            self.cb_cm.Enable(False)
            self.ch_cm.Enable(True)
            self.rb_render_0.Enable(True)
            self.rb_render_1.Enable(True)
            self.rb_render_2.Enable(True)
            self.rb_render_3.Enable(True)
        elif self.model_curr == '曲面A':
            # 场景设置：Z轴向上
            self.scene.setCamera(cam=[4, -1, 0], head='z+', save=True)
            self.scene.setView([-1,1,-1,1,3.5,10], save=True)
            self.scene.setScale([1, 1, 1], save=True)
            self.scene.setZoom(1.0, save=True)
            self.UpdateAllInfo()
            
            # 重置视区尺寸
            self.master.resetBox((0, 0, 0.85, 1))
            
            # 生成数据，绘制模型
            y, x = np.mgrid[-1:1:51j, -1:1:51j]
            z = x*y
            c = self.cm.map(z, self.cm_curr, mode='RGBA')
            
            self.master.drawMesh('z=xy', x, y, z, c, mode=self.render)
            self.master.update()
            
            # ColorBar
            self.cbar.drawColorBar(
                'cb', 
                (z.min(),z.max()), 
                self.cm_curr, 
                'v', 
                title_name = '色标', 
                title_size = 35,
                title_offset = (-0.07, 0),
                label_precision = '%.2f'
            )
            self.cbar.update()
            
            # 坐标轴
            self.axes.drawAxes('xyz', k=1.0)
            self.axes.update()
            
            # 控件可用性设置
            self.cb_axes.SetValue(True)
            self.cb_cm.Enable(True)
            self.ch_cm.Enable(True)
            self.rb_render_0.Enable(True)
            self.rb_render_1.Enable(True)
            self.rb_render_2.Enable(True)
            self.rb_render_3.Enable(True)
        elif self.model_curr == '曲面B':
            # 场景设置：Z轴向上
            self.scene.setCamera(cam=[11, 0, 9], head='z+', save=True)
            self.scene.setView([-4, 4, -4, 4, 10, 20], save=True)
            self.scene.setScale([1, 1, 1], save=True)
            self.scene.setZoom(0.7, save=True)
            self.UpdateAllInfo()
            
            # 重置视区尺寸
            self.master.resetBox((0, 0, 0.85, 1))
            
            # 生成数据，绘制模型
            y, x = np.mgrid[-np.pi:np.pi:51j, -np.pi:np.pi:51j]
            z = np.sin(x) + np.cos(y)
            c = self.cm.map(z, self.cm_curr, mode='RGBA')
            
            self.master.drawMesh('z=xy', x, y, z, c, mode=self.render)
            self.master.update()
            
            # ColorBar
            self.cbar.drawColorBar(
                'cb', 
                (z.min(),z.max()), 
                self.cm_curr, 
                'v', 
                title_name = '色标', 
                title_size = 35,
                title_offset = (-0.07, 0),
                label_precision = '%.2f'
            )
            self.cbar.update()
            
            # 坐标轴
            self.axes.drawAxes('xyz', k=4)
            self.axes.update()
            
            # 控件可用性设置
            self.cb_axes.SetValue(True)
            self.cb_cm.Enable(True)
            self.ch_cm.Enable(True)
            self.rb_render_0.Enable(True)
            self.rb_render_1.Enable(True)
            self.rb_render_2.Enable(True)
            self.rb_render_3.Enable(True)
        elif self.model_curr == '曲面C':
            # 场景设置：Z轴向上
            self.scene.setCamera(cam=[11, 0, 9], head='z+', save=True)
            self.scene.setView([-2, 2, -2, 2, 10, 20], save=True)
            self.scene.setScale([1, 1, 1], save=True)
            self.scene.setZoom(1.0, save=True)
            self.UpdateAllInfo()
            
            # 重置视区尺寸
            self.master.resetBox((0, 0, 0.85, 1))
            
            # 生成数据，绘制模型
            x, y = np.mgrid[-2:2:50j,-2:2:50j]
            z = 2*x*np.exp(-x**2-y**2)
            c = self.cm.map(z, self.cm_curr, mode='RGBA')
            
            self.master.drawMesh('z=xy', x, y, z, c, mode=self.render)
            self.master.update()
            
            # ColorBar
            self.cbar.drawColorBar(
                'cb', 
                (z.min(),z.max()), 
                self.cm_curr, 
                'v', 
                title_name = '色标', 
                title_size = 35,
                title_offset = (-0.07, 0),
                label_precision = '%.2f'
            )
            self.cbar.update()
            
            # 坐标轴
            self.axes.drawAxes('xyz', k=2.5)
            self.axes.update()
            
            # 控件可用性设置
            self.cb_axes.SetValue(True)
            self.cb_cm.Enable(True)
            self.ch_cm.Enable(True)
            self.rb_render_0.Enable(True)
            self.rb_render_1.Enable(True)
            self.rb_render_2.Enable(True)
            self.rb_render_3.Enable(True)
        elif self.model_curr == '体数据绘制': # sin(x) + sin(y) + sin(z) = 40
            # 场景设置：Z轴向上
            self.scene.setCamera(cam=[0, -35, 0], head='z+', save=True)
            self.scene.setView([-10,10,-10,10,15,50], save=True)
            self.scene.setScale([1, 1, 1], save=True)
            self.scene.setZoom(1.0, save=True)
            self.UpdateAllInfo()
            
            # 重置视区尺寸
            self.master.resetBox((0, 0, 0.85, 1))
            
            # 生成数据，绘制模型
            y, x = np.mgrid[-10:10:101j, -10:10:101j]
            z = np.linspace(-10, 10, 101)
            v = np.sin(z).repeat(101*101).reshape((101,101,101)) + np.sin(x) + np.sin(y)
            #v = np.where((v>-0.5)&(v<0.5), v, np.nan)
            #v = np.where((v<-0.5)|(v>0.5), v, np.nan)
            #v = np.where((v>-0.1)&(v<0.1), v, np.nan)
            v = np.where((v>-0.01)&(v<0.01), v, np.nan)
            c = self.cm.map(v, self.cm_curr, mode='RGBA')
            
            self.master.drawVolume('volume', c, x, y, z, smooth=False)
            self.master.update()
            
            # ColorBar
            self.cbar.drawColorBar(
                'cb', 
                (np.nanmin(v), np.nanmax(v)), 
                self.cm_curr, 
                'v', 
                title_name = '色标', 
                title_size = 35,
                title_offset = (-0.07, 0),
                label_precision = '%.2f'
            )
            self.cbar.update()
            
            # 坐标轴
            self.axes.drawAxes('xyz', k=8.0)
            self.axes.update()
            
            # 控件可用性设置
            self.cb_axes.SetValue(True)
            self.cb_cm.Enable(True)
            self.rb_render_0.Enable(True)
            self.rb_render_1.Enable(True)
            self.rb_render_2.Enable(True)
            self.rb_render_3.Enable(True)
        elif self.model_curr == '地球':
            # 场景设置：Z轴向上
            self.scene.setCamera(cam=[-2.5, 4.5, 0], head='z+', save=True)
            self.scene.setView([-1, 1, -1, 1, 3.5, 10], save=True)
            self.scene.setScale([1, 1, 1], save=True)
            self.scene.setZoom(1.0, save=True)
            self.UpdateAllInfo()
            
            # 重置视区尺寸
            self.master.resetBox((0, 0, 1, 1))
            
            # 从等经纬地图上读取经纬度网格上的每一个格点的颜色
            c = np.array(Image.open('res/shadedrelief.png'))/255
            
            # 生成和等经纬地图分辨率一致的经纬度网格，计算经纬度网格上的每一个格点的空间坐标(x,y,z)
            lats, lons = np.mgrid[np.pi/2:-np.pi/2:complex(0,c.shape[0]), 0:2*np.pi:complex(0,c.shape[1])]
            x = np.cos(lats)*np.cos(lons)
            y = np.cos(lats)*np.sin(lons)
            z = np.sin(lats)
            
            self.master.drawMesh('earth', x, y, z, c)
            self.master.update()
            
            # 坐标轴
            self.axes.drawAxes('xyz', k=1.0)
            self.axes.update()
            
            # 控件可用性设置
            self.cb_axes.SetValue(True)
            self.cb_cm.Enable(False)
            self.ch_cm.Enable(False)
            self.rb_render_0.Enable(False)
            self.rb_render_1.Enable(False)
            self.rb_render_2.Enable(False)
            self.rb_render_3.Enable(False)
        elif self.model_curr == '三维重建':
            # 场景设置：Z轴向上
            self.scene.setCamera(cam=[0, 4.5, 1.8], head='z+', save=True)
            self.scene.setView([-1, 1, -1, 1, 3.5, 10], save=True)
            self.scene.setScale([1, 1, 1], save=True)
            self.scene.setZoom(0.75, save=True)
            self.UpdateAllInfo()
            
            # 重置视区尺寸
            self.master.resetBox((0, 0, 1, 1))
            
            # 读取109张头部CT的断层扫描图片
            data = np.stack([np.array(Image.open('res/head%d.png'%i)) for i in range(109)], axis=0)
            data = np.rollaxis(data, 2, start=0)[::-1] # 反转数组轴（2轴变0轴），然后0轴逆序
            
            # 三维重建（本质上是体数据绘制）
            self.master.drawVolume('volume', data/255.0, method='Q', smooth=False)
            self.master.update()
            
            # 坐标轴
            self.axes.drawAxes('xyz', k=1.0)
            self.axes.update()
            
            # 控件可用性设置
            self.cb_axes.SetValue(True)
            self.cb_cm.Enable(False)
            self.ch_cm.Enable(False)
            self.rb_render_0.Enable(False)
            self.rb_render_1.Enable(False)
            self.rb_render_2.Enable(False)
            self.rb_render_3.Enable(False)
            
class mainApp(wx.App):
    def OnInit(self):
        self.Frame = mainFrame()
        self.Frame.Show()
        return True

if __name__ == "__main__":
    app = mainApp()
    app.MainLoop()
    
# -*- coding: utf-8 -*-


import time
import numpy as np
import wx

from scene import *
from colormap import *


FONT_FILE = r"C:\Windows\Fonts\simfang.ttf"


class mainFrame(wx.Frame):
    """程序主窗口类，继承自wx.Frame"""

    def __init__(self):
        """构造函数"""

        wx.Frame.__init__(self, None, -1, u'WxGL项目演示', style=wx.DEFAULT_FRAME_STYLE)
        self.Maximize()
        self.SetBackgroundColour(wx.Colour(240,240,240))
        
        self.models = dict()            # 所有模型
        self.selected = list()          # 选中显示的模型
        self.curr = 0                   # 动画显示时当前显示的模型索引
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        
        self.cm = ColorMap()
        self.cm_list = list(self.cm.getColorMaps())
        
        self.cm_curr = None                             # 当前选中的调色板
        self.ismap = False                              # 是否显示地形图
        self.isvolume = False                           # 体数据绘制标志
        self.mode = 0                                   # 剖切方式
        self.step_lon = 2.0                             # 沿经线剖切的间隔
        self.step_lat = 2.0                             # 沿纬线剖切的间隔
        self.step_rotation = 10.0                       # 旋转剖切的间隔
        self.o_lon = 117.0                              # 旋转圆心的经度
        self.o_lat = 37.0                               # 旋转圆心的纬度
        self.v_min = None                               # 体数据最小值
        self.v_max = None                               # 体数据最大值
        
        self.raw = None                                 # 原始数据
        self.grid_lon = None
        self.grid_lan = None
        self.height = None
        self.r_temp = None
        self.r_lon = None
        self.r_lat = None
        
        
        # 操作区
        btn_p = wx.Panel(self, -1, pos=(0,0), size=(350,185), style=wx.BORDER_SUNKEN)
        
        btn_mode = wx.Button(btn_p, -1, u'切换投影模式', pos=(40,20), size=(120,25))
        btn_view = wx.Button(btn_p, -1, u'设置视景体', pos=(185,20), size=(120,25))
        btn_cam = wx.Button(btn_p, -1, u'设置相机位置', pos=(40,60), size=(120,25))
        btn_aim = wx.Button(btn_p, -1, u'设置目标点位', pos=(185,60), size=(120,25))
        btn_head = wx.Button(btn_p, -1, u'设置头部指向', pos=(40,100), size=(120,25))
        btn_posture = wx.Button(btn_p, -1, u'设置相机姿态', pos=(185,100), size=(120,25))
        btn_reset = wx.Button(btn_p, -1, u'恢复初始状态', pos=(40,140), size=(120,25))
        btn_capture = wx.Button(btn_p, -1, u'屏幕截图', pos=(185,140), size=(120,25))
        
        ch_data = wx.Choice(self, id=-1, choices=[u'数值预报',u'FY-4A探测仪'])
        rb_data_0 = wx.RadioButton(self, id=-1, label=u'数据层', style=wx.RB_GROUP)
        rb_data_1 = wx.RadioButton(self, id=-1, label=u'数据体')
        rb_data_0.SetValue(True)
        
        ch_cm = wx.Choice(self, id=-1, choices=self.cm_list)
        cb_cm = wx.CheckBox(self, id=-1, label=u'显示地形图')
        ch_cm.SetSelection(12)
        self.cm_curr = self.cm_list[12]
        
        self.clb = wx.CheckListBox(self, -1, choices=[], size=(130,-1))
        btn_animation = wx.Button(self, -1, u'自动播放', size=(-1, 25))
        
        rb_0 = wx.RadioButton(self, id=-1, label=u'分层显示', style=wx.RB_GROUP)
        rb_1 = wx.RadioButton(self, id=-1, label=u'沿经线剖切，间隔')
        rb_2 = wx.RadioButton(self, id=-1, label=u'沿纬线剖切，间隔')
        rb_3 = wx.RadioButton(self, id=-1, label=u'旋转剖切，间隔')
        
        tc_rb_1 = wx.TextCtrl(self, -1, '2.0', size=(40,18), name='tc_rb_1', style=wx.TE_CENTER)
        tc_rb_2 = wx.TextCtrl(self, -1, '2.0', size=(40,18), name='tc_rb_2', style=wx.TE_CENTER)
        tc_rb_3 = wx.TextCtrl(self, -1, '10.0', size=(40,18), name='tc_rb_3', style=wx.TE_CENTER)
        
        text_o_lon = wx.StaticText(self, -1, u'旋转中心经度：')
        text_o_lat = wx.StaticText(self, -1, u'旋转中心纬度：')
        
        tc_o_lon = wx.TextCtrl(self, -1, '117.0', size=(60,18), name='tc_o_lon', style=wx.TE_CENTER)
        tc_o_lat = wx.TextCtrl(self, -1, '37.0', size=(60,18), name='tc_o_lat', style=wx.TE_CENTER)
        
        tc_v_min = wx.TextCtrl(self, -1, '', size=(100,18), name='tc_v_min', style=wx.TE_CENTER)
        tc_v_max = wx.TextCtrl(self, -1, '', size=(100,18), name='tc_v_max', style=wx.TE_CENTER)
        btn_volume = wx.Button(self, -1, u'确定', size=(60, 25))
        
        # 信息显示区
        info_p = wx.Panel(self, -1, size=(350,240), style=wx.BORDER_SUNKEN)
        
        text = wx.StaticText(info_p, -1, u'投影方式：', pos=(0,10), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, u'视景体：', pos=(0,30), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, u'模型缩放：', pos=(0,50), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, u'视口缩放：', pos=(0,70), size=(90,-1), style=wx.ALIGN_RIGHT)
        
        text = wx.StaticText(info_p, -1, u'相机位置：', pos=(0,100), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, u'目标点位：', pos=(0,120), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, u'头部指向：', pos=(0,140), size=(90,-1), style=wx.ALIGN_RIGHT)
        
        text = wx.StaticText(info_p, -1, u'仰角：', pos=(0,170), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, u'方位角：', pos=(0,190), size=(90,-1), style=wx.ALIGN_RIGHT)
        text = wx.StaticText(info_p, -1, u'距离：', pos=(0,210), size=(90,-1), style=wx.ALIGN_RIGHT)
        
        self.st_mode = wx.StaticText(info_p, -1, u'透视投影', pos=(90,10), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_view = wx.StaticText(info_p, -1, u'[-1, 1, -1, 1, 1, 5]', pos=(90,30), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_scale = wx.StaticText(info_p, -1, u'[1, 1, 1]', pos=(90,50), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_port = wx.StaticText(info_p, -1, u'1.000000', pos=(90,70), size=(230,-1), style=wx.ALIGN_LEFT)
        
        self.st_cam = wx.StaticText(info_p, -1, u'[-3, -1, 0]', pos=(90,100), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_aim = wx.StaticText(info_p, -1, u'[0, 0, 0]', pos=(90,120), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_head = wx.StaticText(info_p, -1, u'z+', pos=(90,140), size=(230,-1), style=wx.ALIGN_LEFT)
        
        self.st_elevation = wx.StaticText(info_p, -1, u'10.21°', pos=(90,170), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_azimuth = wx.StaticText(info_p, -1, u'24.55°', pos=(90,190), size=(230,-1), style=wx.ALIGN_LEFT)
        self.st_dist = wx.StaticText(info_p, -1, u'5.35', pos=(90,210), size=(230,-1), style=wx.ALIGN_LEFT)
        
        # 创建场景，并设置
        self.scene = GLScene(self, FONT_FILE)
        #self.scene.setView([-1,1,-1,1,2,500])
        self.scene.setPosture(elevation=30, azimuth=-45, save=True)
        
        # 装配布局管理器
        sizer_data = wx.BoxSizer()
        sizer_data.Add(ch_data, 2, wx.EXPAND|wx.LEFT, 20)
        sizer_data.Add(rb_data_0, 1, wx.EXPAND|wx.LEFT, 20)
        sizer_data.Add(rb_data_1, 1, wx.EXPAND|wx.ALL, 0)
        
        sizer_data_box = wx.StaticBoxSizer(wx.StaticBox(self, -1, u"数据选择"), wx.VERTICAL)
        sizer_data_box.Add(sizer_data, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        
        sizer_cm = wx.BoxSizer()
        sizer_cm.Add(ch_cm, 1, wx.EXPAND|wx.LEFT, 20)
        sizer_cm.Add(cb_cm, 1, wx.EXPAND|wx.LEFT, 20)
        
        sizer_cm_box = wx.StaticBoxSizer(wx.StaticBox(self, -1, u"调色板设置"), wx.VERTICAL)
        sizer_cm_box.Add(sizer_cm, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        
        sizer_rb_1 = wx.BoxSizer()
        sizer_rb_1.Add(rb_1, 0, wx.EXPAND|wx.ALL, 0)
        sizer_rb_1.Add(tc_rb_1, 0, wx.EXPAND|wx.RIGHT, 5)
        sizer_rb_1.Add(wx.StaticText(self, -1, u'度'), 0, wx.EXPAND|wx.TOP, 1)
        
        sizer_rb_2 = wx.BoxSizer()
        sizer_rb_2.Add(rb_2, 0, wx.EXPAND|wx.ALL, 0)
        sizer_rb_2.Add(tc_rb_2, 0, wx.EXPAND|wx.RIGHT, 5)
        sizer_rb_2.Add(wx.StaticText(self, -1, u'度'), 0, wx.EXPAND|wx.TOP, 1)
        
        sizer_rb_3 = wx.BoxSizer()
        sizer_rb_3.Add(rb_3, 0, wx.EXPAND|wx.ALL, 0)
        sizer_rb_3.Add(tc_rb_3, 0, wx.EXPAND|wx.RIGHT, 5)
        sizer_rb_3.Add(wx.StaticText(self, -1, u'度'), 0, wx.EXPAND|wx.TOP, 1)
        
        sizer_o_lon = wx.BoxSizer()
        sizer_o_lon.Add(text_o_lon, 0, wx.EXPAND|wx.LEFT, 17)
        sizer_o_lon.Add(tc_o_lon, 0, wx.EXPAND|wx.ALL, 0)
        
        sizer_o_lat = wx.BoxSizer()
        sizer_o_lat.Add(text_o_lat, 0, wx.EXPAND|wx.LEFT, 17)
        sizer_o_lat.Add(tc_o_lat, 0, wx.EXPAND|wx.ALL, 0)
        
        sizer_section = wx.BoxSizer(wx.VERTICAL)
        sizer_section.Add(rb_0, 0, wx.EXPAND|wx.ALL, 5)
        sizer_section.Add(sizer_rb_1, 0, wx.EXPAND|wx.ALL, 5)
        sizer_section.Add(sizer_rb_2, 0, wx.EXPAND|wx.ALL, 5)
        sizer_section.Add(sizer_rb_3, 0, wx.EXPAND|wx.ALL, 5)
        sizer_section.Add(sizer_o_lon, 0, wx.EXPAND|wx.ALL, 5)
        sizer_section.Add(sizer_o_lat, 0, wx.EXPAND|wx.ALL, 5)
        sizer_section.Add(btn_animation, 0, wx.EXPAND|wx.ALL, 20)
        
        self.sizer_layer = wx.BoxSizer()
        self.sizer_layer.Add(self.clb, 0, wx.EXPAND|wx.ALL, 0)
        self.sizer_layer.Add(sizer_section, 1, wx.EXPAND|wx.ALL, 10)
        
        sizer_range = wx.BoxSizer()
        sizer_range.Add(tc_v_min, 0, wx.EXPAND|wx.LEFT, 20)
        sizer_range.Add(wx.StaticText(self, -1, u'~'), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        sizer_range.Add(tc_v_max, 0, wx.EXPAND|wx.ALL, 0)
        sizer_range.Add(btn_volume, 0, wx.EXPAND|wx.LEFT, 20)
        
        self.sizer_volume = wx.StaticBoxSizer(wx.StaticBox(self, -1, u"数据值域"), wx.VERTICAL)
        self.sizer_volume.Add(sizer_range, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        
        self.sizer_left = wx.BoxSizer(wx.VERTICAL) 
        self.sizer_left.Add(btn_p, 0, wx.EXPAND|wx.ALL, 0)
        self.sizer_left.Add(sizer_data_box, 0, wx.EXPAND|wx.TOP, 20)
        self.sizer_left.Add(sizer_cm_box, 0, wx.EXPAND|wx.TOP, 20)
        self.sizer_left.Add(self.sizer_layer, 1, wx.EXPAND|wx.TOP, 20)
        self.sizer_left.Add(self.sizer_volume, 0, wx.EXPAND|wx.TOP, 20)
        self.sizer_left.Add(info_p, 0, wx.EXPAND|wx.TOP, 20)
        
        self.sizer_left.Hide(self.sizer_volume)
        
        self.sizer_max = wx.BoxSizer() 
        self.sizer_max.Add(self.sizer_left, 0, wx.EXPAND|wx.ALL, 10) 
        self.sizer_max.Add(self.scene, 1, wx.EXPAND|wx.ALL, 0)
        
        self.SetAutoLayout(True) 
        self.SetSizer(self.sizer_max)
        self.Layout()
        
        # 绑定操作行为
        self.Bind(wx.EVT_BUTTON, self.onChangeMode, btn_mode)
        self.Bind(wx.EVT_BUTTON, self.onCapture, btn_capture)
        self.Bind(wx.EVT_BUTTON, self.onRestore, btn_reset)
        self.Bind(wx.EVT_BUTTON, self.onSetView, btn_view)
        self.Bind(wx.EVT_BUTTON, self.onSetCam, btn_cam)
        self.Bind(wx.EVT_BUTTON, self.onSetAim, btn_aim)
        self.Bind(wx.EVT_BUTTON, self.onSetHead, btn_head)
        self.Bind(wx.EVT_BUTTON, self.onSetPosture, btn_posture)
        
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioData, rb_data_0 )
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioData, rb_data_1 )
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSection, rb_0 )
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSection, rb_1 )
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSection, rb_2 )
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSection, rb_3 )
        self.Bind(wx.EVT_CHOICE, self.onChoiceData, ch_data)
        self.Bind(wx.EVT_CHOICE, self.onChoiceCM, ch_cm)
        self.Bind(wx.EVT_CHECKBOX, self.onCheckBox, cb_cm)
        self.Bind(wx.EVT_TEXT, self.onTextCtr)
        self.Bind(wx.EVT_BUTTON, self.onAnimation, btn_animation)
        self.Bind(wx.EVT_BUTTON, self.onVolume, btn_volume)
        self.Bind(wx.EVT_CHECKLISTBOX, self.onCheckListBox, self.clb)
        
        # 创建master视区，并添加模型
        master = self.scene.addRegion('master', (0,0,0.85,1))
        
        # 创建axes视区，并添加部件
        axes = self.scene.addRegion('axes', (0,0,0.15,0.15), scale=[1.2,1.2,1.2])
        axes.drawAxes('xyz')
        axes.update()
        
        # 创建colorbar视区，并添加模型
        cb = self.scene.addRegion('cb', (0.85,0,0.15,1), lookat=[0,0,5,0,0,0,0,1,0], scale=[1,1,1], mode='ortho')
        
        # 更窗口信息显示
        self.st_view.SetLabel(u'[%.2f, %.2f, %.2f, %.2f, %.2f, %.2f]'%(self.scene.view[0],self.scene.view[1],self.scene.view[2],self.scene.view[3],self.scene.view[4],self.scene.view[5]))
        self.st_scale.SetLabel(u'[%.2f, %.2f, %.2f]'%(self.scene.scale[0],self.scene.scale[1],self.scene.scale[2]))
        self.st_aim.SetLabel(u'[%.2f, %.2f, %.2f]'%(self.scene.aim[0],self.scene.aim[1],self.scene.aim[2]))
        self.st_head.SetLabel(self.scene.head)
        
    def onChangeMode(self, evt):
        """切换投影模式"""
        
        if self.scene.getMode() == 'ortho':
            mode = 'cone'
            self.st_mode.SetLabel(u'透视投影')
        else:
            mode = 'ortho'
            self.st_mode.SetLabel(u'平行投影')
        
        self.scene.setMode(mode)
    
    def onCapture(self, evt):
        """屏幕截图"""
        
        fn = 'capture/%d.png'%int(time.time()*1000)
        self.scene.screenshot(fn, alpha=True)
    
    def onRestore(self, evt):
        """恢复初始状态"""
        
        t = time.localtime()
        self.scene.restorePosture()
    
    def onSetView(self, evt):
        """设置视景体"""
        
        dlg = wx.TextEntryDialog(self, u'请输入视景体6个参数，以半角逗号分隔：', u'设置视景体')
        dlg.SetValue('')
        
        if dlg.ShowModal() == wx.ID_OK:
            self.scene.setView([float(item.strip()) for item in dlg.GetValue().split(',')])
            self.st_view.SetLabel(u'[%.2f, %.2f, %.2f, %.2f, %.2f, %.2f]'%(self.scene.view[0],self.scene.view[1],self.scene.view[2],self.scene.view[3],self.scene.view[4],self.scene.view[5]))
        
        dlg.Destroy()
    
    def onSetCam(self, evt):
        """设置相机"""
        
        dlg = wx.TextEntryDialog(self, u'请输入相机位置（3个参数，以半角逗号分隔）：', u'设置相机')
        dlg.SetValue('')
        
        if dlg.ShowModal() == wx.ID_OK:
            self.scene.setCamera(cam=[float(item.strip()) for item in dlg.GetValue().split(',')])
        
        dlg.Destroy()
    
    def onSetAim(self, evt):
        """设置目标点位"""
        
        dlg = wx.TextEntryDialog(self, u'请输入目标点位（3个参数，以半角逗号分隔）：', u'设置目标点位')
        dlg.SetValue('')
        
        if dlg.ShowModal() == wx.ID_OK:
            self.scene.setCamera(aim=[float(item.strip()) for item in dlg.GetValue().split(',')])
        
        dlg.Destroy()
    
    def onSetHead(self, evt):
        """设置头部指向"""
        
        dlg = wx.TextEntryDialog(self, u'请输入头部指向（z+|y+|x+）：', u'设置头部指向')
        dlg.SetValue('')
        
        if dlg.ShowModal() == wx.ID_OK:
            self.scene.setCamera(head=dlg.GetValue().strip())
        
        dlg.Destroy()
    
    def onSetPosture(self, evt):
        """设置相机姿态"""
        
        dlg = wx.TextEntryDialog(self, u'请输入依次输入仰角、方位角和距离，以半角逗号分隔：', u'设置相机姿态')
        dlg.SetValue('')
        
        if dlg.ShowModal() == wx.ID_OK:
            elevation, azimuth, dist = [item.strip() for item in dlg.GetValue().split(',')]
            elevation = float(elevation) if elevation else None
            azimuth = float(azimuth) if azimuth else None
            dist = float(dist) if dist else None
            
            self.scene.setPosture(elevation=elevation, azimuth=azimuth, dist=dist,)
        
        dlg.Destroy()
    
    def onRadioData(self, evt):
        """选择绘制层数据/体数据"""
        
        if evt.GetEventObject().GetLabel() == u'数据层':
            self.sizer_left.Hide(self.sizer_volume)
            self.sizer_left.Show(self.sizer_layer)
            self.isvolume = False
            
            self.clearRegin(['master', 'cb'])
            self.drawLayers()
        else:
            self.sizer_left.Show(self.sizer_volume)
            self.sizer_left.Hide(self.sizer_layer)
            self.isvolume = True
            
            self.clearRegin(['master', 'cb'])
            self.drawVolume()
        
        self.sizer_max.Layout()
        self.Refresh()
    
    def onRadioSection(self, evt):
        """选择剖切方式"""
        
        label = evt.GetEventObject().GetLabel()
        if label == u'分层显示':
            self.mode = 0
        elif label == u'沿经线剖切，间隔':
            self.mode = 1
        elif label == u'沿纬线剖切，间隔':
            self.mode = 2
        else:
            self.mode = 3
        
        self.clearRegin(['master'])
        self.drawLayers(colorbar=False)
    
    def onChoiceData(self, evt):
        """选择数据"""
        
        data_name = evt.GetString()
        if data_name == u'数值预报':
            self.raw = np.load('data/NWP_GBAL_20190226_1200.npz')
        else:
            self.raw = np.load('data/FY4A-_GIIRS-_N_REGX_1047E_L2-_AVP-_MULT_NUL_20180228030000_20180228052549_016KM_V0001.npz')
            
        print('------------------------------------')
        print(u'开始加载%s数据'%data_name)
        for key in self.raw:
            print(key, self.raw[key].shape)
        
        # 经纬度和高度数据标准化
        self.r_temp = (np.nanmin(self.raw['temp']), np.nanmax(self.raw['temp']))
        self.r_lon = (np.nanmin(self.raw['grid_lon']), np.nanmax(self.raw['grid_lon']))
        self.r_lat = (np.nanmin(self.raw['grid_lat']), np.nanmax(self.raw['grid_lat']))
        k = 2.0/max(self.r_lon[1]-self.r_lon[0], self.r_lat[1]-self.r_lat[0])
        
        self.grid_lon = k*(self.raw['grid_lon']-self.r_lon[0])
        self.grid_lon -= (np.nanmax(self.grid_lon)-np.nanmin(self.grid_lon))/2.0
        self.grid_lat = k*(self.raw['grid_lat']-self.r_lat[0])
        self.grid_lat -= (np.nanmax(self.grid_lat)-np.nanmin(self.grid_lat))/2.0
        self.height = 0.00005*self.raw['height']
        
        self.refresh()
    
    def onChoiceCM(self, evt):
        """选择调色板"""
        
        self.cm_curr = evt.GetString()
        
        if self.isvolume:
            self.clearRegin(['master', 'cb'])
            self.drawVolume()
        else:
            self.clearRegin(['master', 'cb'])
            self.drawLayers()
        
    def onCheckBox(self, evt):
        """是否显示地形图"""
        
        self.ismap = evt.GetEventObject().IsChecked()
        self.refresh()
        
    def onTextCtr(self, evt):
        """输入框内容改变"""
        
        obj = evt.GetEventObject()
        name = obj.GetName()
        
        try:
            value = float(obj.GetValue())
        except:
            obj.SetValue('')
            return
        
        if name == 'tc_rb_1':
            self.step_lon = value
        elif name == 'tc_rb_2':
            self.step_lat = value
        elif name == 'tc_rb_3':
            self.step_rotation = value
        elif name == 'tc_o_lon':
            self.o_lon = value
        elif name == 'tc_o_lat':
            self.o_lat = value
        elif name == 'tc_v_min':
            self.v_min = value
        elif name == 'tc_v_max':
            self.v_max = value
        
    def onVolume(self, evt):
        """使用新的值域选择数据重新体绘制数据"""
        
        self.clearRegin(['master'])
        self.drawVolume(colorbar=False)
        
    def onCheckListBox(self, evt):
        """选中层"""
        
        selected = evt.GetEventObject().GetCheckedStrings()
        for key in self.scene.regions['master'].models:
            if key in selected or (self.ismap and key == 'map'):
                self.scene.regions['master'].showModel(key)
            else:
                self.scene.regions['master'].hideModel(key)
        
        self.scene.regions['master'].update()
        
    def onAnimation(self, evt):
        """自动播放"""
        
        obj = evt.GetEventObject()
        if obj.GetLabel() == u'自动播放':
            obj.SetLabel(u'停止播放')
            for key in self.scene.regions['master'].models:
                if self.ismap and key == 'map':
                    self.scene.regions['master'].showModel(key)
                else:
                    self.scene.regions['master'].hideModel(key)
            self.scene.regions['master'].update()
            self.curr = 0
            self.timer.Start(1000)
        else:
            obj.SetLabel(u'自动播放')
            self.timer.Stop()
            
            selected = self.clb.GetCheckedStrings()
            for key in self.scene.regions['master'].models:
                if key in selected or (self.ismap and key == 'map'):
                    self.scene.regions['master'].showModel(key)
                else:
                    self.scene.regions['master'].hideModel(key)
            
            self.scene.regions['master'].update()
        
    def onTimer(self, evt):
        
        selected = self.clb.GetCheckedStrings()
        model = selected[self.curr]
        for key in self.scene.regions['master'].models:
            if key == selected[self.curr] or (self.ismap and key == 'map'):
                self.scene.regions['master'].showModel(key)
            else:
                self.scene.regions['master'].hideModel(key)
        
        self.scene.regions['master'].update()
        
        self.curr += 1
        self.curr %= len(selected)
    
    def clearRegin(self, region_list):
        """清除指定视区的模型"""
        
        for region_name in region_list:
            region = self.scene.regions[region_name]
            for model_name in list(region.models.keys()):
                region.deleteModel(model_name)
    
    def refresh(self):
        """更新显示"""
        
        # 清除指定视区的模型
        self.clearRegin(['master', 'cb'])
        
        if self.isvolume:
            self.drawVolume()
        else:
            self.drawLayers()
        
    def drawVolume(self, colorbar=True):
        """体数据绘制"""
        
        if self.raw:
            c = self.raw['temp'].copy()
            if self.v_min:
                c[c<self.v_min] = np.nan
            if self.v_max:
                c[c>self.v_max] = np.nan
            
            c = self.cm.map(c, self.cm_curr, mode='RGBA', datamax=self.r_temp[1], datamin=self.r_temp[0])
            x = self.grid_lon
            y = self.grid_lat
            z = self.height
            
            if self.ismap:
                self.scene.regions['master'].drawSurface('map', x, y, self.raw['landform']*0.000005-0.2, self.raw['landscape'], method=0, mode=1)
            
            self.scene.regions['master'].drawVolume('volume', c)
            self.scene.regions['master'].update()
            
            if colorbar:
                self.scene.regions['cb'].drawColorBar('colorbar', self.r_temp, self.cm_curr, 'right', title=u'温度', 
                    title_offset=(-0.25,0.2), 
                    precision=u'%d'
                )
                self.scene.regions['cb'].update()
        
    def drawLayers(self, colorbar=True):
        """层数据绘制"""
        
        if self.raw:
            c = self.cm.map(self.raw['temp'], self.cm_curr, mode='RGBA', datamax=self.r_temp[1], datamin=self.r_temp[0])
            d, h, w  = c.shape[0], c.shape[1], c.shape[2]
            x = self.grid_lon
            y = self.grid_lat
            z = self.height
            
            if self.ismap:
                self.scene.regions['master'].drawSurface('map', x, y, self.raw['landform']*0.000005-0.2, self.raw['landscape'], method=0, mode=1)
              
            if self.mode == 0:
                self.clb.Items = ['%.1fhPa'%p for p in self.raw['airp']]
                for i in range(d):
                    self.scene.regions['master'].drawSurface(self.clb.Items[i], x, y, z[i]*np.ones_like(x), c[i], method=0, mode=1, display=i%3==0)
                
                self.clb.SetChecked(list(range(0, self.clb.GetCount()))[::3])
            elif self.mode == 1:
                items = []
                lon = self.r_lon[0]
                z_h = z.repeat(h).reshape((-1, h))
                while lon < self.r_lon[1]:
                    items.append('%.3f'%lon)
                    col = np.abs(self.raw['grid_lon'][0,:]-lon).argmin()
                    x_h = np.tile(x[:,col], (d,1))
                    y_h = np.tile(y[:,col], (d,1))
                    c_h = c[:d,:,col]
                    self.scene.regions['master'].drawSurface(items[-1], x_h, y_h, z_h, c_h, method=0, mode=1)
                    lon += self.step_lon
                
                self.clb.Items = items
                self.clb.SetChecked(list(range(0, self.clb.GetCount())))
            elif self.mode == 2:
                items = []
                lat = self.r_lat[0]
                z_v = z.repeat(w).reshape((-1, w))
                while lat < self.r_lat[1]:
                    items.append('%.3f'%lat)
                    row = np.abs(self.raw['grid_lat'][:,0]-lat).argmin()
                    x_v = np.tile(x[row,:], (d,1))
                    y_v = np.tile(y[row,:], (d,1))
                    c_v = c[:d,row,:]
                    self.scene.regions['master'].drawSurface(items[-1], x_v, y_v, z_v, c_v, method=0, mode=1)
                    lat += self.step_lat
                
                self.clb.Items = items
                self.clb.SetChecked(list(range(0, self.clb.GetCount())))
            elif self.mode == 3:
                items = []
                x0, y0 = (np.abs(self.raw['grid_lon'][0,:]-self.o_lon)).argmin(), (np.abs(self.raw['grid_lat'][:,0]-self.o_lat)).argmin()
                for phi in np.arange(0,180,self.step_rotation):
                    items.append('%.3f'%phi)
                    if phi == 0 or phi == 180:
                        x_v = np.tile(x[y0,:], (d,1))
                        y_v = np.tile(y[y0,:], (d,1))
                        z_v = z.repeat(w).reshape((-1, w))
                        c_v = c[:d,y0,:]
                        self.scene.regions['master'].drawSurface(items[-1], x_v, y_v, z_v, c_v, method=0, mode=1)
                    elif phi == 90:
                        x_h = np.tile(x[:,x0], (d,1))
                        y_h = np.tile(y[:,x0], (d,1))
                        z_h = z.repeat(h).reshape((-1, h))
                        c_h = c[:d,:,x0]
                        self.scene.regions['master'].drawSurface(items[-1], x_h, y_h, z_h, c_h, method=0, mode=1)
                    else:
                        Y, X = h-1, w-1
                        k = np.tan(np.deg2rad(phi))
                        b = y0-k*x0
                        
                        if -1 < k < 1:
                            if k > 0:
                                xMask = np.arange(int(max(0, -b/k)), int(min(X, (Y-b)/k))).astype(np.int)
                            else:
                                xMask = np.arange(int(max(0, (Y-b)/k)), int(min(X, -b/k))).astype(np.int)
                            yMask = k*xMask+b
                            yMask[yMask<0] = 0
                            yMask[yMask>Y] = Y
                            yMask = np.round_(yMask).astype(np.int)
                        else:
                            if k > 0:
                                yMask = np.arange(int(max(0, b)), int(min(Y, k*X+b))).astype(np.int)
                            else:
                                yMask = np.arange(int(max(0, k*X+b)), int(min(Y, b))).astype(np.int)
                            xMask = (yMask-b)/k
                            xMask[xMask<0] = 0
                            xMask[xMask>X] = X
                            xMask = np.round_(xMask).astype(np.int)
                        
                        xm = np.tile(xMask, d)
                        ym = np.tile(yMask, d)
                        zm = np.arange(d).repeat(xMask.shape[0])
                        
                        x_v = np.tile(self.grid_lon[(yMask,xMask)], (d,1))
                        y_v = np.tile(self.grid_lat[(yMask,xMask)], (d,1))
                        z_v = z.repeat(x_v.shape[1]).reshape((-1, x_v.shape[1]))
                        c_v = c[(zm,ym,xm)].reshape((d,-1,4))
                        
                        self.scene.regions['master'].drawSurface(items[-1], x_v, y_v, z_v, c_v, method=0, mode=1)
                    
                self.clb.Items = items
                self.clb.SetChecked(list(range(0, self.clb.GetCount()))) 
            
            self.scene.regions['master'].update()
            if colorbar:
                self.scene.regions['cb'].drawColorBar('colorbar', self.r_temp, self.cm_curr, 'right', title=u'温度', 
                    title_offset=(-0.25,0.2), 
                    precision=u'%d'
                )
                self.scene.regions['cb'].update()


if __name__ == "__main__":
    """测试代码"""
    
    app = wx.App()
    frame = mainFrame()
    frame.Show(True)
    app.MainLoop()
    
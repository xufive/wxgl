# -*- coding: utf-8 -*-
#
# Copyright 2019 xufive@gmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 

"""
WxGL是一个基于pyopengl的三维数据展示库

WxGL以wx为显示后端，以加速渲染为第一追求目标
借助于wxpython，WxGL可以很好的融合matplotlib等其他数据展示技术
"""


import os, wx
import uuid
import wx.lib.agw.aui as aui
import numpy as np

from . import scene
from . import colormap


BASE_PATH = os.path.dirname(__file__)


class FigureFrame(wx.Frame):
    """"""
    
    ID_RESTORE = wx.NewIdRef()      # 回到初始状态
    ID_AXES = wx.NewIdRef()         # 坐标轴
    ID_GRID = wx.NewIdRef()         # 网格
    ID_ARGS = wx.NewIdRef()         # 设置
    ID_SAVE = wx.NewIdRef()         # 保存
    
    def __init__(self, parent, size=(800,600), **kwds):
        """构造函数"""
        
        for key in kwds:
            if key not in ['head', 'zoom', 'mode', 'elevation', 'azimuth', 'style']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        head = kwds.get('head', 'z+')
        zoom = kwds.get('zoom', 1.0)
        mode = kwds.get('mode', '3D')
        elevation = kwds.get('elevation', 10)
        azimuth = kwds.get('azimuth', 30)
        style = kwds.get('style', 'black')
        
        wx.Frame.__init__(self, None, -1, u'wxPlot', style=wx.DEFAULT_FRAME_STYLE)
        self.parent = parent
        self.SetSize(size)
        self.Center()
        
        icon = wx.Icon(os.path.join(BASE_PATH, 'res', 'wxplot.ico'))
        self.SetIcon(icon)
        
        bmp_restore = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_restore.png'), wx.BITMAP_TYPE_ANY)
        bmp_axes = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_axes.png'), wx.BITMAP_TYPE_ANY)
        bmp_grid = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_grid.png'), wx.BITMAP_TYPE_ANY)
        bmp_args = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_args.png'), wx.BITMAP_TYPE_ANY)
        bmp_save = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_save.png'), wx.BITMAP_TYPE_ANY)
        
        self.tb = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize)
        self.tb.SetToolBitmapSize(wx.Size(32, 32))
        self.tb.AddSimpleTool(self.ID_RESTORE, '复位', bmp_restore, '回到初始状态')
        self.tb.AddSeparator()
        if mode == '3D':
            self.tb.AddSimpleTool(self.ID_AXES, '坐标轴', bmp_axes, '显示/隐藏坐标轴')
            self.tb.AddSimpleTool(self.ID_GRID, '网格', bmp_grid, '显示/隐藏网格')
        self.tb.AddSimpleTool(self.ID_ARGS, '背景', bmp_args, '设置背景颜色')
        self.tb.AddSeparator()
        self.tb.AddSimpleTool(self.ID_SAVE, '保存', bmp_save, '保存为文件')
        self.tb.Realize()
        
        self.scene = scene.WxGLScene(self, head=head, zoom=zoom, mode=mode, elevation=elevation, azimuth=azimuth, style=style)
        
        self._mgr = aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        self._mgr.AddPane(self.scene, aui.AuiPaneInfo().Name('Scene').CenterPane().Show())
        self._mgr.AddPane(self.tb, aui.AuiPaneInfo().Name('ToolBar').ToolbarPane().Bottom().Floatable(False))
        self._mgr.Update()
        
        self.Bind(wx.EVT_MENU, self.on_restore, id=self.ID_RESTORE)
        self.Bind(wx.EVT_MENU, self.on_args, id=self.ID_ARGS)
        self.Bind(wx.EVT_MENU, self.on_save, id=self.ID_SAVE)
        
        if mode == '3D':
            self.Bind(wx.EVT_MENU, self.on_axes, id=self.ID_AXES)
            self.Bind(wx.EVT_MENU, self.on_grid, id=self.ID_GRID)
        
        # 创建axes视区，并添加部件
        if mode == '3D':
            self.xyz = self.scene.add_region((0,0,0.15,0.15))
            self.xyz.coordinate(name='xyz')
        
        self.xyz_visible = True
        self.grid_visible = False
    
    def on_restore(self, evt):
        """回到初始状态"""
        
        self.scene.reset_posture()
    
    def on_axes(self, evt):
        """显示/隐藏坐标轴"""
        
        self.xyz_visible = not self.xyz_visible
        self.xyz.set_model_visible('xyz', self.xyz_visible)
        self.xyz.refresh()
    
    def on_grid(self, evt):
        """显示/隐藏网格"""
        
        self.grid_visible = not self.grid_visible
        for ax in self.parent.subgraphs:
            if ax.reg_main.grid_tick:
                ax.reg_main.hide_ticks()
            else:
                ax.reg_main.ticks(**ax.reg_main.grid_tick_kwds)
    
    def on_args(self, evt):
        """调整参数"""
        
        self.scene.set_style('white')
        self.scene.init_gl()
        
        for rid in self.scene.regions:
            reg = self.scene.regions[rid]
            reg.assembly = dict()
            reg.models = dict()
        
        self.parent.draw()
        
        if self.scene.mode == '3D':
            self.xyz.coordinate(name='xyz')
            if not self.xyz_visible:
                self.xyz.set_model_visible('xyz', False)
                self.xyz.refresh()
            
            if self.grid_visible:
                for ax in self.parent.subgraphs:
                    ax.reg_main.show_ticks()
    
    def on_save(self, evt):
        """保存为文件"""
        
        dlg = wx.FileDialog(self, 
            message = "保存为文件...", 
            defaultDir = os.getcwd(),
            defaultFile = "", 
            wildcard = 'PNG (*.png)|*.png|JPG (*.jpg)|*.jpg',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            fn = dlg.GetPaths()[0]
            self.scene.save_scene(fn, alpha=True, buffer='FRONT')
        
        dlg.Destroy()
        

class Figure:
    """wxplot的API"""
    
    def __init__(self, size=(800,600), **kwds):
        """构造函数
        
        size        - 画布分辨率
        kwds        - 关键字参数
                        head        - 定义方向：'x+'|'y+'|'z+'
                        zoom        - 视口缩放因子
                        mode        - 2D/3D模式
                        elevation   - 仰角
                        azimuth     - 方位角
                        style       - 场景风格，'black'|'white'|'gray'
        """
        
        for key in kwds:
            if key not in ['head', 'zoom', 'mode', 'elevation', 'azimuth', 'style']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        if 'head' not in kwds:
            kwds.update({'head':'z+'})
        if 'zoom' not in kwds:
            kwds.update({'zoom':1.0})
        if 'mode' not in kwds:
            kwds.update({'mode':'3D'})
        if 'elevation' not in kwds:
            kwds.update({'elevation':10})
        if 'azimuth' not in kwds:
            kwds.update({'azimuth':30})
        if 'style' not in kwds:
            kwds.update({'style':'black'})
        
        self.size = size
        self.kwds = kwds
        
        self.cm = colormap.WxGLColorMap()
        self.app = None
        self.ff = None
        self.curr_ax = None
        self.assembly = list()
        self.subgraphs = list()
    
    def create_frame(self):
        """生成窗体"""
        
        if not self.app:
            self.app = wx.App()
        
        if not self.ff:
            self.ff = FigureFrame(self, size=self.size, **self.kwds)
            self.curr_ax = None
            self.assembly = list()
            self.subgraphs = list()
    
    def destroy_frame(self):
        """销毁窗体"""
        
        self.app.Destroy()
        
        del self.ff
        del self.app
        
        self.app = None
        self.ff = None
    
    def draw(self):
        """绘制"""
        
        for item in self.assembly:
            getattr(item[0], item[1])(*item[2], **item[3])
        
        if self.ff.scene.mode == '2D':
            for ax in self.subgraphs:
                ax.reg_main.ticks2d()
    
    def show(self):
        """显示画布"""
        
        self.create_frame()
        self.draw()
        self.ff.Show()
        self.app.MainLoop()
        self.destroy_frame()
    
    def savefig(self, fn, alpha=False):
        """保存画布为文件
        
        fn          - 文件名
        alpha       - 背景是否透明
        """
        
        self.create_frame()
        self.draw()
        self.ff.Show()
        self.ff.scene.save_scene(fn, alpha=alpha)
        self.ff.Destroy()
        self.destroy_frame()
    
    def add_axes(self, pos, padding=(20,20,20,20)):
        """添加子图
        
        pos         - 三个数字组成的字符串或四元组，表示子图在场景中的位置和大小
        padding     - 四元组，上、右、下、左四个方向距离边缘的留白像素
        """
        
        self.create_frame()
        ax = self.ff.scene.add_axes(pos, padding=padding)
        self.subgraphs.append(ax)
        self.curr_ax = ax
        
        return ax
    
    def add_widget(self, reg, func, *args, **kwds):
        """添加部件"""
        
        self.assembly.append([reg, func, list(args), kwds])
        
# -*- coding: utf-8 -*-

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
        
        icon = wx.Icon(os.path.join(BASE_PATH, 'res', 'wxgl.ico'))
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
        
        choices = ['暗黑', '纯白', '浅灰', '幽蓝']
        styles = ['black', 'white', 'gray', 'blue']
        dlg = wx.SingleChoiceDialog(self, '请选择配色方案', '设置背景颜色', choices, wx.CHOICEDLG_STYLE)
        dlg.SetSelection(styles.index(self.scene.style))
        
        if dlg.ShowModal() == wx.ID_OK:
            style = styles[choices.index(dlg.GetStringSelection())]
            if style != self.scene.style:
                self.scene.set_style(style)
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
        dlg.Destroy()
    
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
    
    def show(self, rotation=None, **kwds):
        """显示画布
        
        rotation    - 旋转模式
                        None        - 无旋转
                        'h+'        - 水平顺时针旋转（默认方式）
                        'h-'        - 水平逆时针旋转
                        'v+'        - 垂直前翻旋转
                        'v-'        - 垂直后翻旋转
        kwds        - 关键字参数
                        elevation   - 初始仰角，以度（°）为单位，默认值为0
                        azimuth     - 初始方位角以度（°）为单位，默认值为0
                        step        - 帧增量，以度（°）为单位，默认值为5
                        interval    - 帧间隔，以ms为单位，默认值为20
        """
        
        self.create_frame()
        try:
            self.draw()
            self.ff.Show()
            if rotation:
                self.ff.scene.auto_rotate(rotation=rotation, **kwds)
        except Exception as e:
            print(str(e))
        finally:
            self.app.MainLoop()
            self.destroy_frame()
    
    def savefig(self, fn, alpha=False):
        """保存画布为文件
        
        fn          - 文件名
        alpha       - 透明通道开关
        """
        
        self.create_frame()
        try:
            self.draw()
            self.ff.Show()
            self.ff.scene.save_scene(fn, alpha=alpha)
        except Exception as e:
            print(str(e))
        finally:
            self.ff.Destroy()
            self.destroy_frame()
    
    def add_axes(self, pos, padding=(20,20,20,20)):
        """添加子图
        
        pos         - 子图在场景中的位置和大小
                        三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                        四元组      - 以画布左下角为原点，宽度和高度都是1。四元组分别表示子图左下角在画布上的水平、垂直位置和宽度、高度
        padding     - 四元组，上、右、下、左四个方向距离边缘的留白像素
        """
        
        self.create_frame()
        ax = self.ff.scene.add_axes(pos, padding=padding)
        self.subgraphs.append(ax)
        self.curr_ax = ax
        
        return ax
    
    def cmap(self, *args, **kwds):
        """数值颜色映射
        
        data        - 数据
        cm          - 颜色映射表名
        kwds        - 关键字参数
                        invalid     - 无效数据的标识
                        invalid_c   - 无效数据的颜色
                        datamax     - 数据最大值，默认为None
                        datamin     - 数据最小值，默认为None
                        alpha       - 透明度，None表示返回RGB格式
        """
        
        return self.cm.cmap(*args, **kwds)
    
    def add_widget(self, reg, func, *args, **kwds):
        """添加部件"""
        
        self.assembly.append([reg, func, list(args), kwds])
        
# -*- coding: utf-8 -*-

import os
import uuid
import wx
import wx.lib.agw.aui as aui
import numpy as np

from . import scene
from . import cm


BASE_PATH = os.path.dirname(__file__)


class WxGLFrame(wx.Frame):
    """"""
    
    ID_RESTORE = wx.NewIdRef()      # 恢复初始姿态
    ID_PAUSE = wx.NewIdRef()        # 坐标轴
    ID_GRID = wx.NewIdRef()         # 网格
    ID_STYLE = wx.NewIdRef()        # 设置
    ID_SAVE = wx.NewIdRef()         # 保存
    
    id_white = wx.NewIdRef()
    id_black = wx.NewIdRef()
    id_gray = wx.NewIdRef()
    id_blue = wx.NewIdRef()
    
    def __init__(self, parent, size, **kwds):
        """构造函数"""
        
        wx.Frame.__init__(self, None, -1, 'wxPlot', style=wx.DEFAULT_FRAME_STYLE)
        self.parent = parent
        self.SetSize(size)
        self.Center()
        
        icon = wx.Icon(os.path.join(BASE_PATH, 'res', 'wxgl.ico'))
        self.SetIcon(icon)
        
        self.scene = scene.WxGLScene(self, **kwds)
        
        bmp_save = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_save.png'), wx.BITMAP_TYPE_ANY)
        bmp_style = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_style.png'), wx.BITMAP_TYPE_ANY)
        bmp_grid = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_grid.png'), wx.BITMAP_TYPE_ANY)
        bmp_pause = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_pause.png'), wx.BITMAP_TYPE_ANY)
        bmp_restore = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_restore.png'), wx.BITMAP_TYPE_ANY)
        
        self.tb = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize)
        self.tb.SetToolBitmapSize(wx.Size(32, 32))
        
        self.tb.AddSimpleTool(self.ID_RESTORE, '复位', bmp_restore, '恢复初始姿态')
        self.tb.AddSimpleTool(self.ID_SAVE, '保存', bmp_save, '保存为文件')
        self.tb.AddSeparator()
        self.tb.AddSimpleTool(self.ID_STYLE, '背景', bmp_style, '设置背景颜色')
        self.tb.AddSeparator()
        self.tb.AddSimpleTool(self.ID_GRID, '显示/隐藏', bmp_grid, '显示/隐藏网格')
        self.tb.AddSimpleTool(self.ID_PAUSE, '暂停/启动', bmp_pause, '暂停/启动（动画、旋转等动态显示）')
        
        self.tb.SetToolDropDown(self.ID_STYLE, True)
        self.tb.Realize()
        
        self._mgr = aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        self._mgr.AddPane(self.scene, aui.AuiPaneInfo().Name('Scene').CenterPane().Show())
        self._mgr.AddPane(self.tb, aui.AuiPaneInfo().Name('ToolBar').ToolbarPane().Bottom().Floatable(False))
        self._mgr.Update()
        
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.on_style, id=self.ID_STYLE)
        
        self.Bind(wx.EVT_MENU, self.on_save, id=self.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_style, id=self.ID_STYLE)
        self.Bind(wx.EVT_MENU, self.on_pause, id=self.ID_PAUSE)
        self.Bind(wx.EVT_MENU, self.on_restore, id=self.ID_RESTORE)
        self.Bind(wx.EVT_MENU, self.on_grid, id=self.ID_GRID)
        
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_white)
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_black)
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_gray)
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_blue)
    
    def on_color(self, evt):
        """选择风格"""
        
        idx = evt.GetId()
        if idx == self.id_black.Id:
            color = 'black'
        elif idx == self.id_gray.Id:
            color = 'gray'
        elif idx == self.id_blue.Id:
            color = 'blue'
        else:
            color = 'white'
        
        self.scene.set_style(color)
        self.parent.redraw()
        self.scene.Refresh(False)
    
    def on_style(self, evt):
        """设置背景颜色"""
        
        tb = evt.GetEventObject()
        tb.SetToolSticky(evt.GetId(), True)
        
        submenu = wx.Menu()
        bmp = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'item_16.png'), wx.BITMAP_TYPE_ANY)

        m1 =  wx.MenuItem(submenu, self.id_white, "白色背景")
        m1.SetBitmap(bmp)
        submenu.Append(m1)

        m2 =  wx.MenuItem(submenu, self.id_black, "黑色背景")
        m2.SetBitmap(bmp)
        submenu.Append(m2)

        m3 =  wx.MenuItem(submenu, self.id_gray, "浅灰色背景")
        m3.SetBitmap(bmp)
        submenu.Append(m3)

        m4 =  wx.MenuItem(submenu, self.id_blue, "深蓝色背景")
        m4.SetBitmap(bmp)
        submenu.Append(m4)

        self.PopupMenu(submenu)
        tb.SetToolSticky(evt.GetId(), False)
        
    def on_resize(self, evt):
        """响应窗口尺寸改变事件"""
        
        #self.parent.redraw()
        #self.scene.Refresh(False)
        
        evt.Skip()
    
    def on_restore(self, evt):
        """回到初始状态"""
        
        self.scene.restore_posture()
    
    def on_grid(self, evt):
        """显示/隐藏坐网格"""
        
        self.scene.set_grid_visible()
    
    def on_pause(self, evt):
        """暂停/启动"""
        
        self.scene.pause_sys_timer()
    
    def on_save(self, evt):
        """保存为文件"""
        
        wildcard = 'PNG files (*.png)|*.png|JPEG file (*.jpg)|*.jpg'
        dlg = wx.FileDialog(self, message='保存为文件', defaultDir=os.getcwd(), defaultFile="", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        dlg.SetFilterIndex(0)
        
        if dlg.ShowModal() == wx.ID_OK:
            fn = dlg.GetPath()
            alpha = os.path.splitext(fn)[-1] == '.png'
            self.scene.save_scene(fn, alpha=alpha)
        
        dlg.Destroy()


class WxGLFigure:
    """wxplot的API"""
    
    def __init__(self, size=(800,600), **kwds):
        """构造函数
        
        size        - 画布分辨率
        kwds        - 关键字参数
                        dist        - 相机位置与目标点位之间的距离
                        view        - 视景体
                        elevation   - 仰角
                        azimuth     - 方位角
        """
        
        for key in kwds:
            if key not in ['dist', 'view', 'elevation', 'azimuth']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        self.size = size
        self.kwds = kwds
        
        self.app = None
        self.ff = None
        self.cm = cm.ColorManager()
        self.curr_ax = None
        self.assembly = list()
        self.subgraphs = list()
        
        self._create_frame()
    
    def _create_frame(self):
        """生成窗体"""
        
        if not self.app:
            self.app = wx.App()
        
        if not self.ff:
            self.ff = WxGLFrame(self, size=self.size, **self.kwds)
            self.curr_ax = None
            self.assembly = list()
            self.subgraphs = list()
    
    def _destroy_frame(self):
        """销毁窗体"""
        
        self.app.Destroy()
        
        del self.ff
        del self.app
        
        self.app = None
        self.ff = None
    
    def _draw(self):
        """绘制"""
        
        for item in self.assembly:
            getattr(item[0], item[1])(*item[2], **item[3])
        
        for ax in self.subgraphs:
            if self.ff.scene.mode == '2D':
                ax.reg_main.ticks2d()
            else:
                ax.reg_main.ticks3d()
    
    def redraw(self):
        """重新绘制"""
        
        for reg in self.ff.scene.regions:
            reg.reset()
        
        self._draw()
    
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
        
        self._create_frame()
        try:
            self._draw()
            self.ff.Show()
        except Exception as e:
            print(str(e))
        finally:
            self.app.MainLoop()
            self._destroy_frame()
    
    def savefig(self, fn, alpha=False):
        """保存画布为文件
        
        fn          - 文件名
        alpha       - 透明通道开关
        """
        
        self._create_frame()
        try:
            self._draw()
            self.ff.Show()
            self.ff.scene.save_scene(fn, alpha=alpha)
        except Exception as e:
            print(str(e))
        finally:
            self.ff.Destroy()
            self._destroy_frame()
    
    def add_axes(self, pos, padding=(20,20,20,20)):
        """添加子图
        
        pos         - 子图在场景中的位置和大小
                        三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                        四元组      - 以画布左下角为原点，宽度和高度都是1。四元组分别表示子图左下角在画布上的水平、垂直位置和宽度、高度
        padding     - 四元组，上、右、下、左四个方向距离边缘的留白像素
        """
        
        self._create_frame()
        self.curr_ax = self.ff.scene.add_axes(pos, padding=padding)
        self.subgraphs.append(self.curr_ax)
    
    def add_widget(self, reg, func, *args, **kwds):
        """添加部件"""
        
        self.assembly.append([reg, func, list(args), kwds])
        
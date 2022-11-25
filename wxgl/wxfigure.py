#!/usr/bin/env python3

import wx
import wx.lib.agw.aui as aui
from wx.lib.embeddedimage import PyEmbeddedImage

from . wxscene import WxScene
from . import imgres

class WxFigure(wx.Frame):
    """基于wx的画布类"""

    ID_RESTORE = wx.NewIdRef()  # 相机复位
    ID_SAVE = wx.NewIdRef()     # 保存
    ID_ANIMATE = wx.NewIdRef()  # 动画播放/暂停

    def __init__(self, scheme, **kwds):
        """构造函数

        kwds        - 关键字参数
            size        - 窗口分辨率，默认960×640
            bg          - 画布背景色，默认(0.0, 0.0, 0.0)
            haxis       - 高度轴，默认y轴，可选z轴，不支持x轴
            fovy        - 相机水平视野角度，默认50°
            azim        - 方位角，默认0°
            elev        - 高度角，默认0°
            azim_range  - 方位角变化范围，默认-180°～180°
            elev_range  - 高度角变化范围，默认-180°～180°
            smooth      - 直线和点的反走样，默认True
        """
 
        self.app = wx.App()

        size = kwds.get('size', (960,640))
        wx.Frame.__init__(self, None, -1, 'GLTK', size=size, style=wx.DEFAULT_FRAME_STYLE)
 
        self.SetIcon(PyEmbeddedImage(imgres.data['appicon']).GetIcon())
        self.Center()

        bmp_save = PyEmbeddedImage(imgres.data['save']).GetBitmap()
        bmp_home = PyEmbeddedImage(imgres.data['home']).GetBitmap()
        self.bmp_play = PyEmbeddedImage(imgres.data['play']).GetBitmap()
        self.bmp_pause = PyEmbeddedImage(imgres.data['pause']).GetBitmap()
 
        self.tb = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, agwStyle=aui.AUI_TB_OVERFLOW|aui.AUI_TB_VERTICAL)
        self.tb.SetToolBitmapSize(wx.Size(32, 32))
 
        self.tb.AddSimpleTool(self.ID_SAVE, '保存', bmp_save, '保存画布')
        self.tb.AddSimpleTool(self.ID_RESTORE, '复位', bmp_home, '初始位置')
        self.tb.AddSimpleTool(self.ID_ANIMATE, '动画', self.bmp_play, '动画', kind=aui.ITEM_CHECK)
 
        if scheme.animate:
            self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_pause)
            self.tb.SetToolShortHelp(self.ID_ANIMATE, '暂停')
        else:
            self.tb.EnableTool(self.ID_ANIMATE, False)

        self.tb.Realize()
        self.sb = self.CreateStatusBar()
        self.scene = WxScene(self, scheme, **kwds)

        self._mgr = aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        self._mgr.AddPane(self.scene, aui.AuiPaneInfo().Name('Scene').CenterPane().Show())
        self._mgr.AddPane(self.tb, aui.AuiPaneInfo().Name('ToolBar').ToolbarPane().Left())
        self._mgr.Update()

        self.Bind(wx.EVT_MENU, self.on_home, id=self.ID_RESTORE)
        self.Bind(wx.EVT_MENU, self.on_save, id=self.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_pause, id=self.ID_ANIMATE)

    def on_home(self, evt):
        """恢复初始位置和姿态"""

        self.scene.home()

    def on_save(self, evt):
        """将缓冲区保存为图像文件"""

        self.scene.save()

    def on_pause(self, evt):
        """动画/暂停"""

        self.scene.pause()

        if self.scene.scheme.animate:
            self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_pause)
            self.tb.SetToolShortHelp(self.ID_ANIMATE, '暂停')
        else:
            self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_play)
            self.tb.SetToolShortHelp(self.ID_ANIMATE, '动画')
        
        self.tb.Realize()

    def loop(self):
        """显示画布，侦听事件"""

        self.Show()
        self.app.MainLoop()


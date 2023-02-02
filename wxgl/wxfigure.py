#!/usr/bin/env python3

import os
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

    def __init__(self, scheme):
        """构造函数"""
 
        size = scheme.kwds.get('size', (960,640))
        wx.Frame.__init__(self, None, -1, 'WxGL', size=size, style=wx.DEFAULT_FRAME_STYLE)
 
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
 
        if scheme.alive:
            self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_pause)
            self.tb.SetToolShortHelp(self.ID_ANIMATE, '暂停')
        else:
            self.tb.EnableTool(self.ID_ANIMATE, False)

        self.tb.Realize()
        self.sb = self.CreateStatusBar()
        self.scene = WxScene(self, scheme, **scheme.kwds)
        
        self.Show()

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

        im = self.scene.get_buffer()

        wildcard = 'PNG files (*.png)|*.png|JPEG file (*.jpg)|*.jpg'
        dlg = wx.FileDialog(self, message='保存为文件', wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        dlg.SetFilterIndex(0)
 
        if dlg.ShowModal() == wx.ID_OK:
            fn = dlg.GetPath()
            name, ext = os.path.splitext(fn)
            
            if ext != '.png' and ext != '.jpg':
                ext = ['.png', '.jpg'][dlg.GetFilterIndex()]

            if ext == '.jpg':
                im.convert('RGB').save('%s%s'%(name, ext))
            else:
                im.save('%s%s'%(name, ext))
        
        dlg.Destroy()

    def on_pause(self, evt):
        """动画/暂停"""

        self.scene.pause()

        if self.scene.playing:
            self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_pause)
            self.tb.SetToolShortHelp(self.ID_ANIMATE, '暂停')
        else:
            self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_play)
            self.tb.SetToolShortHelp(self.ID_ANIMATE, '动画')
        
        self.tb.Realize()

def show_wxfigure(scheme):
    """显示画布"""

    app = wx.App()
    fig = WxFigure(scheme)
    app.MainLoop()
    scheme.reset()


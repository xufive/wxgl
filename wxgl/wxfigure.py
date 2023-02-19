#!/usr/bin/env python3

import os, sys, time
import numpy as np
import threading
import imageio
import wx
import wx.lib.agw.aui as aui
from wx.lib.embeddedimage import PyEmbeddedImage
from . wxscene import WxScene
from . import imgres

if sys.platform.lower() != 'darwin':
    import webp

class WxFigure(wx.Frame):
    """构造函数"""

    ID_RESTORE = wx.NewIdRef()  # 相机复位
    ID_SAVE = wx.NewIdRef()     # 保存
    ID_ANIMATE = wx.NewIdRef()  # 动画播放/暂停

    def __init__(self, scheme, **kwds):
        """构造函数

        scheme      - 展示方案
        kwds        - 关键字参数
            outfile     - 输出文件名
            ext         - 输出文件扩展名
            dpi         - 图像文件每英寸像素数
            fps         - 动画文件帧率
            frames      - 动画文件总帧数
            loop        - gif文件播放次数，0表示循环播放
            quality     - webp文件质量，100表示最高品质
        """
 
        self.outfile = kwds.get('outfile')
        self.ext = kwds.get('ext')
        self.dpi = kwds.get('dpi')
        self.fps = kwds.get('fps')
        self.frames = kwds.get('frames')
        self.loop = kwds.get('loop')
        self.quality = kwds.get('quality')

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
        self.scene.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.scene.Bind(wx.EVT_KEY_UP, self.on_key_up)
        
        if not self.outfile is None:
            self.cn = 0
            threading_record = threading.Thread(target=self.create_file)
            threading_record.setDaemon(True)
            threading_record.start()

    def on_key_down(self, evt):
        """键盘按下"""

        key = evt.GetKeyCode()
        if key == wx.WXK_CONTROL:
            self.scene.ctrl_down = True

    def on_key_up(self, evt):
        """键盘弹起"""

        key = evt.GetKeyCode()
        if key == wx.WXK_CONTROL:
            self.scene.ctrl_down = False
        elif key == wx.WXK_ESCAPE:
            wx.CallAfter(self.scene.home)

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

    def create_file(self):
        """生成图像或动画文件的线程函数"""
 
        self.scene.increment = False
        self.scene.duration = 0
        ft = round(1000/self.fps)

        self.scene.Refresh(False)
        while not self.scene.gl_init_done:
            time.sleep(0.01)

        if self.ext in ('.png', '.jpg', '.jpeg'):
            self.scene.duration = 0
            time.sleep(0.01)

            self.scene.painted = False
            self.scene.Refresh(False)
            while not self.scene.painted:
                time.sleep(0.01)

            self.scene.im_pil = None
            wx.CallAfter(self.scene.capture, mode='RGBA' if self.ext=='.png' else 'RGB')
            while self.scene.im_pil is None:
                time.sleep(0.01)

            if isinstance(self.dpi, (int, float)):
                self.scene.im_pil.save(self.outfile, dpi=(self.dpi, self.dpi))
            else:
                self.scene.im_pil.save(self.outfile)
        elif self.ext == '.webp':
            enc = webp.WebPAnimEncoder.new(*self.scene.csize)
            cfg = webp.WebPConfig.new(quality=100)
            timestamp_ms = 0
            while self.cn < self.frames:
                self.scene.duration = self.cn * ft
                time.sleep(0.01)

                self.scene.painted = False
                self.scene.Refresh(False)
                while not self.scene.painted:
                    time.sleep(0.01)

                self.scene.im_pil = None
                wx.CallAfter(self.scene.capture)
                while self.scene.im_pil is None:
                    time.sleep(0.01)

                pic = webp.WebPPicture.from_pil(self.scene.im_pil)
                enc.encode_frame(pic, timestamp_ms, cfg)
                timestamp_ms += ft
                self.cn += 1

            anim_data = enc.assemble(timestamp_ms)
            with open(self.outfile, 'wb') as fp:
                fp.write(anim_data.buffer())
        else:
            if self.ext == '.gif':
                writer = imageio.get_writer(self.outfile, fps=self.fps, loop=self.loop)
                crop = False
            else:
                writer = imageio.get_writer(self.outfile, fps=self.fps)
                crop = True
 
            while self.cn < self.frames:
                self.scene.duration = self.cn * ft
                time.sleep(0.01)

                self.scene.painted = False
                self.scene.Refresh(False)
                while not self.scene.painted:
                    time.sleep(0.01)

                self.scene.im_pil = None
                wx.CallAfter(self.scene.capture, crop=crop)
                while self.scene.im_pil is None:
                    time.sleep(0.01)
 
                im = np.array(self.scene.im_pil)
                writer.append_data(im)
                self.cn +=1
 
            writer.close()

        wx.CallAfter(self.Close)

def show_wxfigure(scheme, **kwds):
    """保存画布为图像文件或动画文件

    kwds        - 关键字参数
        outfile     - 输出文件名
        ext         - 输出文件扩展名
        dpi         - 图像文件每英寸像素数
        fps         - 动画文件帧率
        frames      - 动画文件总帧数
        loop        - gif文件播放次数，0表示循环播放
        quality     - webp文件质量，100表示最高品质
    """

    app = wx.App()
    fig = WxFigure(scheme, **kwds)
    app.MainLoop()
    app.Destroy()
    scheme.reset()


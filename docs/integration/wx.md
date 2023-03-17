---
sort: 1
---

# 与wxPython集成

场景类wxgl.wxscene.WxScene是wx.glcanvas.GLCanvas的派生类，因此可以无缝地在wxPython中使用该类。三维绘图功能封装在wxgl.Scheme中，只需要将一个Scheme类实例传到场景类中即可显示三维绘图结果。

```python
import os
import wx
import numpy as np
import wxgl

class MainFrame(wx.Frame):
    """桌面程序主窗口类"""
 
    def __init__(self):
        """构造函数"""
 
        wx.Frame.__init__(self, None, -1, '在WxPython中使用WxGL', size=(1200,800), style=wx.DEFAULT_FRAME_STYLE)
        self.Center()
        self.SetBackgroundColour((224, 224, 224))

        self.scene = wxgl.wxscene.WxScene(self, self.draw())
        self.visible = True

        btn_home = wx.Button(self, -1, '复位', size=(100, -1))
        btn_animate = wx.Button(self, -1, '启动/停止', size=(100, -1))
        btn_visible = wx.Button(self, -1, '隐藏/显示', size=(100, -1))
        btn_save = wx.Button(self, -1, '保存', size=(100, -1))

        sizer_btn = wx.BoxSizer(wx.VERTICAL)
        sizer_btn.Add(btn_home, 0, wx.TOP|wx.BOTTOM, 20)
        sizer_btn.Add(btn_animate, 0, wx.TOP|wx.BOTTOM, 20)
        sizer_btn.Add(btn_visible, 0, wx.TOP|wx.BOTTOM, 20)
        sizer_btn.Add(btn_save, 0, wx.TOP|wx.BOTTOM, 20)

        sizer_max = wx.BoxSizer()
        sizer_max.Add(self.scene, 1, wx.EXPAND|wx.LEFT|wx.TOP|wx.BOTTOM, 5)
        sizer_max.Add(sizer_btn, 0, wx.ALL, 20)
        
        self.SetAutoLayout(True)
        self.SetSizer(sizer_max)
        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.on_home, btn_home)
        self.Bind(wx.EVT_BUTTON, self.on_animate, btn_animate)
        self.Bind(wx.EVT_BUTTON, self.on_visible, btn_visible)
        self.Bind(wx.EVT_BUTTON, self.on_save, btn_save)

    def draw(self):
        """绘制网格球和圆柱的组合体"""

        tf = lambda t : ((0, 1, 0, (0.03*t)%360), )
        sch = wxgl.Scheme()
        sch.sphere((0,0,0), 1, fill=False)
        sch.cylinder((-1.2,0,0), (1.2,0,0), 0.3, color='cyan', transform=tf, name='cudgel')
        sch.circle((-1.2,0,0), 0.3, vec=(-1,0,0), color='cyan', transform=tf, name='cudgel')
        sch.circle((1.2,0,0), 0.3, vec=(1,0,0), color='cyan', transform=tf, name='cudgel')
        sch.axes()
        
        return sch

    def on_home(self, evt):
        """点击复位按钮"""

        self.scene.home()

    def on_animate(self, evt):
        """点击启动/停止按钮"""

        self.scene.pause()

    def on_visible(self, evt):
        """点击隐藏/显示按钮"""

        self.visible = not self.visible
        self.scene.set_visible('cudgel', self.visible)

    def on_save(self, evt):
        """点击保存按钮"""

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

if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
```


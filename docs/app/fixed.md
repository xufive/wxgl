---
sort: 2
---

# 锁定视区

一个场景可以创建多个视区。标题或Colorbar，可以绘制在一个锁定的（fixed）视区上——模型不能缩放，也不响应拖拽操作。

```python
import wx
import numpy as np
import wxgl

class mainFrame(wx.Frame):
    """程序主窗口类，继承自wx.Frame"""

    def __init__(self):
        """构造函数"""

        wx.Frame.__init__(self, None, -1, 'WxGL项目演示', style=wx.DEFAULT_FRAME_STYLE)
        self.Maximize()
        self.SetBackgroundColour(wx.Colour(240,240,240))
        
        self.scene = wxgl.Scene(self) # 创建场景
        self.reg = self.scene.add_region((0,0,0.8,1)) # 添加视区
        self.cb = self.scene.add_region((0.8,0,0.2,1), fixed=True) # 添加fixed视区
                
        self.draw_mesh()
        self.draw_colorbar()
    
    def draw_mesh(self):
        """网格模型"""
        
        # 生成球面网格数据
        lats, lons = np.mgrid[90:-90:91j, -180:180:180j]
        lats, lons = np.radians(lats), np.radians(lons)
        zs = np.cos(lats)*np.cos(lons)
        xs = np.cos(lats)*np.sin(lons)
        ys = np.sin(lats)
        
        # 生成纹理
        texture = wxgl.Texture('res/earth.jpg') 
        
        self.reg.mesh(xs, ys, zs, texture=texture) # 绘制网格面
        self.reg.grid() # 绘制坐标网格
    
    def draw_colorbar(self):
        """Colorbar"""
        
        box = np.array([[-0.9,2],[-0.9,-2.5],[-0.5,2],[-0.5,-2.5]])
        self.cb.colorbar('hsv', (-50, 100), box, subject='温度')
        
    
if __name__ == "__main__":
    app = wx.App()
    frame = mainFrame()
    frame.Show(True)
    app.MainLoop()
```


---
sort: 1
---

# 单个视区

这段代码演示了wx.Frame和wxgl.Scene的集成方法。调用wxgl.Scene.add_region方法添加视区（wxgl.Region对象），而绘制网格面（mesh）和绘制坐标网格（grid）都是wxgl.Region对象的方法。

```
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
        self.reg = self.scene.add_region((0,0,1,1)) # 添加视区
                
        self.draw_mesh()
    
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
    
if __name__ == "__main__":
    app = wx.App()
    frame = mainFrame()
    frame.Show(True)
    app.MainLoop()
```


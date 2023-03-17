# WxGL

[![PyPI Version](https://img.shields.io/pypi/v/wxgl?color=orange)](https://pypi.python.org/pypi/wxgl/)
[![Downloads](https://pepy.tech/badge/wxgl)](https://pepy.tech/project/wxgl)
[![Downloads](https://pepy.tech/badge/wxgl/month)](https://pepy.tech/project/wxgl)
[![Downloads](https://pepy.tech/badge/wxgl/week)](https://pepy.tech/project/wxgl)

WxGL是一个基于PyOpenGL的跨平台三维数据快速可视化工具包，提供类似Matplotlib风格的应用方式。WxGL也可以集成到wxPython或PyQt6中实现更多的功能和控制。

[项目地址](https://github.com/xufive/wxgl)

[中文文档](https://xufive.github.io/wxgl/)

# 安装

```shell
pip install wxgl
```

# 快速体验

下面这几行代码，绘制了一个半径为1的地球，并以20°/s的角速度绕地轴自转。配合太阳光照效果和模型动画，可以清晰地看到晨昏分界线的变化。这段代码在example路径下有更详细的说明。

```python
import numpy as np
import wxgl

r = 1 # 地球半径
gv, gu = np.mgrid[np.pi/2:-np.pi/2:91j, 0:2*np.pi:361j] # 纬度和经度网格
xs = r * np.cos(gv)*np.cos(gu)
ys = r * np.cos(gv)*np.sin(gu)
zs = r * np.sin(gv)

light = wxgl.SunLight(direction=(-1,1,0), ambient=(0.1,0.1,0.1)) # 太阳光照向左前方，暗环境光
tf = lambda t : ((0, 0, 1, (0.02*t)%360), ) # 以20°/s的角速度绕y逆时针轴旋转

app = wxgl.App(haxis='z') # 以z轴为高度轴
app.title('自转的地球')
app.mesh(xs, ys, zs, texture='res/earth.jpg', light=light, transform=tf)
app.show()
```


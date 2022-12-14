# WxGL

[![PyPI Version](https://img.shields.io/pypi/v/wxgl?color=orange)](https://pypi.python.org/pypi/wxgl/)
[![Downloads](https://pepy.tech/badge/wxgl)](https://pepy.tech/project/wxgl)
[![Downloads](https://pepy.tech/badge/wxgl/month)](https://pepy.tech/project/wxgl)
[![Downloads](https://pepy.tech/badge/wxgl/week)](https://pepy.tech/project/wxgl)
[![](https://img.shields.io/badge/blog-@xufive-blueviolet.svg)](https://xufive.blog.csdn.net/)

WxGL是一个基于PyOpenGL的跨平台三维数据绘图工具包，提供类似Matplotlib风格的应用方式。WxGL也可以集成到wxPython和PyQt6中实现更多的功能和控制。

[项目地址](https://github.com/xufive/wxgl)

[中文文档](https://xufive.github.io/wxgl/)

# 安装

```shell
pip install wxgl
```

# 快速体验

下面这几行代码，绘制了一个半径为1的地球，并以20°/s的角速度绕地轴自转。配合太阳光照效果和模型动画，可以清晰地看到晨昏分界线的变化。这段代码在example路径下有更详细的说明。

```python
import wxgl
tf = lambda t : ((0, 1, 0, (0.02*t)%360), ) # 以渲染时长t（单位：ms）为参数的模型变换函数
light = wxgl.SunLight(direction=(-1,0,-1), ambient=(0.1,0.1,0.1)) # 太阳光线从右后方照射过来
app = wxgl.App()
app.title('自转的地球')
app.uvsphere((0,0,0), 1, texture='res/earth.jpg', light=light, transform=tf)
app.show()
```


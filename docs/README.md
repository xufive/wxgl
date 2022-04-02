# WxGL

[![PyPI Version](https://img.shields.io/pypi/v/wxgl?color=orange)](https://pypi.python.org/pypi/wxgl/)
[![Downloads](https://pepy.tech/badge/wxgl)](https://pepy.tech/project/wxgl)
[![Downloads](https://pepy.tech/badge/wxgl/month)](https://pepy.tech/project/wxgl)
[![Downloads](https://pepy.tech/badge/wxgl/week)](https://pepy.tech/project/wxgl)
[![](https://img.shields.io/badge/blog-@xufive-blueviolet.svg)](https://xufive.blog.csdn.net/)

WxGL是一个基于PyOpenGL的三维数据绘图工具包，以wx为显示后端，提供Matplotlib风格的应用方式。WxGL也可以和wxPython无缝结合，在wx的窗体上绘制三维模型。

[项目地址](https://github.com/xufive/wxgl)

[中文文档](https://xufive.github.io/wxgl/)

# 安装

```
pip install wxgl
```

# 快速体验

* 一个中心在三维坐标系原点半径为1的纯色圆球。忽略模块名的话，这些代码和Matplotlib的风格几乎是完全一致的。

```python
import wxgl.glplot as glt

glt.title('快速体验：$x^2+y^2+z^2=1$')
glt.uvsphere((0,0,0), 1, color='cyan')
glt.show()
```

* 阳光下的球环。除了glplot子模块，WxGL还内置了灯光、纹理等子模块，以及常量和工具函数。

```python
import wxgl
import wxgl.glplot as glt

light = wxgl.SunLight(roughness=0, metalness=0, shininess=0.5)

glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=light)
glt.grid()
glt.show()
```

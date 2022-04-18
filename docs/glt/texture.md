---
sort: 15
---

# 纹理

WxGL的纹理类[wxgl.Texture](https://xufive.github.io/wxgl/api/texture.html)支持1D纹理、2D纹理、3D纹理和2D纹理数组，接受图片文件和8位无符号整形数组作为纹理资源，允许用户定制纹理滤波参数、S/T/R方向的铺贴方式，还可选择是否在x/y方向反转纹理图像。

下面的代码演示了2D纹理的应用方法，所有参数均使用默认值。代码中的纹理图片在GitHub本项目的example路径下。

```python
import numpy as np
import wxgl
import wxgl.glplot as glt

tx = wxgl.Texture('res/earth.jpg')

r = 1
lats, lons = np.mgrid[90:-90:91j, 0:360:181j]
ys = r * np.sin(np.radians(lats))
xs = r * np.cos(np.radians(lats)) * np.cos(np.radians(lons))
zs = -r * np.cos(np.radians(lats)) * np.sin(np.radians(lons))

glt.mesh(xs, ys, zs, texture=tx)
glt.show()
```

[doc_texture.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/doc_texture.jpg)


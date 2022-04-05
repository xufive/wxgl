---
sort: 8
---

# 定制轴名称和轴刻度

坐标网格和坐标轴刻度函数[wxgl.glplot.colorbar](https://xufive.github.io/wxgl/api/glplot.html#wxglregiongrid)提供了若干关键字参数，用来定制坐标网格和坐标轴刻度。比如参数xlabel/ylabel/zlabel用于设置坐标轴名称，参数xd/yd/zd用于调整标轴标注密度，参数xf/yf/zf则用于格式化坐标轴的标注。

xf/yf/zf缺省默认以str函数作为格式化函数，用户可以通过自定义函数或lambda函数定制刻度文本的样式。

```pyhton
import numpy as np
import wxgl.glplot as glt

z, x = np.mgrid[1:-1:20j,-1:1:20j]
y = x*x + z*z
glt.mesh(x, y, z, color=y, cm='hsv')

xf = lambda x:'%0.1f°'%(x*50)
yf = lambda y:'%0.3fKm'%y

glt.grid(xlabel='经度', ylabel='高度', zlabel='纬度', yd=2, xf=xf, yf=yf)
glt.show()
```
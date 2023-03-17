---
sort: 6
---

# 三维曲面重建

WxGL实现了基于MarchingCube算法的三维曲面重建。下面例子中使用GitHub本项目example路径下的头部CT图片完成头部三维重建。

```python
import numpy as np
from PIL import Image
import wxgl

layers = list()
for i in range(109): # 读取109张头部CT断层扫描片，只保留透明通道
    im = np.array(Image.open('res/headCT/head%d.png'%i))
    layers.append(np.fliplr(im[...,3]))
data = np.stack(layers, axis=0)

app = wxgl.App(haxis='z', bg='#60e0f0')
app.isosurface(data, data.max()/8, color='#CCC6B0', xr=(-0.65,0.65), yr=(-1,1), zr=(-1,1))
app.title('基于MarchingCube算法的三维重建演示')
app.grid() # 显示网格
app.cruise(lambda t : {'azim':(0.02*t)%360}) # 相机以20°/s的角速度逆时针环绕模型
app.show()
```

![tour_isosurface.png](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/tour_isosurface.png)


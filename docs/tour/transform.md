---
sort: 4
---

# 让模型动起来

通过transform参数传递一个以渲染时长为参数的函数给模型，可以实现复杂的模型动画。该函数返回一个由一系列旋转、位移和缩放动作组成的元组：

**- 旋转用4元组表示，前3个元素是旋转轴，第4个元素是旋转角度，旋转方向遵从右手定则
- 位移用3元组表示，分别表示模型在xyz轴上的位移距离
- 缩放系数用数值表示

下面这几行代码，绘制了一个半径为1的地球，并以20°/s的角速度绕地轴自转。配合太阳光照效果和模型动画，可以清晰地看到晨昏分界线的变化。

```python
import numpy as np
import wxgl

r = 1 # 地球半径
gv, gu = np.mgrid[np.pi/2:-np.pi/2:91j, 0:2*np.pi:361j] # 纬度和经度网格
xs = r * np.cos(gv)*np.cos(gu)
ys = r * np.cos(gv)*np.sin(gu)
zs = r * np.sin(gv)

light = wxgl.SunLight(direction=(-1,1,0), ambient=(0.1,0.1,0.1)) # 太阳光照向左前方，暗环境光
tf = lambda t : ((0, 0, 1, (0.02*t)%360), ) # 以20°/s的角速度绕y逆时针轴旋转（t是以毫秒为单位的渲染时长）

app = wxgl.App(haxis='z') # 以z轴为高度轴
app.title('自转的地球')
app.mesh(xs, ys, zs, texture='res/earth.jpg', light=light, transform=tf)
app.show()
```

![tour_transform.png](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/tour_transform.png)

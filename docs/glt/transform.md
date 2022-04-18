---
sort: 13
---

# 模型变换

调用wxgl.glplot.show函数后，WxGL会启动一个内部计时器，记录以毫秒为单位的渲染时长。通过transform参数传递一个变换函数给模型，可以实现复杂的模型动画。传递给transform的函数，以WxGL内部计时器为参数，返回由旋转、平移和缩放任意组合的元组。

* 旋转用4元组描述，前3个元素为旋转向量，第4个元素为旋转角度，旋转方向遵从右手定则
* 平移用3元组描述，3个元素分别表示模型在x/y/z轴上的平移距离
* 缩放用一个浮点型数值表示

下面的代码在坐标系原点绘制了一大一小两个网格形式的圆球，使用模型变换函数实现了两个球的自转和小球绕大球的公转。

```python
import numpy as np
import wxgl.glplot as glt

tf_1 = lambda t : ((0, 1, 0, (0.01*t)%360),) # 大球自转速度10°/s

def tf_2(t):
    theta = -(0.05*t)%360 # 小球公转和自转都是-50°/s
    rotate = (0, 1, 0, theta) # 小球自转
    theta = np.radians(theta) # 角度转弧度
    r = 1 # 小球公转半径
    shift = (r*np.cos(theta), 0, -r*np.sin(theta)) # 小球公转
    
    return (rotate, shift)

glt.uvsphere((0,0,0), 0.8, fill=False, transform=tf_1)
glt.uvsphere((0,0,0), 0.2, fill=False, transform=tf_2)

glt.show()
```

[doc_tf.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/doc_tf.jpg)


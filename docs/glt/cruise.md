---
sort: 14
---

# 相机巡航

wxgl.glplot的每个子图各自拥有独立的相机，设置相机巡航是对子图对象（Axes）的操作，影响到子图内的所有模型。相机巡航函数[wxgl.glplot.cruise](https://xufive.github.io/wxgl/api/glplot.html#wxglglplotcruise)接受以WxGL内部计时器为参数的函数，该函数返回一个字典，字典可能的键包括：

* azim - 相机方位角
* elev - 相机高度角
* dist - 相机与视点之间的距离

下面的代码演示了相机巡航和模型动画之间的区别。

```python
import wxgl
import wxgl.glplot as glt

cf = lambda t : {'azim':(-0.05*t)%360, 'dist':3.5+5*(t%1000)/1000}
glt.cruise(cf)
glt.uvsphere((0,0,0), 1, fill=False)

glt.show()
```

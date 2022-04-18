---
sort: 1
---

# 熟悉的风格

下面这几行代码，绘制了一个中心在三维坐标系原点半径为1的纯色圆球。忽略模块名的话，这些代码和Matplotlib的风格几乎是完全一致的。

```python
import wxgl.glplot as glt

glt.title('快速体验：$x^2+y^2+z^2=1$')
glt.uvsphere((0,0,0), 1, color='cyan')
glt.show()
```

[readme_01.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/readme_01.jpg)


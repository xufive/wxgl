---
sort: 1
---

# 熟悉的风格

下面这几行代码，绘制了一个中心在三维坐标系原点半径为1的纯色圆球。忽略模块名的话，这些代码和Matplotlib的风格非常相似。

```python
import wxgl

app = wxgl.App()
app.sphere((0,0,0), 1, color='cyan')
app.title('快速体验：$x^2+y^2+z^2=1$')
app.show()
```

![tour_familiar.png](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/tour_familiar.png)


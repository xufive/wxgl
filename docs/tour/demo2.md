---
sort: 2
---

# 子图布局

在一张画布上可以任意放置多个子图。下面的代码演示了子图布局函数subplot的经典用法，代码中的纹理图片在example路径下。

```python
import wxgl
import wxgl.glplot as glt

glt.subplot(121)
glt.title('经纬度网格生成球体')
glt.uvsphere((0,0,0), 1, texture=wxgl.Texture('res/earth.jpg'))
glt.grid()

glt.subplot(122)
glt.title('正八面体迭代细分生成球体')
glt.isosphere((0,0,0), 1, color=(0,1,1), fill=False, iterations=5)
glt.grid()

glt.show()
```

---
sort: 10
---

# 渲染面剔除

由三角面或四角面描述的曲面有前后两个面，三角面或四角面的顶点按逆时针排序的为前面，反之为后面。WxGL默认开启双面渲染。模型的cull参数可以设置单面渲染，剔除无需渲染的一面。

```python
import numpy as np
import wxgl.glplot as glt

#    v6----- v4
#   /|      /|
#  v0------v2|
#  | |     | |
#  | |v7---|-|v5
#  |/      |/
#  v1------v3

vs = np.array([[-1.2,1,1.2],[-1.2,-1,1.2],[1.2,1,1.2],[1.2,-1,1.2],[1.2,1,-1.2],[1.2,-1,-1.2],[-1.2,1,-1.2],[-1.2,-1,-1.2]])
color = np.array([[1,0,0],[1,0,1],[1,1,1],[1,1,0],[0,1,1],[0,1,0],[0,0,0],[0,0,1]])

glt.subplot(121)
glt.title('剔除前面，仅渲染背面')

indices = np.array([0,1,3,2,2,3,5,4,4,5,7,6,6,7,1,0,0,2,4,6,1,7,5,3])
glt.quad(vs, color=color, method='isolate', indices=indices, cull='front')
glt.grid()

glt.subplot(122)
glt.title('剔除背面，仅渲染前面')

indices = np.array([0,1,2,3,4,5,6,7,0,1])
vs = vs[indices]
color = color[indices]
glt.quad(vs, color=color, method='strip', cull='back')
glt.grid()

glt.show()
```

[doc_cull.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/doc_cull.jpg)


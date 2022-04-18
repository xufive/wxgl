---
sort: 6
---

# 子图布局

子图布局函数[wxgl.glplot.subplot](https://xufive.github.io/wxgl/api/glplot.html#wxglglplotsubplot)接受整数参数，字符串参数，也接受4元组参数。

```
import numpy as np
import wxgl
import wxgl.glplot as glt

glt.figure(elev=-20)
    
glt.subplot(221) # 整数参数，表示两行两列的第1个位置（左上）
glt.title('独立三角面方法：isolate', size=80)
vs = np.array([[-1,1,1],[-1,-1,1],[1,1,1],[1,-1,1],[1,1,-1],[1,-1,-1],[-1,1,-1],[-1,-1,-1]])
indices = np.array([0,1,3,0,3,2,2,3,5,2,5,4,4,5,7,4,7,6,6,7,1,6,1,0])
color = np.array([[1,0,0],[1,0,1],[1,1,1],[1,1,0],[0,1,1],[0,1,0],[0,0,0],[0,0,1]])
glt.surface(vs, color=color, indices=indices, method='isolate')
glt.yrange((-1.2, 1.2))

glt.subplot('223') # 字符串参数，表示两行两列的第3个位置（左下）
glt.title('带状三角面方法：strip', size=80)
vs = np.array([[-1,1,1],[-1,-1,1],[1,1,1],[1,-1,1],[1,1,-1],[1,-1,-1],[-1,1,-1],[-1,-1,-1],[-1,1,1],[-1,-1,1]])
color = np.array([[1,0,0],[1,0,1],[1,1,1],[1,1,0],[0,1,1],[0,1,0],[0,0,0],[0,0,1],[1,0,0],[1,0,1]])
glt.surface(vs, color=color, method='strip')
glt.yrange((-1.2, 1.2))

glt.subplot((0.5, 0, 0.5, 1)) # 子图左下角坐标(0.5, 0)，宽度0.5， 高度1，即窗口右半部
glt.title('连续三角面方法：fan')
theta = np.radians(np.linspace(30, 150, 21))
xs, ys, zs = 2*np.cos(theta), 2*np.sin(theta)-0.5, np.zeros(21)
zs[1::2] += 0.2 
vs = np.vstack(((0,-0.8,0), np.stack((xs,ys-0.8,zs), axis=1)))
glt.surface(vs, method='fan', light=wxgl.SphereLight(9), transform=lambda duration:((0, 1, 0, (0.05*duration)%360),))
vs = np.vstack(((0,1.2,0), np.stack((xs,ys+1.2,zs), axis=1)))
glt.surface(vs, method='fan', light=wxgl.SphereLight(9), transform=lambda duration:((0, 1, 0, -(0.05*duration)%360),))

glt.show()
```

![doc_sp.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/doc_sp.jpg)

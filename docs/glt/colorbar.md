---
sort: 7
---

# 多个Colorbar

在一个子图上，可以放置多个Colorbar，位置由Colorbar函数[wxgl.glplot.colorbar](https://xufive.github.io/wxgl/api/glplot.html#wxglglplotcolorbar)的loc参数指定。loc参数只有'right'和'bottom'两个选项，即子图右侧和子图底部。

```
import numpy as np
import wxgl.glplot as glt

vs = np.random.random((300, 3))*2-1
color = np.random.random(300)
size = np.linalg.norm(vs, axis=1)
size = 30 * (size - size.min()) / (size.max() - size.min())

glt.title('随机生成的300个点')
glt.point(vs, color, cm='jet', alpha=0.8, size=size)
glt.colorbar('jet', [0, 100], loc='right', subject='高度', endpoint=True)
glt.colorbar('hsv', [3, 8], loc='right', subject='厚度', endpoint=True)
glt.colorbar('Paired', [-50, 50], loc='bottom', subject='温度', margin_left=5)
glt.colorbar('rainbow', [0, 240], loc='bottom', subject='速度', margin_right=5)
glt.show()
```

[doc_cb.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/doc_cb.jpg)

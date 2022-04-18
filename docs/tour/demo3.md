---
sort: 3
---

# Colorbar

对于数据快速可视化工具来说，Colorbar是必不可少的。下面的代码演示了Colorbar最简单的用法。

```python
import numpy as np
import wxgl.glplot as glt

vs = np.random.random((300, 3))*2-1
color = np.random.random(300)
size = np.linalg.norm(vs, axis=1)
size = 30 * (size - size.min()) / (size.max() - size.min())

glt.title('随机生成的300个点')
glt.point(vs, color, cm='jet', alpha=0.8, size=size)
glt.colorbar('jet', [0, 100], loc='right', subject='高度')
glt.colorbar('Paired', [-50, 50], loc='bottom', subject='温度', margin_left=5)
glt.colorbar('rainbow', [0, 240], loc='bottom', subject='速度', margin_right=5)
glt.show()
```

[readme_03.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/readme_03.jpg)


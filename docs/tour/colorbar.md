---
sort: 2
---

# Colorbar

对于数据快速可视化工具来说，Colorbar是必不可少的。下面的代码演示了Colorbar最简单的用法。

```python
import numpy as np
import wxgl

z, x = np.mgrid[-np.pi:np.pi:51j, -np.pi:np.pi:51j]
y = np.sin(x) + np.cos(z)
cm = 'viridis' # WxGL的颜色映射方案继承自Matplotlib

app = wxgl.App()
app.title('网格曲面')
app.mesh(x, y, z, data=y, cm=cm, fill=False)
app.colorbar((y.min(), y.max()), cm=cm, ff=lambda v:'%.2f'%v) # ff用于设置ColorBar刻度标注的格式化函数
app.show()
```

![tour_colorbar.png](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/tour_colorbar.png)


---
sort: 11
---

# 渲染面填充

fill参数可以设置由三角面或四角面描述的曲面模型的填充方式，缺省默认值为None，表示使用当前设置，True表示填充，False表示无填充。如果有必要，还可以尝试fill参数的其他选项：'FCBC'|'FLBC'|'FCBL'|'FLBL'。

```python
import numpy as np
import wxgl.glplot as glt

z, x = np.mgrid[-2:2:50j,-2:2:50j]
y = 2*x*np.exp(-x**2-z**2)

glt.mesh(x, y, z, color=y, cm='hsv', fill='FLBC')
glt.show()
```

![doc_fill.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/doc_fill.jpg)


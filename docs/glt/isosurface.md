---
sort: 17
---

# 三维重建

[wxgl.glplot.isosurface](https://xufive.github.io/wxgl/api/glplot.html#wxglregionisosurface)实现了基于MarchingCube算法的三维重建。

下面例子中使用GitHub本项目example路径下的头部CT图片完成头部三维重建。

```python
import numpy as np
from PIL import Image
import wxgl
import wxgl.glplot as glt

glt.title('基于头部CT的三维重建演示')
data = np.stack([np.flipud(np.fliplr(np.array(Image.open('res/headCT/head%d.png'%i)))) for i in range(109)], axis=0)
data = np.rollaxis(data, 2, 1)[...,3]
glt.isosurface(data, data.max()/8, color='#CCC6B0', x=(-0.65,0.65), y=(-1, 1), z=(-1, 1), light=wxgl.SkyLight())
glt.grid()

glt.show()
```

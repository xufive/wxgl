---
sort: 9
---

# 透明和不透明模型

对于（半）透明模型，需要显式地设置其不透明参数opacity为False。WxGL在渲染（半）透明模型时自动关闭深度缓冲区并按模型深度从深至浅依次渲染。（半）透明模型深度由该模型所有顶点的z值的均值决定。3D文本模型作为（半）透明模型，无需设置opacity参数。

```python
import numpy as np
import wxgl.glplot as glt

glt.cube((0,0,0), 1.2)
glt.cylinder((-1,0,0), (1,0,0), 0.5, color=(1.0,1.0,0.1,0.7), opacity=False)
glt.text3d('WxGL', [[-1,1,0.5], [-1,-1,0.5], [1,1,0.5], [1,-1,0.5]], color='blue', size=128)
glt.text3d('WxGL', [[-1,1,-0.5], [-1,-1,-0.5], [1,1,-0.5], [1,-1,-0.5]], color='cyan', size=128)
glt.show()
```

![doc_opacity.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/doc_opacity.jpg)


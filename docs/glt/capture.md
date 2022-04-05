---
sort: 18
---

# 静默生成GIF或视频文件

除了在UI上操作按钮可以生成GIF或视频文件，wxgl.glplot提供了静默生成GIF或视频文件的函数[wxgl.glplot.capture](https://xufive.github.io/wxgl/api/glplot.html#wxglglplotcapture)。

运行下面这段代码，将会生成每秒50帧，共计300帧的mp4格式的视频文件。

```python
import numpy as np
import wxgl.glplot as glt

tf_1 = lambda t:((0, 1, 0, (0.01*t)%360),) # 大球自转速度10°/s

def tf_2(t):
    theta = -(0.05*t)%360 # 小球公转和自转都是-50°/s
    rotate = (0, 1, 0, theta) # 小球自转
    theta = np.radians(theta) # 角度转弧度
    r = 1 # 小球公转半径
    shift = (r*np.cos(theta), 0, -r*np.sin(theta)) # 小球公转
    
    return (rotate, shift)

glt.uvsphere((0,0,0), 0.8, fill=False, transform=tf_1)
glt.uvsphere((0,0,0), 0.2, fill=False, transform=tf_2)

glt.capture(r'd:\demo.mp4', fps=50, fn=300)
```

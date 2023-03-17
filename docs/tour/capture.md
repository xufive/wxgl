---
sort: 7
---

# 生成动画或视频文件

除了显示画布的show方法，wxgl.App还提供了保存画布的savefig方法。savefig不仅可以将当前OpengGL缓冲区的内容保存为.png或.jpg类型的图像文件，还可以生成.gif/.webp/.mp4/.avi等动画或视频文件。

下面这段代码绘制了一大一小两个自转的圆球，小球同时围绕大球公转。运行代码，将会生成每秒25帧共计200帧的mp4格式的视频文件。

```python
import wxgl

tf_1 = lambda t:((0, 1, 0, (0.01*t)%360),) # 大球自转速度10°/s

def tf_2(t):
    theta = -(0.05*t)%360 # 小球公转和自转都是-50°/s
    rotate = (0, 1, 0, theta) # 小球自转
    theta = np.radians(theta) # 角度转弧度
    r = 1 # 小球公转半径
    shift = (r*np.cos(theta), 0, -r*np.sin(theta)) # 小球公转
    
    return (rotate, shift)

app = wxgl.App()
app.sphere((0,0,0), 0.8, fill=False, transform=tf_1)
app.sphere((0,0,0), 0.2, fill=False, transform=tf_2)
app.savefig('capture/revolve.mp4', fps=25, frames=200)
```

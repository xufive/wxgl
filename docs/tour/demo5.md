---
sort: 5
---

# 让模型动起来

通过transform参数传递一个以累计渲染时长duration为参数的函数给模型，可以实现复杂的模型动画。相机巡航也以类似的方式实现。下面的代码中，两个子图均使用了射向右后方的平行灯光。当模型旋转时，由于相机和灯光位置不变，模型上的光照位置随之改变；而相机旋转时，由于模型和灯光的相对管不变，模型上的光照位置固定不变。

```python
import wxgl
import wxgl.glplot as glt

tf = lambda duration : ((0, 1, 0, (0.02*duration)%360),)
cf = lambda duration : {'azim':(-0.02*duration)%360}

tx = wxgl.Texture('res/earth.jpg')
light = wxgl.SunLight(direction=(1,0,-1))

glt.subplot(121)
glt.title('模型旋转')
glt.cylinder((0,1,0), (0,-1,0), 1, texture=tx, transform=tf, light=light)

glt.subplot(122)
glt.cruise(cf)
glt.title('相机旋转')
glt.cylinder((0,1,0), (0,-1,0), 1, texture=tx, light=light)

glt.show()
```

![readme_05.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/readme_05.jpg)

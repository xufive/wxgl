---
sort: 3
---

# 光照效果

WxGL提供了BaseLight（基础光照模型）、SunLight（太阳光照模型）、LampLight（点光源光照模型）、SkyLight（户外光照模型）、SphereLight（球谐光照模型）等多种光照方案，配合漫反射系数、镜面反射系数、高光系数、透光系数等参数，可模拟出不同的质感。即使不设置light参数，WxGL的模型也都使用了默认的光照效果。下面的代码使用light参数演示了不同光照效果下的球环模型。

```python
import wxgl

app = wxgl.App()
app.text('太阳光', (-5,7.5,0), align='center')
app.torus((-5,4,0), 1, 3, vec=(0,1,1), light=wxgl.SunLight())
app.text('灯光', (5,7.5,0), align='center')
app.torus((5,4,0), 1, 3, vec=(0,1,1), light=wxgl.LampLight())
app.text('户外光', (-5,-0.5,0), align='center')
app.torus((-5,-4,0), 1, 3, vec=(0,1,1), light=wxgl.SkyLight())
app.text('球谐光', (5,-0.5,0), align='center')
app.torus((5,-4,0), 1, 3, vec=(0,1,1), light=wxgl.SphereLight(5))
app.show()
```

![tour_light.png](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/tour_light.png)

---
sort: 4
---

# 光照和材质

WxGL提供了BaseLight、SunLight、LampLight、SkyLight、SphereLight等多种光照方案，配合光洁度、粗糙度、金属度、透光度等参数，可模拟出不同的质感。

```python
import wxgl
import wxgl.glplot as glt

glt.subplot(221)
glt.title('太阳光')
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.SunLight(roughness=0, metalness=0, shininess=0.5))

glt.subplot(222)
glt.title('灯光')
pos = (3, 0.0, 3)
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.LampLight(position=pos))
glt.point((pos,), color='white', size=20)

glt.subplot(223)
glt.title('户外光')
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.SkyLight(sky=(1.0,1.0,1.0)))

glt.subplot(224)
glt.title('球谐光')
glt.torus((0,0,0), 1, 3, vec=(0,1,1), light=wxgl.SphereLight(5, factor=0.8))

glt.show()
```

[doc_light.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/doc_light.jpg)

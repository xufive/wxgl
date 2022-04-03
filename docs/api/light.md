---
sort: 3
---

# light

WxGL光照情景模式类。

## wxgl.BaseLight

**wxgl.BaseLight(ambient=(1.0,1.0,1.0))**

环境光照情景模式。参数说明如下：

```
ambient     - 环境光颜色，默认(1.0,1.0,1.0)
```

## wxgl.SunLight

**wxgl.SunLight(direction=(-5.0,-1.0,-5.0), color=(1.0,1.0,1.0), ambient=(0.3,0.3,0.3), \*\*kwds)**

太阳光照情景模式。参数说明如下：

```
direction   - 太阳光方向，默认(1.0,1.0,1.0)
color     	- 太阳光颜色，默认(1.0,1.0,1.0)
ambient     - 环境光颜色，默认(1.0,1.0,1.0)
kwds        - 关键字参数
                stray           - 是否存在杂散光：默认False
                roughness       - 粗糙度（1-镜面反射系数）：值域范围[0.0,1.0]，默认0.2
				metalness       - 金属度（1-漫反射系数）：值域范围[0.0,1.0]，默认0.2
				pellucidness    - 透光度：值域范围[0.0,1.0]，默认0.2
				shininess       - 光洁度（高光系数）：值域范围(0.0,1.0]，默认0.5
```

## wxgl.LampLight

**wxgl.LampLight(position=(5.0,1.0,5.0), color=(1.0,1.0,1.0), ambient=(0.3,0.3,0.3), \*\*kwds)**

定位光照情景模式。参数说明如下：

```
position    - 灯光位置，默认(5.0,1.0,5.0)
color     	- 灯光颜色，默认(1.0,1.0,1.0)
ambient     - 环境光颜色，默认(1.0,1.0,1.0)
kwds        - 关键字参数
                stray           - 是否存在杂散光：默认False
                roughness       - 粗糙度（1-镜面反射系数）：值域范围[0.0,1.0]，默认0.2
				metalness       - 金属度（1-漫反射系数）：值域范围[0.0,1.0]，默认0.2
				pellucidness    - 透光度：值域范围[0.0,1.0]，默认0.2
				shininess       - 光洁度（高光系数）：值域范围(0.0,1.0]，默认0.5
```

## wxgl.SkyLight

**wxgl.SkyLight(direction=(0.0,-1.0,0.0), sky=(1.0,1.0,1.0), ground=(0.5,0.5,0.5))**

户外光照情景模式。参数说明如下：

```
position    - 主光方向，默认(0.0,-1.0,0.0)
sky     	- 天光颜色，默认(1.0,1.0,1.0)
ground      - 地光颜色，默认(0.5,0.5,0.5)
```

## wxgl.SphereLight

**wxgl.SphereLight(key=0, factor=0.8)**

球谐光照情景模式。参数说明如下：

```
key         - 情景序号，0~9，默认0
factor      - 反射衰减因子，值域范围(0.0,1.0]，默认0.8
```

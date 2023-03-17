---
sort: 3
---

# 光照情景模式

## wxgl.BaseLight

wxgl.BaseLight(ambient=(1.0,1.0,1.0))

基础光照情景模式。

```
ambient     - 环境光颜色，默认(1.0,1.0,1.0)
```

## wxgl.SunLight

wxgl.SunLight(direction=(0.0,0.0,-1.0), lightcolor=(1.0,1.0,1.0), ambient=(0.3,0.3,0.3), \*\*kwds)

太阳光照情景模式。

```
direction   - 太阳光方向
lightcolor  - 太阳光颜色
ambient     - 环境光颜色
kwds        - 关键字参数
    diffuse     - 漫反射系数：值域范围[0.0, 1.0]，数值越大，表面越亮。默认值0.8
    specular    - 镜面反射系数：值域范围[0.0, 1.0]，数值越大，高光越亮。默认值0.6
	shiny       - 高光系数：值域范围[1, 3000]，数值越大，高光区域越小。默认值50
	pellucid    - 透光系数：值域范围[0.0,1.0]，数值越大，背面越亮。默认值0.5
```

## wxgl.LampLight

wxgl.LampLight(lamp=(0.0,0.0,2.0), lightcolor=(1.0,1.0,1.0), ambient=(0.5,0.5,0.5), \*\*kwds)

定位光照情景模式。

```
lamp        - 光源位置
lightcolor  - 光源颜色
ambient     - 环境光颜色
kwds        - 关键字参数
    diffuse     - 漫反射系数：值域范围[0.0, 1.0]，数值越大，表面越亮。默认值0.8
    specular    - 镜面反射系数：值域范围[0.0, 1.0]，数值越大，高光越亮。默认值0.6
	shiny       - 高光系数：值域范围[1, 3000]，数值越大，高光区域越小。默认值50
	pellucid    - 透光系数：值域范围[0.0,1.0]，数值越大，背面越亮。默认值0.5
```

## wxgl.SkyLight

wxgl.SkyLight(direction=(0.0,-1.0,0.0), sky=(1.0,1.0,1.0), ground=(0.3,0.3,0.3))

户外光照情景模式。

```
direction   - 主光方向
sky     	- 天光颜色
ground      - 地光颜色
```

## wxgl.SphereLight

wxgl.SphereLight(style=0, factor=0.8)

球谐光照情景模式。

```
style       - 情景序号，0~9，默认0
factor      - 反射衰减因子，值域范围(0.0,1.0]，默认0.8
```

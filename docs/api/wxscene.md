---
sort: 8
---

# wxgl.wxscene.WxScene

wxgl.wxscene.WxScene(parent, scheme, \*\*kwds)

场景类，继承自wx.glcanvas.GLCanvas类。

```
parent      - 父级窗口对象
scheme      - wxgl.Scheme类实例
kwds        - 关键字参数
    size        - 窗口分辨率，默认(960, 640)
    bg          - 画布背景色，默认(0.0, 0.0, 0.0)
    haxis       - 高度轴，默认y轴，可选z轴，不支持x轴
    fovy        - 相机水平视野角度，默认50°
    azim        - 方位角，默认0°
    elev        - 高度角，默认0°
    azim_range  - 方位角变化范围，默认-180°～180°
    elev_range  - 高度角变化范围，默认-180°～180°
    smooth      - 直线和点的反走样，默认True
```

## wxgl.wxscene.WxScene.capture

wxgl.wxscene.WxScene.capture(mode='RGBA', crop=False, buffer='front')

捕捉缓冲区数据，保存到名为im_pil的类属性变量中。

```
mode        - 'RGB'或'RGBA'
crop        - 是否将宽高裁切为16的倍数
buffer      - 'front'（前缓冲区）或'back'（后缓冲区）
```

## wxgl.wxscene.WxScene.get_buffer

wxgl.wxscene.WxScene.get_buffer(mode='RGBA', crop=False, buffer='front')

以PIL对象的格式返回场景缓冲区数据。

```
mode        - 'RGB'或'RGBA'
crop        - 是否将宽高裁切为16的倍数
buffer      - 'front'（前缓冲区）或'back'（后缓冲区）
```

## wxgl.wxscene.WxScene.home

wxgl.wxscene.WxScene.home()

恢复初始位置和姿态。

## wxgl.wxscene.WxScene.pause

wxgl.wxscene.WxScene.pause()

动画启停。

## wxgl.wxscene.WxScene.set_visible

wxgl.wxscene.WxScene.set_visible(name, visible)

设置部件或模型的可见性。

```
name        - 部件名或模型id
visible     - bool型
```

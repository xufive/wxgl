---
sort: 7
---

# wxgl.App

wxgl.App(backend='auto', \*\*kwds)

三维数据快速可视化类，由wxgl.Scheme派生而来。

```
backend     - 后端GUI库，可选wx或qt，默认auto（按照wx/qt优先级自动选择）
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

## wxgl.App.info

wxgl.App.info(time_func=None, cam_func=None)

设置时间信息格式化函数和相机位置信息格式化函数，开启在界面状态栏显示信息功能。

```
time_func   - 以时间t（毫秒）为参数的时间信息格式化函数，返回字符串
cam_func    - 以方位角、仰角和距离为参数的相机位置信息格式化函数，返回字符串
```

## wxgl.App.save_fig

wxgl.App.save_fig(outfile, dpi=None, fps=25, frames=100, loop=0, quality=100)

保存画布为图像文件或动画文件。

```
outfile     - 输出文件名，支持的文件格式：'.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.avi', '.wmv', '.mov' 
dpi         - 图像文件每英寸像素数
fps         - 动画文件帧率
frames      - 动画文件总帧数
loop        - gif文件播放次数，0表示循环播放
quality     - webp文件质量，100表示最高品质
```

## wxgl.App.show

wxgl.App.show()

显示画布。


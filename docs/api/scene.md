---
sort: 7
---

# wxgl.Scene

**wxgl.Scene(parent, smooth=True, style='blue')**

场景类，继承自wx.glcanvas.GLCanvas类。参数说明如下：

```
parent      - 父级窗口对象
smooth      - 反走样开关，默认开
style       - 场景风格，默认太空蓝
	'blue'      - 太空蓝
	'gray'      - 国际灰
	'black'     - 石墨黑
	'white'     - 珍珠白
	'royal'     - 宝石蓝
```

## wxgl.Scene.add_region

**wxgl.Scene.add_region(box, \*\*kwds)**

向场景内添加视区，返回视区对象（Region实例）。参数说明如下：

```
box         - 视区位置四元组：四个元素分别表示视区左下角坐标、宽度、高度，元素值域[0,1]
kwds        - 关键字参数
                proj        - 投影模式：'O' - 正射投影，'P' - 透视投影（默认）
                fixed       - 锁定模式：固定ECS原点、相机位置和角度，以及视口缩放因子等。布尔型，默认False
                azim        - 方位角：-180°~180°范围内的浮点数，默认0°
                elev        - 高度角：-180°~180°范围内的浮点数，默认0°
                azim_range  - 方位角限位器：默认-180°~180°
                elev_range  - 仰角限位器：默认-180°~180°
                zoom        - 视口缩放因子：默认1.0
				name        - 视区名
```

## wxgl.Scene.set_style

**wxgl.Scene.set_style(style)**

设置场景风格。参数说明如下：

```
style       - 场景风格，可选项：'blue'|'gray'|'black'|'white'|'royal'
```

## wxgl.Scene.render

模型渲染。无参数。

**wxgl.Scene.render()**

## wxgl.Scene.save_scene

**wxgl.Scene.save_scene(fn, alpha=True, buffer='front', crop=False)**

保存场景为图像文件。参数说明如下：

```
fn          - 保存的文件名
alpha       - 是否使用透明通道
buffer      - 显示缓冲区， 可选项：'front'|'back'。默认使用前缓冲区（当前显示内容）
crop        - 是否将宽高裁切为16的倍数
```

## wxgl.Scene.start_animate

开始动画。无参数。

**wxgl.Scene.start_animate()**

## wxgl.Scene.stop_animate

**wxgl.Scene.stop_animate()**

停止动画。无参数。

## wxgl.Scene.pause_animate

**wxgl.Scene.pause_animate()**

暂停或重启动画。无参数。

## wxgl.Scene.estimate

动画渲染帧频评估，返回当前渲染帧率。无参数。

**wxgl.Scene.estimate()**

## wxgl.Scene.start_record

**wxgl.Scene.start_record(out_file, fps, fn, loop)**

开始生成gif或视频文件。参数说明如下：

```
out_file    - 文件名，支持gif和mp4、avi、wmv等格式
fps         - 每秒帧数
fn          - 总帧数
loop        - 循环播放次数（仅gif格式有效，0表示无限循环）
```

## wxgl.Scene.stop_record

**wxgl.Scene.stop_record()**

停止生成gif或视频文件。无参数。

## wxgl.Scene.restore_posture

还原场景内各视区的相机初始姿态。无参数。

**wxgl.Scene.restore_posture()**


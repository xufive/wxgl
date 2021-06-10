# WxGL

WxGL是一个基于PyOpenGL的三维数据可视化库，以wx为显示后端，提供Matplotlib风格的交互式应用模式，同时，也可以和wxPython无缝结合，在wx的窗体上绘制三维模型。

# 1. 安装和依赖关系

WxGL模块使用pip命令安装。
```shell
pip install wxgl
```

WxGL依赖以下模块，如果当前运行环境没有安装这些模块，安装程序将会自动安装它们。如果安装过程出现问题，或者安装完成后无法正常使用，请手动安装WxGL的依赖模块。
* numpy（推荐版本：1.18.2或更高） 
* scipy（推荐版本：1.4.1或更高） 
* freetype（推荐版本：2.1.0.post1或更高）
* matplotlib（推荐版本：3.1.2或更高） 
* wxpython（推荐版本：4.0.7.post2或更高） 
* pyopengl（推荐版本：3.1.3b2或更高） 

# 2. 快速体验

从V0.6.0开始，WxGL新增了交互式绘图子模块wxplot，提供类似Matplotlib风格2D/3D绘图函数。如果熟悉NumPy和Matplotlib的话，几分钟就可以学会使用WxGL的交互式绘图。

```python
>>> import numpy as np
>>> import wxgl.wxplot as plt
>>> x = np.linspace(0, 2*np.pi, 361)
>>> y = np.sin(x) * 3
>>> plt.plot(x, y)
>>> plt.show()
```

上面这几行代码，画出了一条正弦曲线。如果忽略模块名的话，这些代码和Matplotlib是完全一样的。除去导入模块和数据准备，真正的绘图语句只有最后两行。执行最后一句show()命令后，将弹出GUI窗口，同时程序将阻塞，直至关闭GUI窗口。

WxGL支持在一张画布上画多张子图，创建子图的方式也非常类似Matplotlib。下面使用wxplot.sphere()函数绘制两个球体。

* 创建子图方式一：
```python
>>> plt.subplot(121) # 一行两列的第一个位置
>>> plt.sphere((0,0,0), 3, 'green')
>>> plt.subplot(122) # 一行两列的第二个位置
>>> plt.sphere((0,0,0), 3, '#00FFFF', mode='FCBC')
>>> plt.show()
```

* 创建子图方式二：
```python
>>> ax1 = plt.subplot(121) # 一行两列的第一个位置
>>> ax1.sphere((0,0,0), 3, 'green')
>>> ax2 = plt.subplot(122) # 一行两列的第二个位置
>>> ax2.sphere((0,0,0), 3, '#00FFFF', mode='FCBC')
>>> plt.show()
```

* 创建子图方式三：
```python
>>> fig = plt.figure()
>>> ax1 = fig.add_axes(121) # 一行两列的第一个位置
>>> ax1.sphere((0,0,0), 3, 'green')
>>> ax2 = fig.add_axes(122) # 一行两列的第二个位置
>>> ax2.sphere((0,0,0), 3, '#00FFFF', mode='FCBC')
>>> plt.show()
```

上面三种方式创建的子图，绘制效果是完全一致的。

和Matplotlib类似，wxplot也提供了title()和text()两个函数来绘制标题和文本。除了文本内容，这两个函数还可以接受文本大小、位置、颜色、字体、对齐方式等若干参数。
```python
>>> plt.cube((0,0,0), 3, 'cyan') # 绘制六面体，cyan是颜色，十六进制表示为#00FFFF
>>> plt.sphere((0,0,0), 1.5, 'orange') # 绘制球
>>> plt.cylinder((0,0,-2), (0,0,2), 0.5, 'green') # 绘制圆柱
>>> plt.cone((0,-2,0), (0,2,0), 0.5, 'purple') # 绘制圆锥，purple是颜色，十六进制表示为#F020F0
>>> plt.title('六面体、圆锥、圆柱和球的组合') # 绘制标题
>>> plt.text('这是锥尖', size=40, pos=(0,2,0), align='left') # 绘制文本
>>> plt.show()
```

# 3. 交互式绘图函数

wxplot函数自带完备的文档说明，只需要使用__doc__查看即可。

## 3.1 新建画布：figure()
```python
>>> print(plt.figure.__doc__)
    新建画布
    Useage: figure(*args, **kwds)
    ----------------------------------------------------
    size        - 画布分辨率，默认800x600
    kwds        - 关键字参数
                    head        - 定义方向：'x+'|'y+'|'z+'
                    zoom        - 视口缩放因子
                    mode        - 2D/3D模式
                    aim         - 观察焦点
                    dist        - 相机位置与目标点位之间的距离
                    view        - 视景体
					elevation   - 仰角
                    azimuth     - 方位角
					interval    - 模型动画帧间隔时间（单位：ms）
                    style       - 配色方案，'black'|'white'|'gray'|'blue'
```

## 3.2 保存画布为文件：savefig()
```python
>>> print(plt.savefig.__doc__)
    保存画布为文件
    Useage: savefig(fn, alpha=False)
    ----------------------------------------------------
    fn          - 文件名
    alpha       - 透明通道开关
```

## 3.3 显示画布：show()
```python
>>> print(plt.savefig.__doc__)
    显示画布
    Useage: show(rotation=None, **kwds)
    ----------------------------------------------------
    rotation    - 旋转模式
                    None        - 无旋转
                    'h+'        - 水平顺时针旋转（默认方式）
                    'h-'        - 水平逆时针旋转
                    'v+'        - 垂直前翻旋转
                    'v-'        - 垂直后翻旋转
    kwds        - 关键字参数
                    elevation   - 初始仰角，以度（°）为单位，默认值为0
                    azimuth     - 初始方位角以度（°）为单位，默认值为0
                    step        - 帧增量，以度（°）为单位，默认值为5
                    interval    - 帧间隔，以ms为单位，默认值为20
```

## 3.4 数值颜色映射：cmap()
```python
>>> print(plt.cmap.__doc__)
    数值颜色映射
    Useage: cmap(data, cm, **kwds)
    ----------------------------------------------------
    data        - 数据
    cm          - 颜色映射表名
    kwds        - 关键字参数
                    invalid     - 无效数据的标识
                    invalid_c   - 无效数据的颜色
                    datamax     - 数据最大值，默认为None
                    datamin     - 数据最小值，默认为None
                    alpha       - 透明度，None表示返回RGB格式
```

## 3.5 添加子图：subplot()
```python
>>> print(plt.subplot.__doc__)
    添加子图
    Useage: subplot(pos, padding=(20,20,20,20))
    ----------------------------------------------------
    pos         - 子图在画布上的位置和大小
                    三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                    四元组      - 以画布左下角为原点，宽度和高度都是1。四元组分别表示子图左下角在画布上的水平、垂直位置和宽度、高度
    padding     - 四元组，上、右、下、左四个方向距离边缘的留白像素
```

## 3.6 绘制点和线：plot()函数
```python
>>> print(plt.plot.__doc__)
    绘制点和线
    Useage: plot(xs, ys, zs=None, color=None, size=0.0, width=1.0, style='solid', cmap='hsv', caxis='z', **kwds)
    ----------------------------------------------------
    xs/ys/zs    - 顶点的x/y/z坐标集，元组、列表或一维数组类型，长度相等。若zs为None，则自动补为全0的数组
    color       - 全部或每一个顶点的颜色。None表示使用cmap参数映射颜色
    size        - 顶点的大小，整型或浮点型。若为0，则表示不绘制点，只绘制线
    width       - 线宽，0.0~10.0之间的浮点数。若为0，则表示不绘制线，只绘制点
    style       - 线型
                    'solid'     - 实线
                    'dashed'    - 虚线
                    'dotted'    - 点线
                    'dash-dot'  - 虚点线
    cmap        - 颜色映射表，color为None时有效
    caxis       - 用于颜色映射的坐标轴数据，2D模式下自动转为'y'
	kwds        - 关键字参数
                    slide       - 是否作为动画播放的帧
                    name        - 模型名
```

## 3.7 绘制散点图：scatter()函数
```python
>>> print(plt.scatter.__doc__)
    绘制散点图
    Useage: scatter(vs, color=None, size=1.0, cmap='hsv', caxis='z')
    ----------------------------------------------------
    vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
    color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
    size        - 顶点的大小，整型或浮点型
    cmap        - 颜色映射表，color为None时有效。使用vs的z坐标映射颜色
    caxis       - 用于颜色映射的坐标轴数据，2D模式下自动转为'y'
```

## 3.8 绘制mesh：mesh()
```python
>>> print(plt.mesh.__doc__)
    绘制mesh
    Useage: mesh(xs, ys, zs, color=None, mode='FCBC', cmap='hsv', caxis='z', **kwds)
    ----------------------------------------------------
    xs/ys/zs    - 顶点的x/y/z坐标集，二维数组
    color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
    mode        - 显示模式
                    'FCBC'      - 前后面填充颜色FCBC
                    'FLBL'      - 前后面显示线条FLBL
                    'FCBL'      - 前面填充颜色，后面显示线条FCBL
                    'FLBC'      - 前面显示线条，后面填充颜色FLBC
    cmap        - 颜色映射表，color为None时有效。使用zs映射颜色
    caxis       - 用于颜色映射的坐标轴数据，2D模式下自动转为'y'
    kwds        - 关键字参数
					light       - 材质灯光颜色，None表示关闭材质灯光
					slide       - 是否作为动画播放的帧
					name        - 模型名
```

## 3.9 绘制surface：surface()
```python
>>> print(plt.surface.__doc__)
    绘制surface
    Useage: surface(vs, color=None, method='Q', mode='FCBC', texture=None, alpha=True, **kwds)
    ----------------------------------------------------
    vs          - 顶点坐标集，二维数组类型，shape=(n,3)
    color       - 顶点颜色或颜色集，可以混合使用纹理。None表示仅使用纹理
    method      - 绘制方法
                    'Q'         - 四边形
                                    0--3 4--7
                                    |  | |  |
                                    1--2 5--6
                    'T'         - 三角形
                                    0--2 3--5
                                     \/   \/
                                      1    4
                    'Q+'        - 边靠边的连续四边形
                                   0--2--4
                                   |  |  |
                                   1--3--5
                    'T+'        - 边靠边的连续三角形
                                       0--2--4
                                        \/_\/_\
                                         1  3  5
                    'F'         - 扇形
                    'P'         - 多边形
    mode        - 显示模式
                    'FCBC'      - 前后面填充颜色FCBC
                    'FLBL'      - 前后面显示线条FLBL
                    'FCBL'      - 前面填充颜色，后面显示线条FCBL
                    'FLBC'      - 前面显示线条，后面填充颜色FLBC
    texture     - 用于纹理的图像文件或数组对象，仅当method为Q时有效
    kwds        - 关键字参数
                    light       - 材质灯光颜色，None表示关闭材质灯光
                    slide       - 是否作为动画播放的帧
                    name        - 模型名
```

## 3.10 绘制圆管：pipe()
```python
>>> print(plt.pipe.__doc__)
    绘制圆管
    Useage: pipe(vs, radius, color=None, slices=36, mode='FCBC', cmap='hsv', caxis='z')
    ----------------------------------------------------
    vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
    radius      - 圆管半径，浮点型
    color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
    slices      - 圆管面分片数（数值越大越精细）
    mode        - 显示模式
                    'FCBC'      - 前后面填充颜色FCBC
                    'FLBL'      - 前后面显示线条FLBL
                    'FCBL'      - 前面填充颜色，后面显示线条FCBL
                    'FLBC'      - 前面显示线条，后面填充颜色FLBC
    cmap        - 颜色映射表，color为None时有效。使用vs的z坐标映射颜色
    caxis       - 用于颜色映射的坐标轴数据，2D模式下自动转为'y'
```

## 3.11 绘制球体：sphere()
```python
>>> print(plt.sphere.__doc__)
    绘制球体
    Useage: sphere(center, radius, color, slices=60, mode='FLBL')
    ----------------------------------------------------
    center      - 球心坐标，元组、列表或数组
    radius      - 半径，浮点型
    color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
    slices      - 球面分片数（数值越大越精细）
    mode        - 显示模式
                    'FCBC'      - 前后面填充颜色FCBC
                    'FLBL'      - 前后面显示线条FLBL
                    'FCBL'      - 前面填充颜色，后面显示线条FCBL
                    'FLBC'      - 前面显示线条，后面填充颜色FLBC
```


## 3.12 绘制六面体：cube()
```python
>>> print(plt.cube.__doc__)
    绘制六面体
    Useage: cube(center, side, color, mode='FLBL')
    ----------------------------------------------------
    center      - 中心坐标，元组、列表或数组
    side        - 棱长，整型、浮点型，或长度为3的元组、列表数组
    color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
    mode        - 显示模式
                    'FCBC'      - 前后面填充颜色FCBC
                    'FLBL'      - 前后面显示线条FLBL
                    'FCBL'      - 前面填充颜色，后面显示线条FCBL
                    'FLBC'      - 前面显示线条，后面填充颜色FLBC
```

## 3.13 绘制圆柱体：cylinder()
```python
>>> print(plt.cylinder.__doc__)
    绘制圆柱体
    Useage: cylinder(v_top, v_bottom, radius, color, slices=60, mode='FCBC')
    ----------------------------------------------------
    v_top       - 圆柱上端面的圆心坐标，元组、列表或numpy数组
    v_bottom    - 圆柱下端面的圆心坐标，元组、列表或numpy数组
    radius      - 半径，浮点型
    color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
    slices      - 圆柱面分片数（数值越大越精细）
    mode        - 显示模式
                    'FCBC'      - 前后面填充颜色FCBC
                    'FLBL'      - 前后面显示线条FLBL
                    'FCBL'      - 前面填充颜色，后面显示线条FCBL
                    'FLBC'      - 前面显示线条，后面填充颜色FLBC
```

## 3.14 绘制圆锥体：cone()
```python
>>> print(plt.cone.__doc__)
    绘制圆锥体
    Useage: cone(center, spire, radius, color, slices=60, mode='FCBC')
    ----------------------------------------------------
    center      - 锥底圆心坐标，元组、列表或数组
    spire       - 锥尖坐标，元组、列表或数组
    radius      - 半径，浮点型
    color       - 顶点颜色或颜色集，None表示使用cmap参数映射颜色
    slices      - 锥面分片数（数值越大越精细）
    mode        - 显示模式
                    'FCBC'      - 前后面填充颜色FCBC
                    'FLBL'      - 前后面显示线条FLBL
                    'FCBL'      - 前面填充颜色，后面显示线条FCBL
                    'FLBC'      - 前面显示线条，后面填充颜色FLBC
```

## 3.15 绘制三维等值面：capsule()
```python
>>> print(plt.capsule.__doc__)
    绘制囊（三维等值面）
    Useage: capsule(data, threshold, color, r_x=None, r_y=None, r_z=None, mode='FCBC', **kwds)
    ----------------------------------------------------
    data        - 数据集，numpy.ndarray类型，shape=(layers,rows,cols)
    threshold   - 阈值，浮点型
    color       - 表面颜色
    r_x         - x的动态范围，元组
    r_y         - y的动态范围，元组
    r_z         - z的动态范围，元组
    mode        - 显示模式
                    None        - 使用当前设置
                    'FCBC'      - 前后面填充颜色FCBC
                    'FLBL'      - 前后面显示线条FLBL
                    'FCBL'      - 前面填充颜色，后面显示线条FCBL
                    'FLBC'      - 前面显示线条，后面填充颜色FLBC
    kwds        - 关键字参数
                    name        - 模型名
                    inside      - 是否更新数据动态范围
                    visible     - 是否显示
```

## 3.16 绘制流体：flow()
```python
>>> print(plt.flow.__doc__)
    绘制流体
    Useage: flow(ps, us, vs, ws, **kwds)
    ----------------------------------------------------
    ps          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
    us          - 顶点u分量集，numpy.ndarray类型，shape=(n,)
    vs          - 顶点v分量集，numpy.ndarray类型，shape=(n,)
    ws          - 顶点w分量集，numpy.ndarray类型，shape=(n,)
    kwds        - 关键字参数
                    color       - 轨迹线颜色，None表示使用速度映射颜色
                    actor       - 顶点模型类型，'point'|'line'两个选项
                    size        - point大小
                    width       - line宽度
                    length      - 轨迹线长度，以速度矢量的模为单位
                    duty        - 顶点line模型长度与轨迹线长度之比（占空比），建议值为0.4
                    frames      - 总帧数
                    interval    - 帧间隔，以ms为单位
                    threshold   - 高通阈值，滤除速度小于阈值的数据点
                    name        - 模型名
```

## 3.17 绘制标题：title()
```python
>>> print(plt.title.__doc__)
    绘制标题
    Useage: title(text, size=96, color=None, pos=(0,0,0), **kwds)
    ----------------------------------------------------
    text        - 文本字符串
    size        - 文字大小，整形
    color       - 文本颜色，预定义的颜色，或长度为3的列表或元组
    pos         - 文本位置，list或numpy.ndarray类型，shape=(3，)
    kwds        - 关键字参数
                    align       - left/right/center分别表示左对齐、右对齐、居中（默认）
                    valign      - top/bottom/middle分别表示上对齐、下对齐、垂直居中（默认）
                    family      - （系统支持的）字体
                    weight      - light/bold/normal分别表示字体的轻、重、正常（默认）
```

## 3.18 绘制文本：text()
```python
>>> print(plt.text.__doc__)
    绘制文本
    Useage: text(text, size=64, color=None, pos=(0,0,0), **kwds)
    ----------------------------------------------------
    text        - 文本字符串
    size        - 文字大小，整形
    color       - 文本颜色，预定义的颜色，或长度为3的列表或元组
    pos         - 文本位置，list或numpy.ndarray类型，shape=(3，)
    kwds        - 关键字参数
                    align       - left/right/center分别表示左对齐、右对齐、居中（默认）
                    valign      - top/bottom/middle分别表示上对齐、下对齐、垂直居中（默认）
                    family      - （系统支持的）字体
                    weight      - light/bold/normal分别表示字体的轻、重、正常（默认）
```

## 3.19 绘制Colorbar：colorbar()
```python
>>> print(plt.colorbar.__doc__)
    绘制colorbar
    Useage: colorbar(drange, cmap, loc, **kwds)
    ----------------------------------------------------
    drange      - 值域范围，tuple类型
    cmap        - 调色板名称
    loc         - 位置，top|bottom|left|right
    kwds        - 关键字参数
                    length          - ColorBar所在视区的长边长度，默认短边长度为1
                    subject         - 标题
                    subject_size    - 标题字号
                    label_size      - 标注字号
                    label_format    - 标注格式化所用lambda函数
                    tick_line       - 刻度线长度
                    endpoint        - 刻度是否包含值域范围的两个端点值
                    name            - 模型名
                    inside          - 是否数据动态范围
                    visible         - 是否显示
```

## 3.20 绘制网格和刻度：ticks()
```python
>>> print(plt.ticks.__doc__)
    绘制网格和刻度
    Useage: subplot(**kwds)
    ----------------------------------------------------
    kwds        - 关键字参数
                    segment_min     - 标注最少分段数量
                    segment_max     - 标注最多分段数量
                    label_2D3D      - 标注试用2D或3D文字
                    label_size      - 标注字号
                    xlabel_format   - x轴标注格式化所用lambda函数
                    ylabel_format   - y轴标注格式化所用lambda函数
                    zlabel_format   - z轴标注格式化所用lambda函数
```

# 4. 与wxPython集成

WxGL的容器名为WxGLScene，称为场景。WxGLScene是wx.glcanvas.GLCanvas的派生类，因此WxGL和wxPython的集成是天然无缝的，不存在任何障碍。

每个场景可以使用add_region()生成多个WxGLRegion对象，称为视区。在视区内可以创建模型，每个模型由一个或多个组件构成——所谓组件，可以理解为子模型。

## 4.1 WxGLScene API
### 4.1.1 构造函数
<b>WxGLScene.\_\_init\_\_(parent, **kwds)</b>
```
parent      - 父级窗口对象
kwds        - 关键字参数
				head        - 观察者头部的指向，字符串
					'x+'        - 头部指向x轴正方向
					'y+'        - 头部指向y轴正方向
					'z+'        - 头部指向z轴正方向
				
				zoom        - 视口缩放因子
				proj        - 投影模式，字符串
					'ortho'     - 平行投影
					'cone'      - 透视投影
				mode        - 2D/3D模式，字符串
				aim         - 观察焦点
				dist        - 相机距离观察焦点的距离
				view        - 视景体
				elevation   - 仰角
				azimuth     - 方位角
				interval    - 模型动画帧间隔时间（单位：ms）
				style       - 场景风格
					'black'     - 背景黑色，文本白色
					'white'     - 背景白色，文本黑色
					'gray'      - 背景浅灰色，文本深蓝色
					'blue'      - 背景深蓝色，文本淡青色
```

### 4.1.2 设置眼睛与目标点之间的相对关系
<b>WxGLScene.set_posture(elevation=None, azimuth=None, dist=None, save=False)</b>
```
elevation   - 仰角(度)
azimuth     - 方位角(度)
dist        - 相机位置与目标点位之间的距离
save        - 是否保存相机姿态
```

### 4.1.3 恢复初始姿态
<b>WxGLScene.reset_posture()</b>
```
无参数
```

### 4.1.4 保存场景为图像文件
<b>WxGLScene.save_scene(fn, alpha=True, buffer='FRONT')</b>
```
fn          - 保存的文件名
alpha       - 是否使用透明通道
buffer      - 显示缓冲区。默认使用前缓冲区（当前显示内容）
```

### 4.1.5 添加视区
<b>WxGLScene.add_region(box, fixed=False)</b>
```
box         - 四元组，元素值域[0,1]。四个元素分别表示视区左下角坐标、宽度、高度
fixed       - 是否锁定旋转缩放
```

### 4.1.6 添加子图
<b>WxGLScene.add_axes(pos, padding=(20,20,20,20))</b>
```
pos         - 三个数字组成的字符串或四元组，表示子图在场景中的位置和大小
padding     - 四元组，上、右、下、左四个方向距离边缘的留白像素
```

### 4.1.7 自动旋转
<b>WxGLScene.auto_rotate(rotation='h+', **kwds)</b>
```
rotation    - 旋转模式
				'h+'        - 水平顺时针旋转（默认方式）
				'h-'        - 水平逆时针旋转
				'v+'        - 垂直前翻旋转
				'v-'        - 垂直后翻旋转
kwds        - 关键字参数
				elevation   - 初始仰角，以度（°）为单位，默认值为0
				azimuth     - 初始方位角以度（°）为单位，默认值为0
				step        - 帧增量，以度（°）为单位，默认值为5
				interval    - 帧间隔，以ms为单位，默认值为20
```

### 4.1.8 停止旋转
<b>WxGLScene.stop_rotate()</b>
```
无参数
```

## 4.2 WxGLRegion API

### 4.2.1 构造函数
<b>WxGLRegion.\_\_init\_\_(scene, rid, box, fixed=False)</b>
```
scene       - 所属场景对象
rid         - 唯一标识
box         - 四元组，元素值域[0,1]。四个元素分别表示视区左下角坐标、宽度、高度
fixed       - 是否锁定旋转缩放
```


### 4.2.2 重置视区
<b>WxGLRegion.reset_box(box, clear=False)</b>
```
box         - 四元组，元素值域[0,1]。四个元素分别表示视区左下角坐标、宽度、高度
clear       - 是否清空所有模型
```

### 4.2.3 设置坐标轴范围
<b>WxGLRegion.set_data_range(r_x=None, r_y=None, r_z=None)</b>
```
r_x         - 二元组，x坐标轴范围
r_y         - 二元组，y坐标轴范围
r_z         - 二元组，z坐标轴范围
```

### 4.2.4 删除模型
<b>WxGLRegion.delete_model(name)</b>
```
name        - 模型名
```

### 4.2.5 显示模型
<b>WxGLRegion.show_model(name)</b>
```
name        - 模型名
```

### 4.2.6 隐藏模型
<b>WxGLRegion.hide_model(name)</b>
```
name        - 模型名
```

### 4.2.7 更新视区显示
<b>WxGLRegion.refresh()</b>
```
无参数
```

### 4.2.8 创建纹理对象
<b>WxGLRegion.create_texture(img, alpha=True)</b>
```
img         - 纹理图片文件名或数据
alpha       - 是否使用透明通道
```

### 4.2.9 绘制2D文字
<b>WxGLRegion.text2d(text, size=32, color=None, pos=[0,0,0], **kwds)</b>
```
text        - 文本字符串
size        - 文字大小，整型
color       - 文本颜色
				None表示使用场景对象scene的style风格提供的文本颜色
				预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
				浮点型的元组或列表，值域范围：[0,1]，长度：3
				numpy.ndarray类型，shape=(3,)
pos         - 文本位置，元组、列表或numpy数组
kwds        - 关键字参数
				align       - 兼容text3d()，并无实际意义
				valign      - 兼容text3d()，并无实际意义
				family      - （系统支持的）字体
				weight      - light/bold/normal分别表示字体的轻、重、正常（默认）
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
```

### 4.2.10 绘制3D文字
<b>WxGLRegion.text3d(text, size=32, color=None, pos=[0,0,0], **kwds)</b>
```
text        - 文本字符串
size        - 文字大小，整型
color       - 文本颜色
				None表示使用场景对象scene的style风格提供的文本颜色
				预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
				浮点型的元组或列表，值域范围：[0,1]，长度：3
				numpy.ndarray类型，shape=(3,)
pos         - 文本位置，元组、列表或numpy数组
kwds        - 关键字参数
				align       - left/right/center分别表示左对齐、右对齐、居中（默认）
				valign      - top/bottom/middle分别表示上对齐、下对齐、垂直居中（默认）
				family      - （系统支持的）字体
				weight      - light/bold/normal分别表示字体的轻、重、正常（默认）
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
```

### 4.2.11 绘制点
<b>WxGLRegion.point(vs, color, size=None, **kwds)</b>
```
vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
color       - 顶点或顶点集颜色
				预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
				浮点型的元组或列表，值域范围：[0,1]，长度：3
				numpy.ndarray类型，shape=(3,)|(4,)|(n,3)|(n,4)
size        - 点的大小，整数，None表示使用当前设置
kwds        - 关键字参数
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
				program     - 着色器程序
```

### 4.2.12 绘制线段
<b>WxGLRegion.line(vs, color, method='SINGLE', width=None, stipple=None, **kwds)</b>
```
vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
color       - 顶点或顶点集颜色
				预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
				浮点型的元组或列表，值域范围：[0,1]，长度：3
				numpy.ndarray类型，shape=(3,)|(4,)|(n,3)|(n,4)
method      - 绘制方法
				'MULTI'     - 线段
				'SINGLE'    - 连续线段
				'LOOP'      - 闭合线段
width       - 线宽，0.0~10.0之间，None表示使用当前设置
stipple     - 线型，整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None表示使用当前设置
kwds        - 关键字参数
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
				program     - 着色器程序
```

### 4.2.13 绘制曲面
<b>WxGLRegion.surface(vs, color=None, texcoord=None, texture=None, method='Q', mode=None, **kwds)</b>
```
vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
color       - 顶点或顶点集颜色
				None表示仅使用纹理
				预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
				浮点型的元组或列表，值域范围：[0,1]，长度：3
				numpy.ndarray类型，shape=(3|4,)|(n,3|4)
texcoord    - 顶点的纹理坐标集，numpy.ndarray类型，shape=(n,2)
texture     - 2D纹理对象
method      - 绘制方法
				'Q'         - 四边形
								0--3 4--7
								|  | |  |
								1--2 5--6
				'T'         - 三角形
								0--2 3--5
								 \/   \/
								  1    4
				'Q+'        - 边靠边的连续四边形
							   0--2--4
							   |  |  |
							   1--3--5
				'T+'        - 边靠边的连续三角形
							   0--2--4
								\/_\/_\
								 1  3  5
				'F'         - 扇形
				'P'         - 多边形
mode        - 显示模式
				None        - 使用当前设置
				'FCBC'      - 前后面填充颜色FCBC
				'FLBL'      - 前后面显示线条FLBL
				'FCBL'      - 前面填充颜色，后面显示线条FCBL
				'FLBC'      - 前面显示线条，后面填充颜色FLBC
kwds        - 关键字参数
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
				program     - 着色器程序
				light       - 材质灯光颜色，None表示关闭材质灯光
```

### 4.2.14 绘制网格
<b>WxGLRegion.mesh(xs, ys, zs, color, method='Q', mode=None, **kwds)</b>
```
xs          - 顶点集的x坐标集，numpy.ndarray类型，shape=(rows,cols)
ys          - 顶点集的y坐标集，numpy.ndarray类型，shape=(rows,cols)
zs          - 顶点集的z坐标集，numpy.ndarray类型，shape=(rows,cols)
color       - 顶点或顶点集颜色
				预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
				浮点型的元组或列表，值域范围：[0,1]，长度：3
				numpy.ndarray类型，shape=(3|4,)|(rows,cols,3|4)
method      - 绘制方法：
				'Q'         - 四边形
				'T'         - 三角形
mode        - 显示模式
				None        - 使用当前设置
				'FCBC'      - 前后面填充颜色FCBC
				'FLBL'      - 前后面显示线条FLBL
				'FCBL'      - 前面填充颜色，后面显示线条FCBL
				'FLBC'      - 前面显示线条，后面填充颜色FLBC
kwds        - 关键字参数
				blc         - 边框的颜色，None表示无边框
				blw         - 边框宽度
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
				program     - 着色器程序
				light       - 材质灯光颜色，None表示关闭材质灯光
```

### 4.2.15 绘制球体
<b>WxGLRegion.sphere(center, radius, color, mode='FLBL', slices=60, **kwds)</b>
```
center      - 球心坐标，元组、列表或numpy数组
radius      - 半径，浮点型
color       - 表面颜色
mode        - 显示模式
				None        - 使用当前设置
				'FCBC'      - 前后面填充颜色FCBC
				'FLBL'      - 前后面显示线条FLBL
				'FCBL'      - 前面填充颜色，后面显示线条FCBL
				'FLBC'      - 前面显示线条，后面填充颜色FLBC
slices      - 锥面分片数（数值越大越精细）
kwds        - 关键字参数
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
				light       - 材质灯光开关
```

### 4.2.16 绘制六面体
<b>WxGLRegion.cube(center, side, color, mode='FLBL', **kwds)</b>
```
center      - 中心坐标，元组、列表或numpy数组
side        - 棱长，整型、浮点型，或长度为3的元组、列表、numpy数组
color       - 顶点或顶点集颜色
				预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
				浮点型的元组或列表，值域范围：[0,1]，长度：3
				numpy.ndarray类型，shape=(3|4,)|(rows,cols,3|4)
mode        - 显示模式
				None        - 使用当前设置
				'FCBC'      - 前后面填充颜色FCBC
				'FLBL'      - 前后面显示线条FLBL
				'FCBL'      - 前面填充颜色，后面显示线条FCBL
				'FLBC'      - 前面显示线条，后面填充颜色FLBC
kwds        - 关键字参数
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
				light       - 材质灯光开关
```

### 4.2.17 绘制圆锥体
<b>WxGLRegion.cone(center, spire, radius, color, slices=50, mode='FCBC', **kwds)</b>
```
center      - 锥底圆心坐标，元组、列表或numpy数组
spire       - 锥尖坐标，元组、列表或numpy数组
radius      - 锥底半径，浮点型
color       - 圆锥颜色
				预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
				浮点型的元组或列表，值域范围：[0,1]，长度：3
				numpy.ndarray类型，shape=(3,)
slices      - 锥面分片数（数值越大越精细）
mode        - 显示模式
				None        - 使用当前设置
				'FCBC'      - 前后面填充颜色FCBC
				'FLBL'      - 前后面显示线条FLBL
				'FCBL'      - 前面填充颜色，后面显示线条FCBL
				'FLBC'      - 前面显示线条，后面填充颜色FLBC
kwds        - 关键字参数
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
				light       - 材质灯光开关
```

### 4.2.18 绘制圆柱体
<b>WxGLRegion.cylinder(v_top, v_bottom, radius, color, slices=50, mode='FCBC', **kwds)</b>
```
v_top       - 圆柱上端面的圆心坐标，元组、列表或numpy数组
v_bottom    - 圆柱下端面的圆心坐标，元组、列表或numpy数组
radius      - 圆柱半径，浮点型
color       - 圆柱颜色
				预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
				浮点型的元组或列表，值域范围：[0,1]，长度：3
				numpy.ndarray类型，shape=(3|4,)|(2,3|4)
slices      - 圆柱面分片数（数值越大越精细）
mode        - 显示模式
				None        - 使用当前设置
				'FCBC'      - 前后面填充颜色FCBC
				'FLBL'      - 前后面显示线条FLBL
				'FCBL'      - 前面填充颜色，后面显示线条FCBL
				'FLBC'      - 前面显示线条，后面填充颜色FLBC
kwds        - 关键字参数
				headface    - 是否显示圆柱端面
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
```

### 4.2.19 绘制圆管线
<b>WxGLRegion.pipe(vs, radius, color, slices=36, mode='FCBC', **kwds)</b>
```
vs          - 圆管中心点坐标集，numpy.ndarray类型，shape=(n,3)
radius      - 圆管半径，浮点型
color       - 圆管颜色
				预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
				浮点型的元组或列表，值域范围：[0,1]，长度：3
				numpy.ndarray类型，shape=(3|4,)|(n,3|4)
slices      - 圆管面分片数（数值越大越精细）
mode        - 显示模式
				None        - 使用当前设置
				'FCBC'      - 前后面填充颜色FCBC
				'FLBL'      - 前后面显示线条FLBL
				'FCBL'      - 前面填充颜色，后面显示线条FCBL
				'FLBC'      - 前面显示线条，后面填充颜色FLBC
kwds        - 关键字参数
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
```

### 4.2.20 绘制囊（三维等值面）
<b>WxGLRegion.capsule(data, threshold, color, r_x=None, r_y=None, r_z=None, mode='FLBL', **kwds)</b>
```
data        - 数据集，numpy.ndarray类型，shape=(layers,rows,cols)
threshold   - 阈值，浮点型
color       - 表面颜色
r_x         - x的动态范围，元组
r_y         - y的动态范围，元组
r_z         - z的动态范围，元组
mode        - 显示模式
				None        - 使用当前设置
				'FCBC'      - 前后面填充颜色FCBC
				'FLBL'      - 前后面显示线条FLBL
				'FCBL'      - 前面填充颜色，后面显示线条FCBL
				'FLBC'      - 前面显示线条，后面填充颜色FLBC
kwds        - 关键字参数
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
				light       - 材质灯光开关
```

### 4.2.21 绘制体数据
<b>WxGLRegion.volume(data, x=None, y=None, z=None, method='Q', **kwds)</b>
```
data        - 顶点的颜色集，numpy.ndarray类型，shape=(layers,rows,cols,4)
x           - 顶点的x坐标集，numpy.ndarray类型，shape=(rows,cols)。缺省则使用volume的2轴索引构造
y           - 顶点的y坐标集，numpy.ndarray类型，shape=(rows,cols)。缺省则使用volume的1轴索引构造
z           - 顶点的z坐标集，numpy.ndarray类型，shape=(layers,)。缺省则使用volume的0轴索引构造
method      - 绘制方法：
				'Q'         - 四边形
				'T'         - 三角形
kwds        - 关键字参数
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
```

### 4.2.22 绘制坐标轴
<b>WxGLRegion.coordinate(length=1.0, xlabel=None, ylabel=None, zlabel=None, **kwds)</b>
```
length      - 坐标轴半轴长度，从-length到length
xlabel      - x轴标注
ylabel      - y轴标注
zlabel      - z轴标注
kwds        - 关键字参数
				half        - 是否画半轴
				slices      - 锥面分片数（数值越大越精细）
				label_size  - 标注文本的字号
				name        - 模型名
				inside      - 是否更新数据动态范围
				visible     - 是否显示
```

### 4.2.23 绘制colorBar
<b>WxGLRegion.colorbar(drange, cmap, loc='right', **kwds)</b>
```
drange      - 值域范围，tuple类型
cmap        - 调色板名称
loc         - 位置，top|bottom|left|right
kwds        - 关键字参数
				length          - ColorBar所在视区的长边长度，默认短边长度为1
				subject         - 标题
				subject_size    - 标题字号
				label_size      - 标注字号
				label_format    - 标注格式化所用lambda函数
				tick_line       - 刻度线长度
				endpoint        - 刻度是否包含值域范围的两个端点值
				name            - 模型名
				inside          - 是否更新数据动态范围
				visible         - 是否显示
```

### 4.2.24 绘制网格和刻度
<b>WxGLRegion.ticks(**kwds)</b>
```
kwds        - 关键字参数
				segment_min     - 标注最少分段数量
				segment_max     - 标注最多分段数量
				label_2D3D      - 标注试用2D或3D文字
				label_size      - 标注字号
				xlabel_format   - x轴标注格式化所用lambda函数
				ylabel_format   - y轴标注格式化所用lambda函数
				zlabel_format   - z轴标注格式化所用lambda函数
```

### 4.2.25 隐藏刻度网格
<b>WxGLRegion.hide_ticks()</b>
```
无参数
```

### 4.2.26 绘制2D网格和刻度
<b>WxGLRegion.ticks2d(**kwds)</b>
```
kwds        - 关键字参数
				segment_min     - 标注最少分段数量
				segment_max     - 标注最多分段数量
				label_2D3D      - 标注试用2D或3D文字
				label_size      - 标注字号
				xlabel_format   - x轴标注格式化所用lambda函数
				ylabel_format   - y轴标注格式化所用lambda函数
```

### 4.2.27 绘制流体
<b>WxGLRegion.flow(ps, us, vs, ws, **kwds)</b>
```
ps          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
us          - 顶点u分量集，numpy.ndarray类型，shape=(n,)
vs          - 顶点v分量集，numpy.ndarray类型，shape=(n,)
ws          - 顶点w分量集，numpy.ndarray类型，shape=(n,)
kwds        - 关键字参数
				color       - 轨迹线颜色，None表示使用速度映射颜色
				actor       - 顶点模型类型，'point'|'line'两个选项
				size        - point大小
				width       - line宽度
				length      - 轨迹线长度，以速度矢量的模为单位
				duty        - 顶点line模型长度与轨迹线长度之比（占空比），建议值为0.4
				frames      - 总帧数
				interval    - 帧间隔，以ms为单位
				threshold   - 高通阈值，滤除速度小于阈值的数据点
				name        - 模型名
```

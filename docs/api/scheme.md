---
sort: 6
---

# wxgl.Scheme

wxgl.Scheme(haxis='y', bg=(0.0,0.0,0.0)

应用于三维场景中的展示方案类。

```
haxis       - 高度轴，默认y轴，可选z轴，不支持x轴
bg          - 背景色，默认0.0, 0.0, 0.0)
```

## wxgl.Scheme.axes

wxgl.Scheme.axes(name=None)

绘制三维坐标轴。

```
name        - 部件名
```

## wxgl.Scheme.circle

wxgl.Scheme.circle(center, r, \*\*kwds)

绘制圆面或扇面。

```
center      - 圆心：元组、列表或numpy数组
r           - 半径：浮点型
kwds        - 关键字参数
    color       - 颜色：浮点型元组、列表或numpy数组
    arc         - 弧度角范围：默认0°~360°
    cell        - 网格精度：默认5°
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    opacity     - 模型不透明属性，默认不透明
    cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
    fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列
    light       - 光照模型（默认户外光照模型）
    name        - 模型或部件名
```

## wxgl.Scheme.colorbar

wxgl.Scheme.circle(data, cm='viridis', ff=str, endpoint=True)

绘制调色板。

```
data        - 值域范围或刻度序列：长度大于1的元组或列表
cm          - 调色板名称
kwds        - 关键字参数
ff          - 刻度标注格式化函数
endpoint    - 刻度是否包含值域范围的两个端点值
```

## wxgl.Scheme.cone

wxgl.Scheme.circle(spire, center, r, \*\*kwds)

绘制圆锥。

```
spire       - 锥尖：元组、列表或numpy数组
center      - 锥底圆心：元组、列表或numpy数组
r           - 锥底半径：浮点型
kwds        - 关键字参数
    color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
    arc         - 弧度角范围：默认0°~360°
    cell        - 网格精度：默认5°
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    opacity     - 模型不透明属性，默认不透明
    cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
    fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列
    light       - 光照模型（默认户外光照模型）
    name        - 模型或部件名
```

## wxgl.Scheme.cruise

wxgl.Scheme.cruise(func)

设置相机巡航函数。

```
func        - 以时间t（毫秒）为参数的函数，返回包含下述key的字典
    azim        - 方位角：None或表达式
    elev        - 高度角：None或表达式
    dist        - 相机到OES坐标系原定的距离：None或表达式
```

## wxgl.Scheme.cube

wxgl.Scheme.cube(center, side, \*\*kwds)

绘制立方体。

```
center      - 中心坐标，元组、列表或numpy数组
side        - 棱长：数值或长度为3的元组、列表、numpy数组
kwds        - 关键字参数
    color       - 颜色：浮点型元组、列表或numpy数组
    vec         - 立方体上表面法向量
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    opacity     - 模型不透明属性，默认不透明
    cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
    fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列
    light       - 光照模型（默认户外光照模型）
    name        - 模型或部件名
```

## wxgl.Scheme.cylinder

wxgl.Scheme.cylinder(c1, c2, r, \*\*kwds)

绘制圆柱。

```
c1          - 圆柱端面圆心：元组、列表或numpy数组
c2          - 圆柱端面圆心：元组、列表或numpy数组
r           - 圆柱半径：浮点型
kwds        - 关键字参数
    color       - 颜色：浮点型元组、列表或numpy数组
    arc         - 弧度角范围：默认0°~360°
    cell        - 网格精度：默认5°
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    opacity     - 模型不透明属性，默认不透明
    cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
    fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列
    light       - 光照模型（默认户外光照模型）
    name        - 模型或部件名
```

## wxgl.Scheme.grid

wxgl.Scheme.grid(\*\*kwds)

绘制网格和刻度。

```
kwds        - 关键字参数
    size        - 文本字号，默认32
    xlabel      - x轴名称
    ylabel      - y轴名称
    zlabel      - z轴名称
    xf          - x轴标注格式化函数
    yf          - y轴标注格式化函数
    zf          - z轴标注格式化函数
    name        - 部件名
```

## wxgl.Scheme.isosurface

wxgl.Scheme.isosurface(data, level, \*\*kwds)

绘制基于MarchingCube算法的三维等值面。

```
data        - 数据集：三维numpy数组
level       - 阈值：浮点型
kwds        - 关键字参数
    color       - 颜色：浮点型元组、列表或numpy数组
    xr          - 数据集对应的点的x轴的动态范围
    yr          - 数据集对应的点的y轴的动态范围
    zr          - 数据集对应的点的z轴的动态范围
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    opacity     - 模型不透明属性，默认不透明
    cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
    fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列
    light       - 光照模型（默认户外光照模型）
    name        - 模型或部件名
```

## wxgl.Scheme.line

wxgl.Scheme.line(vs, \*\*kwds)

绘制线段。

```
vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
kwds        - 关键字参数
    color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
    data        - 数据集：元组、列表或numpy数组，shape=(n,)
    cm          - 调色板
    width       - 线宽：0.0~10.0之间，None使用默认设置
    stipple     - 线型：整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None使用默认设置
    pair        - 顶点两两成对绘制多条线段，默认False
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列，默认None
    ambient     - 环境光，默认(1.0,1.0,1.0)
    name        - 模型或部件名
```

## wxgl.Scheme.mesh

wxgl.Scheme.mesh(xs, ys, zs, \*\*kwds)

绘制网格面。

```
xs/ys/zs    - 顶点坐标集：元组、列表或numpy数组，shape=(m,n)，m为网格行数，n为网格列数
kwds        - 关键字参数
    color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
    data        - 数据集：元组、列表或numpy数组，shape=(m,n)
    cm          - 调色板
    texture     - 纹理图片，或2D纹理对象
    quad        - 使用四角面构成网格面，默认False（使用三角面）
    ccw         - 顶点逆时针排序的面为正面，默认True
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    opacity     - 模型不透明属性，默认不透明
    cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
    fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列
    light       - 光照模型（默认户外光照模型）
    name        - 模型或部件名
```

## wxgl.Scheme.model

wxgl.Scheme.model(m, name=None)

添加模型。

```
m           - wxgl.Model类的实例
name        - 模型或部件名
```

## wxgl.Scheme.scatter

wxgl.Scheme.scatter(vs, \*\*kwds)

绘制散列点。

```
vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
kwds        - 关键字参数
    color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
    size        - 点的大小：数值或数值型元组、列表或numpy数组
    data        - 数据集：元组、列表或numpy数组，shape=(n,)
    cm          - 调色板
    texture     - 纹理图片，或2D纹理对象
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列，默认None
    ambient     - 环境光，默认(1.0,1.0,1.0)
    name        - 模型或部件名
```

## wxgl.Scheme.sphere

wxgl.Scheme.sphere(center, r, \*\*kwds)

绘制由经纬度网格生成的球。

```
center      - 锥底圆心坐标：元组、列表或numpy数组
r           - 锥底半径：浮点型
kwds        - 关键字参数
    color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
    vec         - 指向北极的向量
    uarc        - u方向范围：默认0°~360°
    varc        - v方向范围：默认-90°~90°
    cell        - 网格精度：默认5°
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    opacity     - 模型不透明属性，默认不透明
    cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
    fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列
    light       - 光照模型（默认户外光照模型）
    name        - 模型或部件名
```

## wxgl.Scheme.surface

wxgl.Scheme.surface(vs, \*\*kwds)

绘制由三角面（默认）或四角面构成的曲面。

```
vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
kwds        - 关键字参数
    color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
    data        - 数据集：元组、列表或numpy数组，shape=(n,)
    cm          - 调色板
    texture     - 纹理图片，或2D/2DArray/3D纹理对象
    texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
    quad        - 使用四角面构成曲面，默认False（使用三角面）
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    opacity     - 模型不透明属性，默认True（不透明）
    cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
    fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列
    light       - 光照模型（默认户外光照模型）
    name        - 模型或部件名
```

## wxgl.Scheme.text

wxgl.Scheme.text(text, pos, \*\*kwds)

绘制2D文字。

```
text        - 文本字符串
pos         - 文本位置：元组、列表或numpy数组，shape=(2|3,)
kwds        - 关键字参数
    color       - 文本颜色：浮预定义颜色、十六进制颜色，或者点型元组、列表或numpy数组，None表示背景色的对比色
    size        - 字号：整型，默认32
    align       - 水平对齐方式：'left'-左对齐（默认），'center'-水平居中，'right'-右对齐
    valign      - 垂直对齐方式：'bottom'-底部对齐（默认），'middle'-垂直居中，'top'-顶部对齐
    family      - 字体：None表示当前默认的字体
    weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    slide       - 幻灯片函数，默认None
    ambient     - 环境光，默认(1.0,1.0,1.0)
    name        - 模型或部件名
```

## wxgl.Scheme.text3d

wxgl.Scheme.text3d(text, box, \*\*kwds)

绘制3D文字。

```
text        - 文本字符串
box         - 文本显示区域：左上、左下、右下、右上4个点的坐标，浮点型元组、列表或numpy数组，shape=(4,2|3)
kwds        - 关键字参数
    color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
    bg          - 背景色，None表示背景透明
    align       - 对齐方式：'left'-左对齐（默认），'center'-水平居中，'right'-右对齐，'fill'-填充
    family      - 字体：None表示当前默认的字体
    weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
    size        - 字号：整型，默认64。此参数影响文本显示质量，不改变文本大小
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列，默认None
    light       - 光照模型（默认基础光照模型）
    name        - 模型或部件名
```

## wxgl.Scheme.title

wxgl.Scheme.title(title, size=32, color=None, family=None, weight='normal')

设置标题。

```
title       - 标题文本
size        - 字号：整型，默认32
color       - 颜色或颜色集：预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组，值域范围[0,1]
family      - 字体：None表示当前默认的字体
weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
```

## wxgl.Scheme.torus

wxgl.Scheme.torus(center, r1, r2, \*\*kwds)

绘制球环。

```
center      - 球环中心坐标：元组、列表或numpy数组
r1          - 球半径：浮点型
r2          - 环半径：浮点型
kwds        - 关键字参数
    color       - 颜色：浮点型元组、列表或numpy数组
    vec         - 环面法向量
    uarc        - u方向范围：默认0°~360°
    varc        - v方向范围：默认0°~360°
    cell        - 网格精度：默认5°
    visible     - 是否可见，默认True
    inside      - 模型顶点是否影响模型空间，默认True
    opacity     - 模型不透明属性，默认不透明
    cull        - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
    fill        - 填充，可选项：True, False, None（默认，表示使用当前设置） 
    slide       - 幻灯片函数，默认None
    transform   - 由旋转、平移和缩放组成的模型几何变换序列
    light       - 光照模型（默认户外光照模型）
    name        - 模型或部件名
```

## wxgl.Scheme.xrange

wxgl.Scheme.xrange(range_tuple)

设置x轴范围。

```
range_tuple - x轴最小值和最大值组成的元祖
```

## wxgl.Scheme.yrange

wxgl.Scheme.yrange(range_tuple)

设置y轴范围。

```
range_tuple - y轴最小值和最大值组成的元祖
```

## wxgl.Scheme.zrange

wxgl.Scheme.zrange(range_tuple)

设置z轴范围。

```
range_tuple - z轴最小值和最大值组成的元祖
```


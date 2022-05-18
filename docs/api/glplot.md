---
sort: 6
---

# wxgl.glplot

3D绘图工具包。

## wxgl.glplot.figure

**wxgl.glplot.figure(\*\*kwds)**

初始化当前画布，无返回值。参数说明如下：

```
proj        - 投影模式：'O' - 正射投影，'P' - 透视投影（默认）
zoom        - 视口缩放因子：默认1.0
azim        - 方位角：默认0°
elev        - 仰角：默认0°
azim_range  - 方位角限位器：默认-180°~180°
elev_range  - 仰角限位器：默认-180°~180°
smooth      - 反走样开关：默认True
style       - 场景风格
                'blue'      - 太空蓝（默认）
                'gray'      - 国际灰
                'white'     - 珍珠白
                'black'     - 石墨黑
                'royal'     - 宝石蓝
```

## wxgl.glplot.subplot

**wxgl.glplot.subplot(pos)**

添加子图（Axes）对象。参数说明如下：

```
pos         - 子图在场景中的位置和大小
                三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                四元组      - 子图左下角在画布上的水平、垂直位置和子图的宽度、高度。以画布左下角为原点，画布宽度和高度都是1
```

## wxgl.glplot.show

**wxgl.glplot.show()**

显示画布。无参数。

## wxgl.glplot.savefig

**wxgl.glplot.savefig(fn)**

保存画布为文件。参数说明如下：

```
fn         	- 文件名，支持.png和.jpg格式
```

## wxgl.glplot.capture

**wxgl.glplot.capture(out_file, fps=25, fn=50, loop=0)**

生成mp4、avi、wmv或gif文件。参数说明如下：

```
out_file    - 输出文件名，可带路径，支持gif和mp4、avi、wmv等格式
fps         - 每秒帧数
fn          - 总帧数
loop        - 循环播放次数（仅gif格式有效，0表示无限循环）
```

## wxgl.glplot.cruise

**wxgl.glplot.cruise(func)**

设置相机巡航函数。参数说明如下：

```
func        - 以渲染时长（ms）为参数的函数，返回一个字典，'azim'键为相机方位角，'elev'键为相机高度角，'dist'键为相机距离视点的距离
```

## wxgl.glplot.title

**wxgl.glplot.title(text, size=40, color=None, \*\*kwds)**

位于Axes顶部水平居中的标题。参数说明如下：

```
text        - 文本字符串：支持LaTex语法
size        - 字号：整型，默认40
color       - 文本颜色：支持预定义颜色、十六进制颜色，以及值域范围[0,1]的浮点型元组、列表或numpy数组颜色，默认使用场景的前景颜色
kwds        - 关键字参数
                family          - 字体，None表示当前默认的字体
                weight          - 字体的浓淡：'normal'-正常，'light'-轻，'bold'-重（默认）
                border          - 显示标题边框，默认True
                margin_top      - 标题上方留空与标题文字高度之比，默认0.6
                margin_bottom   - 标题下方留空与标题文字高度之比，默认0.2
                margin_left     - 标题左侧留空与标题文字高度之比，默认0.0
                margin_right    - 标题右侧留空与标题文字高度之比，默认0.0
```

## wxgl.glplot.colorbar

**wxgl.glplot.colorbar(cm, drange, loc='right', \*\*kwds)**

Colorbar。参数说明如下：

```
cm          - 调色板名称
drange      - 数据的动态范围：元组、列表或numpy数组
loc         - 位置
                right           - 右侧
                bottom          - 底部
kwds        - 关键字参数
                subject         - 标题
                tick_format     - 刻度标注格式化函数，默认str
                density         - 刻度密度，最少和最多刻度线组成的元组，默认(3,6)
                endpoint        - 刻度是否包含值域范围的两个端点值
                scale           - 色条宽度、文字大小等缩放比例，默认None
                margin_left     - 色条左侧留空，默认0.5
                margin_right    - 色条右侧留空，默认0.5
                margin_top      - 色条上方留空，默认0.5
                margin_bottom   - 色条下方留空，默认0.5
```

## wxgl.glplot.grid

**wxgl.glplot.grid(xlabel='X', ylabel='Y', zlabel='Z', \*\*kwds)**

绘制网格和刻度。参数说明如下：

```
xlabel      - x轴名称，默认'X'
ylabel      - y轴名称，默认'Y'
zlabel      - z轴名称，默认'Z'
kwds        - 关键字参数
                xf              - x轴刻度标注格式化函数，默认str
                yf              - y轴刻度标注格式化函数，默认str
                zf              - z轴刻度标注格式化函数，默认str
                xd              - x轴刻度密度调整，整型，-1~3，默认0
                yd              - y轴刻度密度调整，整型，-1~3，默认0
                zd              - z轴刻度密度调整，整型，-1~3，默认0
                xc              - x轴标注文本颜色，默认(1.0,0.3,0)
                yc              - y轴标注文本颜色，默认(0,1.0,0.3)
                zc              - z轴标注文本颜色，默认(0,0.5,1.0)
                lc              - 网格线颜色，默认使用前景色
                tick_size       - 刻度标注字号，默认32
                label_size      - 坐标轴标注字号，默认40
```

## wxgl.glplot.xrange

**wxgl.glplot.xrange(xrange)**

设置x轴范围。参数说明如下：

```
xrange     	- x轴范围：2元组
```

## wxgl.glplot.yrange

**wxgl.glplot.yrange(yrange)**

设置y轴范围。参数说明如下：

```
yrange     	- y轴范围：2元组
```

## wxgl.glplot.zrange

**wxgl.glplot.zrange(zrange)**

设置z轴范围。参数说明如下：

```
zrange     	- z轴范围：2元组
```

## wxgl.glplot.model

**wxgl.glplot.model(m)**

绘制wxgl.Model模型。参数说明如下：

```
m          	- wxgl.Model实例
```

## wxgl.glplot.text

**wxgl.glplot.text(text, pos, color=None, size=32, loc='left_bottom', \*\*kwds)**

2d文字。参数说明如下：

```
text        - 文本字符串
pos         - 文本位置：元组、列表或numpy数组，shape=(2|3,)
color       - 文本颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色，默认使用场景的前景颜色
size        - 字号：整型，默认32
loc         - pos对应文本区域的位置
                'left-top'      - 左上
                'left-middle'   - 左中
                'left-bottom'   - 左下
                'center-top'    - 上中
                'center-middle' - 中
                'center-bottom' - 下中
                'right-top'     - 右上
                'right-middle'  - 右中
                'right-bottom'  - 右下
kwds        - 关键字参数
                name            - 模型名
			    visible         - 是否可见，默认True
                slide           - 幻灯片函数，默认None
                family          - 字体：None表示当前默认的字体
                weight          - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
```

## wxgl.glplot.text3d

**wxgl.glplot.text3d(text, box, color=None, align='fill', valign='fill', \*\*kwds)**

3d文字。参数说明如下：

```
text        - 文本字符串
box         - 文本显式区域：左上、左下、右上、右下4个点的坐标，浮点型元组、列表或numpy数组，shape=(4,2|3)
color       - 文本颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色，默认使用场景的前景颜色
align       - 文本宽度方向对齐方式
                'fill'          - 填充
                'left'          - 左对齐
                'right'         - 右对齐
                'center'        - 居中对齐
valign      - 文本高度方向对齐方式
                'fill'          - 填充
                'top'           - 上对齐
                'bottom'        - 下对齐
                'middle'        - 居中对齐
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
                ambient         - 环境光，默认(1.0,1.0,1.0)
                family          - 字体：None表示当前默认的字体
                weight          - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
                size            - 字号：整型，默认64。此参数影响文本显示质量，不改变文本大小
```

## wxgl.glplot.point

**wxgl.glplot.point(vs, color=None, cm=None, alpha=None, size=1.0, \*\*kwds)**

散列点。参数说明如下：

```
vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
color       - 颜色或数据：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色；若为数据，其长度等于顶点数量
cm          - 颜色映射表：默认None。若该参数有效，color参数被视为与顶点一一对应的数据
alpha       - 透明度：None或0到1之间的浮点数（cm有效时有效）。默认None，表示不改变当前透明度
size        - 点的大小：数值或数值型元组、列表或numpy数组
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
```

## wxgl.glplot.line

**wxgl.glplot.line(vs, color=None, cm=None, alpha=None, width=None, style='solid', method='strip', \*\*kwds)**

线段。参数说明如下：

```
vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
color       - 颜色或数据：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色；若为数据，其长度等于顶点数量
cm          - 颜色映射表：默认None。若该参数有效，color参数被视为与顶点一一对应的数据
alpha       - 透明度：None或0到1之间的浮点数（cm有效时有效）。默认None，表示不改变当前透明度
width       - 线宽：0.0~10.0之间，None使用默认设置
style       - 线型, 默认实线
                'solid'         - 实线 
                'dashed'        - 虚线
                'dotted'        - 点线
                'dash-dot'      - 虚点线
method      - 绘制方法
                'isolate'       - 独立线段
                'strip'         - 连续线段
                'loop'          - 闭合线段
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认True（不透明）
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
                ambient         - 环境光，默认(1.0,1.0,1.0)
```

## wxgl.glplot.surface

**wxgl.glplot.surface(vs, color=None, cm=None, alpha=None, texture=None, texcoord=None, method='isolate', indices=None, closed=False, \*\*kwds)**

三角曲面。参数说明如下：

```
vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
color       - 颜色或数据：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色；若为数据，其长度等于顶点数量
cm          - 颜色映射表：默认None。若该参数有效，color参数被视为与顶点一一对应的数据
alpha       - 透明度：None或0到1之间的浮点数（cm有效时有效）。默认None，表示不改变当前透明度
texture     - 纹理：wxgl.Texture对象
texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
method      - 绘制方法
                'isolate'       - 独立三角面
                'strip'         - 带状三角面
                'fan'           - 扇面
indices     - 顶点索引集，默认None，表示不使用索引
closed      - 带状三角面或扇面两端闭合：布尔型
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认True（不透明）
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列
                light           - 光照情景模式，默认太阳光照情景模式
```

## wxgl.glplot.quad

**wxgl.glplot.quad(vs, color=None, cm=None, alpha=None, texture=None, texcoord=None, method='isolate', indices=None, closed=False, \*\*kwds)**

四角曲面。参数说明如下：

```
vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
color       - 颜色或数据：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色；若为数据，其长度等于顶点数量
cm          - 颜色映射表：默认None。若该参数有效，color参数被视为与顶点一一对应的数据
alpha       - 透明度：None或0到1之间的浮点数（cm有效时有效）。默认None，表示不改变当前透明度
texture     - 纹理：wxgl.Texture对象
texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
method      - 绘制方法
                'isolate'       - 独立四角面
                'strip'         - 带状四角面
indices     - 顶点索引集，默认None，表示不使用索引
closed      - 带状三角面或扇面两端闭合：布尔型
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认True（不透明）
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列
                light           - 光照情景模式，默认太阳光照情景模式
```

## wxgl.glplot.mesh

**wxgl.glplot.mesh(xs, ys, zs, color=None, cm=None, alpha=None, texture=None, ur=(0,1), vr=(0,1), method='T', uclosed=False, vclosed=False, \*\*kwds)**

网格面。参数说明如下：

```
xs/ys/zs    - 顶点坐标集：元组、列表或numpy数组，shape=(m,n)，m为网格行数，n为网格列数
color       - 颜色或数据：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色；若为数据，shape=(m,n)
cm          - 颜色映射表：默认None。若该参数有效，color参数被视为与mesh网格匹配的数据
alpha       - 透明度：None或0到1之间的浮点数（cm有效时有效）。默认None，表示不改变当前透明度
texture     - 纹理：wxgl.Texture对象
ur          - u方向纹理坐标范围
vr          - v方向纹理坐标范围
method      - 绘制网格的方法：可选项：'T'- GL_TRIANGLES, 'Q' - GL_QUADS
uclosed     - u方向网格两端闭合：布尔型
vclosed     - v方向网格两端闭合：布尔型
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认不透明
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列
                light           - 光照情景模式，默认太阳光照情景模式
```

## wxgl.glplot.cylinder

**wxgl.glplot.cylinder(c1, c2, r, color=None, texture=None, ur=(0,1), vr=(0,1), arc=(0,360), cell=5, \*\*kwds)**

圆柱。参数说明如下：

```
c1          - 圆柱端面圆心：元组、列表或numpy数组
c2          - 圆柱端面圆心：元组、列表或numpy数组
r           - 圆柱半径：浮点型
color       - 颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色
texture     - 纹理：wxgl.Texture对象
ur          - u方向纹理坐标范围
vr          - v方向纹理坐标范围
arc         - 弧度角范围：默认0°~360°
cell        - 网格精度：默认5°
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认不透明
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列
                light           - 光照情景模式，默认太阳光照情景模式
```

## wxgl.glplot.torus

**wxgl.glplot.torus(center, r1, r2, vec=(0,1,0), color=None, texture=None, ur=(0,1), vr=(0,1), u=(0,360), v=(-180,180), cell=5, \*\*kwds)**

球环。参数说明如下：

```
center      - 球环中心坐标：元组、列表或numpy数组
r1          - 球半径：浮点型
r2          - 环半径：浮点型
vec         - 环面法向量
color       - 颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色
texture     - 纹理：wxgl.Texture对象
ur          - u方向纹理坐标范围
vr          - v方向纹理坐标范围
u           - u方向范围：默认0°~360°
v           - v方向范围：默认-90°~90°
cell        - 网格精度：默认5°
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认不透明
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列
                light           - 光照情景模式，默认太阳光照情景模式
```

## wxgl.glplot.uvsphere

**wxgl.glplot.uvsphere(center, r, vec=(0,1,0), color=None, texture=None, ur=(0,1), vr=(0,1), u=(0,360), v=(-90,90), cell=5, \*\*kwds)**

使用经纬度网格生成球。参数说明如下：

```
center      - 锥底圆心坐标：元组、列表或numpy数组
r           - 锥底半径：浮点型
vec         - 轴向量
color       - 颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色
texture     - 纹理：wxgl.Texture对象
ur          - u方向纹理坐标范围
vr          - v方向纹理坐标范围
u           - u方向范围：默认0°~360°
v           - v方向范围：默认-90°~90°
cell        - 网格精度：默认5°
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认不透明
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列
                light           - 光照情景模式，默认太阳光照情景模式
```

## wxgl.glplot.isosphere

**wxgl.glplot.isosphere(center, r, color=None, iterations=5, \*\*kwds)**

通过对正八面体的迭代细分生成球。参数说明如下：

```
center      - 锥底圆心坐标：元组、列表或numpy数组
r           - 锥底半径：浮点型
color       - 颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色
iterations  - 迭代次数：整型
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认不透明
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列
                light           - 光照情景模式，默认太阳光照情景模式
```

## wxgl.glplot.circle

**wxgl.glplot.circle(center, r, vec=(0,1,0), color=None, arc=(0,360), cell=5, \*\*kwds)**

圆。参数说明如下：

```
center      - 锥底圆心：元组、列表或numpy数组
r           - 锥底半径：浮点型
vec         - 圆面法向量
color       - 颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色
arc         - 弧度角范围：默认0°~360°
cell        - 网格精度：默认5°
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认不透明
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列
				light           - 光照情景模式，默认太阳光照情景模式
```

## wxgl.glplot.cone

**wxgl.glplot.cone(spire, center, r, color=None, arc=(0,360), cell=5, \*\*kwds)**

圆锥。参数说明如下：

```
spire       - 锥尖：元组、列表或numpy数组
center      - 锥底圆心：元组、列表或numpy数组
r           - 锥底半径：浮点型
color       - 颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色
arc         - 弧度角范围：默认0°~360°
cell        - 网格精度：默认5°
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认不透明
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列
				light           - 光照情景模式，默认太阳光照情景模式
```

## wxgl.glplot.cube

**wxgl.glplot.cube(center, side, vec=(0,1,0), color=None, \*\*kwds)**

六面体。参数说明如下：

```
center      - 中心坐标，元组、列表或numpy数组
side        - 棱长：数值或长度为3的元组、列表、numpy数组
vec         - 六面体上表面法向量
color       - 颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认不透明
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列
                light           - 光照情景模式，默认太阳光照情景模式
```

## wxgl.glplot.isosurface

**wxgl.glplot.isosurface(data, level, color=None, x=None, y=None, z=None, \*\*kwds)**

基于MarchingCube算法的三维等值面。参数说明如下：

```
data        - 数据集：三维numpy数组
level       - 阈值：浮点型
color       - 颜色：支持预定义颜色、十六进制颜色，以及元组、列表或numpy数组颜色
x/y/z       - 数据集对应的点的x/y/z轴的动态范围
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认不透明
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列
                light           - 光照情景模式，默认太阳光照情景模式
```

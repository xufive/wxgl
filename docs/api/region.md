---
sort: 8
---

# wxgl.Region

**wxgl.Region(scene, box, \*\*kwds)**

视区类。参数说明如下：

```
scene       - 视区所属场景对象
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

## wxgl.Region.reset_box

**wxgl.Region.reset_box(box=None)**

重置视区位置和大小。参数说明如下：

```
box         - 视区位置四元组：四个元素分别表示视区左下角坐标、宽度、高度，元素值域[0,1]
```

## wxgl.Region.clear

**wxgl.Region.clear()**

清空视区。无参数。

## wxgl.Region.set_range

**wxgl.Region.set_range(r_x=None, r_y=None, r_z=None)**

设置坐标轴范围。参数说明如下：

```
r_x         - 二元组，x坐标轴范围
r_y         - 二元组，y坐标轴范围
r_z         - 二元组，z坐标轴范围
```

## wxgl.Region.set_cam_cruise

**wxgl.Region.set_cam_cruise(func)**

设置相机巡航函数。参数说明如下：

```
func        - 以渲染时长（ms）为参数的函数，返回一个字典，'azim'键为相机方位角，'elev'键为相机高度角，'dist'键为相机距离视点的距离
```

## wxgl.Region.save_posture

**wxgl.Region.save_posture()**

保存相机姿态。无参数。

## wxgl.Region.restore_posture

**wxgl.Region.restore_posture()**

还原相机姿态。无参数。

## wxgl.Region.set_model_visible

**wxgl.Region.set_model_visible(name, visible)**

设置模型显示属性。参数说明如下：

```
name        - 模型名
visible     - 布尔值
```

## wxgl.Region.show_model

**wxgl.Region.show_model(name)**

显示模型。参数说明如下：

```
name        - 模型名
```

## wxgl.Region.hide_model

**wxgl.Region.hide_model(name)**

隐藏模型。参数说明如下：

```
name        - 模型名
```

## wxgl.Region.drop_model

**wxgl.Region.drop_model(name)**

删除模型。参数说明如下：

```
name        - 模型名
```

## wxgl.Region.add_model

**wxgl.Region.add_model(m, name=None)**

添加模型。参数说明如下：

```
m           - wxgl.Model实例
name        - 模型名
```

## wxgl.Region.text

**wxgl.Region.text(text, pos, color=None, size=32, loc='left_bottom', \*\*kwds)**

2d文字。参数说明如下：

```
text        - 文本字符串
pos         - 文本位置：元组、列表或numpy数组，shape=(2|3,)
color       - 文本颜色：浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用场景默认的前景颜色
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
                inside          - 模型顶点是否影响模型空间，默认True
                slide           - 幻灯片函数，默认None
                ambient         - 环境光，默认(1.0,1.0,1.0)
                family          - 字体：None表示当前默认的字体
                weight          - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
```

## wxgl.Region.text3d

**wxgl.Region.text3d(text, box, color=None, align='fill', valign='fill', \*\*kwds)**

3d文字。参数说明如下：

```
text        - 文本字符串
box         - 文本显式区域：左上、左下、右上、右下4个点的坐标，浮点型元组、列表或numpy数组，shape=(4,2|3)
color       - 文本颜色：浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用场景默认的前景颜色
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
                cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
                ambient         - 环境光，默认(1.0,1.0,1.0)
                family          - 字体：None表示当前默认的字体
                weight          - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
                size            - 字号：整型，默认64。此参数影响文本显示质量，不改变文本大小
```

## wxgl.Region.point

**wxgl.Region.point(vs, color=None, size=1.0, \*\*kwds)**

散列点。参数说明如下：

```
vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
size        - 点的大小：数值或数值型元组、列表或numpy数组
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                opacity         - 模型不透明属性，默认True（不透明）
                inside          - 模型顶点是否影响模型空间，默认True
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
                ambient         - 环境光，默认(1.0,1.0,1.0)
```

## wxgl.Region.line

**wxgl.Region.line(vs, color=None, method='strip', width=None, stipple=None, \*\*kwds)**

线段。参数说明如下：

```
vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
method      - 绘制方法
                'isolate'       - 独立线段
                'strip'         - 连续线段
                'loop'          - 闭合线段
width       - 线宽：0.0~10.0之间，None使用默认设置
stipple     - 线型：整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None使用默认设置
kwds        - 关键字参数
                name            - 模型名
                visible         - 是否可见，默认True
                inside          - 模型顶点是否影响模型空间，默认True
                opacity         - 模型不透明属性，默认True（不透明）
                slide           - 幻灯片函数，默认None
                transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
                ambient         - 环境光，默认(1.0,1.0,1.0)
```

## wxgl.Region.surface

**wxgl.Region.surface(vs, color=None, texture=None, texcoord=None, method='isolate', indices=None, closed=False, \*\*kwds)**

三角曲面。参数说明如下：

```
vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
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

## wxgl.Region.quad

**wxgl.Region.quad(vs, color=None, texture=None, texcoord=None, method='isolate', indices=None, closed=False, \*\*kwds)**

四角曲面。参数说明如下：

```
vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
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

## wxgl.Region.mesh

**wxgl.Region.mesh(xs, ys, zs, color=None, texture=None, ur=(0,1), vr=(0,1), method='T', uclosed=False, vclosed=False, \*\*kwds)**

网格面。参数说明如下：

```
xs/ys/zs    - 顶点坐标集：元组、列表或numpy数组，shape=(m,n)，m为网格行数，n为网格列数
color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
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

## wxgl.Region.cylinder

**wxgl.Region.cylinder(c1, c2, r, color=None, texture=None, ur=(0,1), vr=(0,1), arc=(0,360), cell=5, \*\*kwds)**

圆柱。参数说明如下：

```
c1          - 圆柱端面圆心：元组、列表或numpy数组
c2          - 圆柱端面圆心：元组、列表或numpy数组
r           - 圆柱半径：浮点型
color       - 颜色：浮点型元组、列表或numpy数组
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

## wxgl.Region.torus

**wxgl.Region.torus(center, r1, r2, vec=(0,1,0), color=None, texture=None, ur=(0,1), vr=(0,1), u=(0,360), v=(-180,180), cell=5, \*\*kwds)**

球环。参数说明如下：

```
center      - 球环中心坐标：元组、列表或numpy数组
r1          - 球半径：浮点型
r2          - 环半径：浮点型
vec         - 环面法向量
color       - 颜色：浮点型元组、列表或numpy数组
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

## wxgl.Region.uvsphere

**wxgl.Region.uvsphere(center, r, vec=(0,1,0), color=None, texture=None, ur=(0,1), vr=(0,1), u=(0,360), v=(-90,90), cell=5, \*\*kwds)**

使用经纬度网格生成球。参数说明如下：

```
center      - 锥底圆心坐标：元组、列表或numpy数组
r           - 锥底半径：浮点型
vec         - 轴向量
color       - 颜色：浮点型元组、列表或numpy数组
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

## wxgl.Region.isosphere

**wxgl.Region.isosphere(center, r, color=None, iterations=5, \*\*kwds)**

通过对正八面体的迭代细分生成球。参数说明如下：

```
center      - 锥底圆心坐标：元组、列表或numpy数组
r           - 锥底半径：浮点型
color       - 颜色：浮点型元组、列表或numpy数组
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

## wxgl.Region.circle

**wxgl.Region.circle(center, r, vec=(0,1,0), color=None, arc=(0,360), cell=5, \*\*kwds)**

圆。参数说明如下：

```
center      - 锥底圆心：元组、列表或numpy数组
r           - 锥底半径：浮点型
vec         - 圆面法向量
color       - 颜色：浮点型元组、列表或numpy数组
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

## wxgl.Region.cone

**wxgl.Region.cone(spire, center, r, color=None, arc=(0,360), cell=5, \*\*kwds)**

圆锥。参数说明如下：

```
spire       - 锥尖：元组、列表或numpy数组
center      - 锥底圆心：元组、列表或numpy数组
r           - 锥底半径：浮点型
color       - 颜色：浮点型元组、列表或numpy数组
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

## wxgl.Region.cube

**wxgl.Region.cube(center, side, vec=(0,1,0), color=None, \*\*kwds)**

六面体。参数说明如下：

```
center      - 中心坐标，元组、列表或numpy数组
side        - 棱长：数值或长度为3的元组、列表、numpy数组
vec         - 六面体上表面法向量
color       - 颜色：浮点型元组、列表或numpy数组
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

## wxgl.Region.isosurface

**wxgl.Region.isosurface(data, level, color=None, x=None, y=None, z=None, \*\*kwds)**

基于MarchingCube算法的三维等值面。参数说明如下：

```
data        - 数据集：三维numpy数组
level       - 阈值：浮点型
color       - 颜色：浮点型元组、列表或numpy数组
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

## wxgl.Region.colorbar

**wxgl.Region.colorbar(cm, drange, box, mode='V', \*\*kwds)**

ColorBar。参数说明如下：

```
cm          - 调色板名称
drange      - 值域范围或刻度序列：长度大于1的元组或列表
box         - 调色板位置：左上、左下、右上、右下的坐标
mode        - 水平或垂直模式：可选项：'H'|'V'
kwds        - 关键字参数
                subject         - 标题
                tick_format     - 刻度标注格式化函数，默认str
                density         - 刻度密度，最少和最多刻度线组成的元组，默认(3,6)
                endpoint        - 刻度是否包含值域范围的两个端点值
```

## wxgl.Region.grid

**wxgl.Region.grid(xlabel='X', ylabel='Y', zlabel='Z', \*\*kwds)**

绘制网格和刻度。参数说明如下：

```
xlabel      - x轴名称，默认'X'
ylabel      - y轴名称，默认'Y'
zlabel      - z轴名称，默认'Z'
kwds        - 关键字参数
                xf              - x轴刻度标注格式化函数，默认str
                yf              - y轴刻度标注格式化函数，默认str
                zf              - z轴刻度标注格式化函数，默认str
                xd              - x轴刻度密度调整，整型，值域范围[-2,10], 默认0
                yd              - y轴刻度密度调整，整型，值域范围[-2,10], 默认0
                zd              - z轴刻度密度调整，整型，值域范围[-2,10], 默认0
                xc              - x轴标注文本颜色，默认(1.0,0.3,0)
                yc              - y轴标注文本颜色，默认(0,1.0,0.3)
                zc              - z轴标注文本颜色，默认(0,0.5,1.0)
                lc              - 网格线颜色，默认使用前景色
                tick_size       - 刻度标注字号，默认32
                label_size      - 坐标轴标注字号，默认40
```

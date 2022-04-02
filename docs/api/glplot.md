---
sort: 6
---

# wxgl.glplot

3D绘图工具包。


## wxgl.glplot.figure

**wxgl.glplot.figure(\*\*kwds)**

初始化当前画布，无返回值。参数说明如下：

```
proj        - 投影模式，默认透视投影
                'frustum'   - 透视投影
                'ortho'     - 正射投影
zoom        - 视口缩放因子，默认1.0
azim        - 方位角，默认0°
elev        - 仰角，默认0°
azim_range  - 方位角限位器，默认-180°~180°
elev_range  - 仰角限位器，默认-180°~180°
smooth      - 直线、多边形和点的反走样开关
style       - 场景风格，默认太空蓝
                'blue'      - 太空蓝
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



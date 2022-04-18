---
sort: 4
---

# 画布参数

以下面的方式导入wxgl.glplot子模块之后，默认的画布就已经被创建，一个和画布同样大小的子图也被同步创建。用户可以直接在此画布的当前子图上绘制3D模型。


```python
import wxgl.glplot as glt
```

此时，画布默认的尺寸（size）为1152x648像素，默认的背景色（style）是太空蓝，相机默认的投影方式（proj）为透视投影，默认的的方位角（azim）和高度角（elev）都是0°，默认的的方位角限位器（azim_range）和高度角限位器（elev_range）都是-180°~180°。

方位角是相机位置与视点坐标系原点连线在xOz平面上的投影和z轴正方向的夹角，遵从右手定则（右手握拳，伸开拇指，拇指指向y轴正方向，其余四指指向方位角的正方向）。高度角是相机位置与视点坐标系原点连线与xOz平面的夹角，相机俯视时高度角为正。

方位角限位器（azim_range）和高度角限位器（elev_range）用来设置相机的方位角和高度角的动态范围。

通常显卡对于OpenGL都有很好的兼容性，因此画布默认开启反走样（smooth）。如果模型渲染出现非期望的网格，请尝试关闭反走样（将smooth设置为False）。

在调用wxgl.glplot其他函数之前，使用wxgl.glplot.figure可以改变画布的默认参数。例如：

```
glt.figure(size=(1600,960), azim=30, elev=20, elev_range=(-90,90), smooth=False)
```




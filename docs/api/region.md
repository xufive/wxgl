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


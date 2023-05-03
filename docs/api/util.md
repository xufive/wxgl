---
sort: 2
---

# 函数

## wxgl.font_list

wxgl.font_list()

返回可用字体列表。

## wxgl.color_list

wxgl.color_list()

返回可用颜色列表。

## wxgl.cm_list

wxgl.cm_list()

返回颜色映射方案（调色板）列表。

## wxgl.cmap

wxgl.cmap(data, cm, drange=None, alpha=None, invalid=np.nan, invalid_c=(0,0,0,0))

数据映射为颜色。

```
data        - 数据
cm          - 颜色映射方案（调色板）
drange      - 数据动态范围，None表示使用data的动态范围
alpha       - 透明度，None表示不改变当前透明度
invalid     - 无效数据的标识，默认nan
invalid_c   - 无效数据的颜色，默认(0,0,0,0)
```

## wxgl.read_pcfile

wxgl.read_pcfile(pcfile)

读取.ply和.pcd格式的点云文件，返回一个PointCloudData类实例，该实例有以下属性：

* PointCloudData.ok         - 数据是否可用，布尔型
* PointCloudData.info       - 数据可用性说明，字符串
* PointCloudData.raw        - 解读出来的原始数据，字典
* PointCloudData.fields     - 数据字段（项）名称，列表
* PointCloudData.xyz        - 点的坐标数据，None或者numpy数组（ndarray）
* PointCloudData.rgb        - 点的颜色数据，None或者numpy数组（ndarray）
* PointCloudData.intensity  - 点的强度数据，None或者numpy数组（ndarray）


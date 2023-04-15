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


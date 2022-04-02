---
sort: 2
---

# util

WxGL工具包。


## wxgl.font_list

**wxgl.font_list()**

返回可用字体列表。无参数。


## wxgl.color_list

**wxgl.color_list()**

返回可用颜色列表。无参数。


## wxgl.color_help

**wxgl.color_help()**

返回可用颜色中英文对照表。无参数。


## wxgl.cmap_list

**wxgl.cmap_list()**

返回颜色映射方案列表。无参数。


## wxgl.cmap_help

**wxgl.cmap_help()**

返回颜色映射方案分类列表。无参数。


## wxgl.cmap

**wxgl.cmap(data, cm, invalid=np.nan, invalid_c=(0,0,0,0), drange=None, alpha=None, drop=False)**

数值映射到颜色。参数说明如下：

```
data        - 数据
cm          - 调色板
invalid     - 无效数据的标识
invalid_c   - 无效数据的颜色
drange      - 数据动态范围，None表示使用data的动态范围
alpha       - 透明度，None表示不改变当前透明度
drop        - 舍弃alpha通道
```


## wxgl.text2image

**wxgl.glplot.text2image(text, size, color, family=None, weight='normal')**

文本转图像。参数说明如下：

```
text        - 文本字符串
size        - 字号，整型，默认32
color       - 文本颜色，浮点型元组、列表或numpy数组，值域范围[0,1]
family      - 字体，None表示当前默认的字体
weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
```

---
sort: 1
---

# 颜色和颜色映射

## 颜色

WxGL支持以下方式的颜色表示。

* 十六进制表示的颜色字符串，例如：'#F3D6E9'
* 浮点类型的元组、列表或numpy数组表示的RGB颜色，例如：(1.0, 0.8, 0.2)
* 浮点类型的元组、列表或numpy数组表示的RGBA颜色，例如：(1.0, 0.8, 0.2, 1.0)
* 预定义的颜色名，例如：'red'

函数[wxgl.color_list](https://xufive.github.io/wxgl/api/util.html#wxglcolor_list)返回预定义的颜色列表。

函数[wxgl.color_help](https://xufive.github.io/wxgl/api/util.html#wxglcolor_help)返回预定义的颜色中英文对照表。

## 颜色映射

WxGL的颜色映射方案继承自Matplotlib库。

函数[wxgl.cmap_list](https://xufive.github.io/wxgl/api/util.html#wxglcmap_list)返回颜色映射方案列表。

函数[wxgl.cmap_help](https://xufive.github.io/wxgl/api/util.html#wxglcmap_help)返回颜色映射方案分类列表。

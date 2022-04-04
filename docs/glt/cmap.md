---
sort: 2
---

# 颜色映射

将数据值域范围内的不同数值映射为不同的颜色，是数据可视化的常用手段。WxGL的颜色映射表继承自Matplotlib库。

尽管WxGL提供了颜色映射函数[wxgl.cmap](https://xufive.github.io/wxgl/api/util.html#wxglcmap)，但通常情况下用户只需要提供一个颜色映射表名而无需显式地调用该函数——除非用户使用定制的着色器绘制模型。

WxGL提供了7大类共计82种颜色映射表，每种映射表名字之后附加'_r'，可以获得该映射表的反转版本。函数[wxgl.cmap_list](https://xufive.github.io/wxgl/api/util.html#wxglcmap_list)返回颜色映射方案列表，函数[wxgl.cmap_help](https://xufive.github.io/wxgl/api/util.html#wxglcmap_help)返回颜色映射方案分类列表。

* 视觉均匀类: 'viridis', 'plasma', 'inferno', 'magma', 'cividis'
* 单调变化类: 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn' 
* 近似单调类: 'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper' 
* 亮度发散类: 'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic' 
* 颜色循环类: 'twilight', 'twilight_shifted', 'hsv'
* 分段阶梯类: 'Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2', 'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c', 
* 专属定制类: 'flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix' 'brg', 'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar'

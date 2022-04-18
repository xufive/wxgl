---
sort: 12
---

# 幻灯片播放

调用wxgl.glplot.show函数后，WxGL会启动一个内部计时器，记录以毫秒为单位的渲染时长。模型的slider参数接受一个以WxGL内部计时器为参数的函数，该函数返回一个布尔值，决定该模型是否显示。下面的例子，通过slider参数实现模型闪烁效果（别忘记点击“播放”按钮）。

```pyton
import numpy as np
import wxgl.glplot as glt

sf = lambda t : bool((t//500)%2)

glt.cone((0,1,0), (0,-1,0), 0.8, slide=sf)
glt.show()
```

![doc_slide.jpg](https://raw.githubusercontent.com/xufive/wxgl/master/example/res/md/doc_slide.jpg)

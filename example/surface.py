#!/usr/bin/env python3

import numpy as np
import wxgl

r = 1
b = pow((5 + pow(5, 0.5)) / 10, 0.5)
a = b * (pow(5, 0.5) - 1) / 2

# 正二十面体的12个顶点坐标
vs = np.array([
    [-a,0,b], [a,0,b], [-a,0,-b], [a,0,-b], [0,b,a], [0,b,-a],
    [0,-b,a], [0,-b,-a], [b,a,0], [-b,a,0], [b,-a,0], [-b,-a,0]
])

# 构成正二十面体的20个三角形的顶点索引
idx = np.array([
    1,4,0,  4,9,0,  4,5,9,  8,5,4,  1,8,4, 1,10,8, 10,3,8, 8,3,5,  3,2,5, 3,7,2,
    3,10,7, 10,6,7, 6,11,7, 6,0,11, 6,1,0, 10,1,6, 11,0,9, 2,11,9, 5,2,9, 11,2,7
])

# 正二十面体的三角面顶点集
vs = vs[idx] * r

app = wxgl.App()
app.title('正二十面体')
app.surface(vs, color='cyan')
app.show()

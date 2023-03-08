import numpy as np
import wxgl

z, x = np.mgrid[-np.pi:np.pi:51j, -np.pi:np.pi:51j]
y = np.sin(x) + np.cos(z)

app = wxgl.App() # 默认以y轴作为高度轴
app.title('网格曲面')
app.mesh(x, y, z, data=y, fill=False) # 默认的颜色映射方案是viridis，也可以使用cm参数指定其他方案
app.colorbar((y.min(), y.max()), ff=lambda v:'%.2f'%v) # ff用于设置ColorBar刻度标注的格式化函数
app.show()


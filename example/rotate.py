import numpy as np
import wxgl

r = 1 # 地球半径
gv, gu = np.mgrid[np.pi/2:-np.pi/2:91j, 0:2*np.pi:361j] # 纬度和经度网格
xs = r * np.cos(gv)*np.cos(gu)
ys = r * np.cos(gv)*np.sin(gu)
zs = r * np.sin(gv)

light = wxgl.SunLight(direction=(-1,1,0), ambient=(0.1,0.1,0.1)) # 太阳光照向左前方，暗环境光
tf = lambda t : ((0, 0, 1, (0.02*t)%360), ) # 以20°/s的角速度绕y逆时针轴旋转（t是以毫秒为单位的渲染时长）

# 函数tf返回一个由一系列旋转、位移和缩放动作组成的元组
# 旋转用4元组表示，前3个元素是旋转轴，第4个元素是旋转角度，旋转方向遵从右手定则
# 位移用3元组表示，分别表示模型在xyz轴上的位移距离
# 缩放系数用数值表示

app = wxgl.App(haxis='z') # 以z轴为高度轴
app.title('自转的地球')
app.mesh(xs, ys, zs, texture='res/earth.jpg', light=light, transform=tf)
app.show()


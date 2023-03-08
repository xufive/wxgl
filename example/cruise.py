import numpy as np
import wxgl

phi, theta = np.mgrid[0:np.pi:181j, 0:2*np.pi:361j]
r = np.sin(4*phi) ** 3 + np.cos(2*phi) ** 3 + np.sin(6*theta) ** 2 + np.cos(6*theta) ** 4
x = r * np.sin(phi) * np.cos(theta)
y = r * np.cos(phi)
z = r * np.sin(phi) * np.sin(theta)

# wxgl.App.cruise函数用来设置相机的巡航，接受一个巡航函数作为参数
# 巡航函数以时间t（毫秒）为参数，返回一个包含方位角（azim）、高度角（elev）和距离（dist）的字典

app = wxgl.App(haxis='z', bg='#d0d0d0') # 背景设置为浅灰色
app.title('相机绕模型旋转')
app.mesh(x, y, z, data=z, cm='viridis', ccw=False, light=wxgl.SunLight(ambient=(0.5,0.5,0.5)))
app.cruise(lambda t:{'azim':(0.03*t)%360}) # 相机绕高度轴以30˚/s的速度旋转
app.show()


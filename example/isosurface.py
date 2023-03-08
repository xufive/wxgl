import numpy as np
from PIL import Image
import wxgl

layers = list()
for i in range(109): # 读取109张头部CT断层扫描片，只保留透明通道
    im = np.array(Image.open('res/headCT/head%d.png'%i))
    layers.append(np.fliplr(im[...,3]))
data = np.stack(layers, axis=0)

app = wxgl.App(haxis='z')
app.isosurface(data, data.max()/8, color='#CCC6B0', xr=(-0.65,0.65), yr=(-1,1), zr=(-1,1))
app.title('基于头部CT的三维重建演示')
app.grid() # 显示网格
app.cruise(lambda t : {'azim':(0.02*t)%360}) # 相机以20°/s的角速度逆时针环绕模型
app.show()


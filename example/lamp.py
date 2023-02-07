#!/usr/bin/env python3

import numpy as np
from PIL import Image
import wxgl

image_file = 'res/bull.png'                     # 制作走马灯的图片
w_im, h_im = Image.open(image_file).size        # 获取图片宽度和高度
r, h = 1, 2*np.pi*h_im/w_im                     # 计算圆柱形花灯的直径和高度
tf = lambda t : ((0, 1, 0, (0.02*t)%360), )     # 走马灯旋转函数，以20°/s的角速度绕y逆时针轴旋转
light = wxgl.BaseLight()

theta = np.linspace(0, 2*np.pi, 18, endpoint=False)
x = r*np.cos(theta)
z = r*np.sin(theta)
x[2::3] = x[1::3]
x[1::3] = 0
z[2::3] = z[1::3]
z[1::3] = 0
y = np.ones(18) * h/2 * 0.9
vs = np.stack((x,y,z), axis=1)

for i in range(5):
    app = wxgl.App(elev=30) # 设置高度角30°
    app.title('元宵节的走马灯')
    app.cylinder((0,h/2,0), (0,-h/2,0), r, texture=image_file, transform=tf, light=light)
    app.isosphere((0,0,0), 0.3, color='#FFFFFF', iterate=1, transform=tf)
    app.surface(vs, color='#C03000', method='isolate', alpha=0.8, transform=tf)
    app.line([[0,0,0], [0,0.8*h,0]], color='#A0A000', width=3.0)
    #app.show()
    app.savefig('/home/xufive/MyCode/GitHub/wxgl/capture/ok_%d.png'%i)



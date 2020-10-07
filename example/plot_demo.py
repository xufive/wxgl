# -*- coding: utf-8 -*-

from PIL import Image
import numpy as np
import wxgl.wxplot as plt

# ------------------------------------------------------------
plt.subplot(121)
plt.cube((0,0,0), 1, 'cyan', mode='FCBC')  
plt.subplot(122)  
plt.sphere((0,0,0), 1, 'green', mode='FCBC')                           
plt.show()

# ------------------------------------------------------------
x, y = np.mgrid[-2:2:50j,-2:2:50j]
z = 2*x*np.exp(-x**2-y**2)
plt.mesh(x, y, z, mode='FLBL')
plt.colorbar((z.min(), z.max()), 'hsv', loc='right', label_size=32)
plt.show()

# ------------------------------------------------------------
x, y = np.mgrid[-2:2:50j,-2:2:50j]
z1 = np.zeros_like(x)
z2 = 2*x*np.exp(-x**2-y**2)
ax1 = plt.subplot(121)
ax1.mesh(x, y, z1, mode='FLBL')
ax2 = plt.subplot(122)
ax2.mesh(x, y, z2, mode='FLBC')
plt.show()

# ------------------------------------------------------------
theta = np.linspace(np.pi/12, 11*np.pi/12, 21)
y = np.cos(theta) * 10
z = np.sin(theta) * 10
x = np.array([i%2-0.5 for i in range(21)])
vs = np.stack((x,y,z), axis=1)
vs = np.vstack((np.array([0,0,0]), vs))
cs = plt.cmap(vs[:,0], 'wind')
plt.surface(vs, color=cs, method='F', mode='FLBC')
plt.show(rotation='h+')

# ------------------------------------------------------------
gf = r'res/girl.jpg'
vs = np.array([
    [1,-1,1], [1,-1,-1], [1,1,-1], [1,1,1],
    [-1,1,1], [-1,1,-1], [-1,-1,-1], [-1,-1,1], 
    [-1,-1,1], [-1,-1,-1], [1,-1,-1], [1,-1,1], 
    [1,1,1], [1,1,-1], [-1,1,-1], [-1,1,1]
])
plt.surface(vs, texture=gf, alpha=False)
plt.show(rotation='h+')

# ------------------------------------------------------------
lats, lons = np.mgrid[-np.pi/2:np.pi/2:500j, 0:2*np.pi:1000j]
xs = np.cos(lats)*np.cos(lons)
ys = np.cos(lats)*np.sin(lons)
zs = np.sin(lats)
im = Image.open('res/earth.png')
cs = np.array(im)/255
plt.mesh(xs, ys, zs, color=cs[::-1])
plt.show(rotation='h-')

# ------------------------------------------------------------
data = np.load('res/landforms.npz')
lon = data['lon']
lat = data['lat']
height = data['height']
landforms = data['landforms']

lons, lats = np.meshgrid(lon, lat)
plt.mesh(lons, lats, height/50000, color=landforms/255)

x = 116.65 + np.random.random(500) * (117.65-116.65)
y = 36.25 + np.random.random(500) * (37.00-36.25)
z = 4500 + np.random.random(500) * 500
vs = np.stack((x,y,z/10000), axis=1)
u = np.sin(3*x)
v = np.cos(4*y)
w = -10 - np.random.random(500)
plt.flow(vs, u/100, v/100, w/100, length=4, frames=30, interval=50, color=(0.8,0.8,0.8), actor='point', size=3)
plt.ticks(zlabel_format=lambda z:'%0.1fkm'%(z*10))
plt.show()

# ------------------------------------------------------------
theta = np.linspace(0, 2*np.pi, 360)
_x = np.cos(theta)
_y = np.sin(theta)
data = np.random.random((60,100,100))
for i in range(60):
	x = _x*i/2 + 50
	x = x.astype(np.int)
	y = _y*i/2 + 50 
	y = y.astype(np.int)
	data[i][(x,y)] = 10

plt.capsule(data, 10, '#C020C0', r_x=(0,100), r_y=(0,100), r_z=(0,60), mode='FCBC')
plt.ticks()
plt.show()




































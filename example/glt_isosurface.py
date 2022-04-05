import numpy as np
from PIL import Image
import wxgl
import wxgl.glplot as glt

glt.title('基于头部CT的三维重建演示')
#glt.cruise(lambda duration : {'azim':(0.02*duration)%360})
data = np.stack([np.flipud(np.fliplr(np.array(Image.open('res/headCT/head%d.png'%i)))) for i in range(109)], axis=0)
data = np.rollaxis(data, 2, 1)[...,3]
glt.isosurface(data, data.max()/8, color='#CCC6B0', x=(-0.65,0.65), y=(-1, 1), z=(-1, 1), light=wxgl.SkyLight())
glt.grid()

glt.show()

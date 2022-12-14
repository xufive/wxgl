import numpy as np
import wxgl

dphi, dtheta = np.pi/180.0, np.pi/180.0
phi, theta = np.mgrid[0:np.pi+dphi*1.5:dphi, 0:2*np.pi+dtheta*1.5:dtheta]
m0, m1, m2, m3, m4, m5, m6, m7 = 4, 3, 2, 3, 6, 2, 6, 4
r = np.sin(m0*phi)**m1 + np.cos(m2*phi)**m3 + np.sin(m4*theta)**m5 + np.cos(m6*theta)**m7
x = r*np.sin(phi)*np.cos(theta)
y = r*np.cos(phi)
z = r*np.sin(phi)*np.sin(theta)

app = wxgl.App(haxis='z', bg='#d0d0d0')
app.mesh(x, y, z, data=z, cm='viridis', ccw=False, light=wxgl.SunLight(ambient=(0.5,0.5,0.5)))
app.cruise(lambda t:{'azim':(0.03*t)%360})
app.show()


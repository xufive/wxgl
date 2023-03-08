import numpy as np
import wxgl

vs = np.random.random((30, 3)) * 2 - 1
size = np.random.random(30) * 30 + 20

app = wxgl.App()
app.title('雪花粒子')
app.scatter(vs, size=size, texture='res/snow.png')
app.show()


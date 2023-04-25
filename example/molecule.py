import wxgl

c1, c2, c3, c4, c5 = '#d8d8d8', '#00d0d0', '#6060f0', '#903030', '#90C090'
light = wxgl.SunLight(direction=(0.5,-0.5,-1.0), diffuse=0.7, specular=0.98, shiny=100, pellucid=0.9)

app = wxgl.App(bg='#f0f0f0', azim=-30, elev=20, fovy=40)

app.sphere((-2,0,0), 0.35, color=c1, light=light)
app.sphere((0,0,0), 0.35, color=c1, light=light)
app.sphere((2,0,0), 0.35, color=c1, light=light)
app.sphere((-1,-1,0), 0.35, color=c1, light=light)
app.sphere((1,-1,0), 0.35, color=c1, light=light)

app.cylinder((-2,0,0), (-1,-1,0), 0.17, color=c2, light=light)
app.cylinder((0,0,0), (-1,-1,0), 0.17, color=c2, light=light)
app.cylinder((0,0,0), (1,-1,0), 0.17, color=c2, light=light)
app.cylinder((2,0,0), (1,-1,0), 0.17, color=c2, light=light)

app.sphere((-2,1.2,-0.6), 0.35, color=c3, light=light)
app.sphere((-3,-0.6,0.6), 0.35, color=c3, light=light)
app.sphere((2.6,0.5,1), 0.35, color=c3, light=light)
app.sphere((2.6,0.5,-1), 0.35, color=c3, light=light)
app.sphere((1,-1.5,1), 0.35, color=c5, light=light)

app.cylinder((-2,0,0), (-2,1.2,-0.6), 0.17, color=c4, light=light)
app.cylinder((-2,0,0), (-3,-0.6,0.6), 0.17, color=c2, light=light)
app.cylinder((2,0,0), (2.6,0.5,1), 0.17, color=c4, light=light)
app.cylinder((2,0,0), (2.6,0.5,-1), 0.17, color=c2, light=light)
app.cylinder((1,-1,0), (1,-1.5,1), 0.17, color=c2, light=light)

app.sphere((0,0.7,-0.8), 0.15, color=c2, light=light)
app.sphere((0,0.7,0.8), 0.15, color=c2, light=light)
app.sphere((-1,-1.7,-0.8), 0.15, color=c2, light=light)
app.sphere((-1,-1.7,0.8), 0.15, color=c2, light=light)

app.cylinder((0,0,0), (0,0.7,-0.8), 0.08, color=c2, light=light)
app.cylinder((0,0,0), (0,0.7,0.8), 0.08, color=c2, light=light)
app.cylinder((-1,-1,0), (-1,-1.7,-0.8), 0.08, color=c2, light=light)
app.cylinder((-1,-1,0), (-1,-1.7,0.8), 0.08, color=c2, light=light)

app.show()

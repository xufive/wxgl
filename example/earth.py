import wxgl

def tf(t):
    """模型几何变换函数，t是以毫秒为单位的渲染时长
    
    返回模型旋转、平移、缩放的任意组合序列，该序列元素：
    1. 4元组表示旋转，前3个元素表示旋转轴，第4个元素表示旋转角度
    2. 3元组表示模型在xyz轴上的平移
    3. 数值表示缩放系数
    """
    
    return ((0, 1, 0, (0.02*t)%360), ) # 以20°/s的角速度逆时针绕y轴旋转

light = wxgl.SunLight(direction=(-1,0,-1), ambient=(0.1,0.1,0.1)) # 太阳光照向左前方

app = wxgl.App()
app.title('自转的地球')
app.uvsphere((0,0,0), 1, texture='res/earth.jpg', light=light, transform=tf)
app.show()


# -*- coding: utf-8 -*-
#
# MIT License
# 
# Copyright (c) 2021 Tianyuan Langzi
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


"""
WxGL: 基于pyopengl的三维数据可视化库

WxGL以wx为显示后端，提供matplotlib风格的交互绘图模式
同时，也可以和wxpython无缝结合，在wx的窗体上绘制三维模型
"""


import numpy as np
from . import figure as wff


fig = wff.WxGLFigure()
create_figure = wff.WxGLFigure

show = fig.show
savefig = fig.savefig
capture = fig.capture

cmap = fig.cm.cmap

def figure(**kwds):
    """初始化画布
    
    kwds        - 关键字参数
                    size        - 画布分辨率， 默认1280x960
                    style2d     - 2D模式下的默认风格，默认
                    style3d     - 3D模式下的默认风格
                    dist        - 眼睛与ECS原点的距离
                    view        - 视景体
                    elevation   - 仰角
                    azimuth     - 方位角
    """
    
    global fig
    fig = wff.WxGLFigure(**kwds)

def subplot(pos=111):
    """添加子图
    
    pos         - 子图在场景中的位置和大小
                    三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                    四元组      - 以画布左下角为原点，宽度和高度都是1。四元组分别表示子图左下角在画布上的水平、垂直位置和宽度、高度
    """
    
    ax = fig.add_axes(pos)

def current_axes(func):
    """装饰器函数，检查是否存在当前子图，若无则创建"""
    
    def wrapper(*args, **kwds):
        fig._create_frame()
        if not fig.curr_ax:
            fig.add_axes('111')
        
        func(*args, **kwds)
    
    return wrapper

@current_axes
def axis(**kwds):
    fig.curr_ax.xlabel(**kwds)

@current_axes
def xlabel(xlabel):
    fig.curr_ax.xlabel(xlabel)

@current_axes
def ylabel(ylabel):
    fig.curr_ax.ylabel(ylabel)

@current_axes
def zlabel(zlabel):
    fig.curr_ax.zlabel(zlabel)

@current_axes
def xrotate():
    fig.curr_ax.xrotate()

@current_axes
def xformat(xf):
    fig.curr_ax.xformat(xf)

@current_axes
def yformat(yf):
    fig.curr_ax.yformat(yf)

@current_axes
def zformat(zf):
    fig.curr_ax.zformat(zf)

@current_axes
def xdensity(xd):
    fig.curr_ax.xdensity(xd)

@current_axes
def ydensity(yd):
    fig.curr_ax.ydensity(yd)

@current_axes
def zdensity(zd):
    fig.curr_ax.zdensity(zd)

@current_axes
def title(*args, **kwds):
    fig.curr_ax.title(*args, **kwds)

@current_axes
def colorbar(*args, **kwds):
    fig.curr_ax.colorbar(*args, **kwds)

@current_axes
def text(*args, **kwds):
    fig.curr_ax.text(*args, **kwds)

@current_axes
def plot(*args, **kwds):
    fig.curr_ax.plot(*args, **kwds)

@current_axes
def scatter(*args, **kwds):
    fig.curr_ax.scatter(*args, **kwds)

@current_axes
def hot(*args, **kwds):
    fig.curr_ax.hot(*args, **kwds)

@current_axes
def contour(*args, **kwds):
    fig.curr_ax.contour(*args, **kwds)

@current_axes
def mesh(*args, **kwds):
    fig.curr_ax.mesh(*args, **kwds)

@current_axes
def surface(*args, **kwds):
    fig.curr_ax.surface(*args, **kwds)

@current_axes
def cube(*args, **kwds):
    fig.curr_ax.cube(*args, **kwds)

@current_axes
def sphere(*args, **kwds):
    fig.curr_ax.sphere(*args, **kwds)

@current_axes
def cone(*args, **kwds):
    fig.curr_ax.cone(*args, **kwds)

@current_axes
def cylinder(*args, **kwds):
    fig.curr_ax.cylinder(*args, **kwds)

@current_axes
def colors():
    """绘制可用的颜色及其对应的中英文名称"""
    
    vs = np.array([[0, 1],[0, -13],[31, -13],[31, 1]])
    fig.curr_ax.surface(vs, color='#F0F0F0', method='Q')
    
    colors = fig.cm.color_help()
    for i in range(len(colors)):
        row, col = i//6, i%6
        x, y = 2.2+col*5, -row*0.5
        cen, ccn = colors[i]
        c = fig.cm.color2c(cen)
        
        vs = np.array([[x-0.1, y+0.1],[x-0.1, y-0.1],[x+0.1, y-0.1],[x+0.1, y+0.1]])
        fig.curr_ax.surface(vs, color=c, method='Q')
        
        vs = np.array([[x-0.1, y+0.1],[x-0.1, y-0.1],[x+0.1, y-0.1],[x+0.1, y+0.1],[x-0.1, y+0.1]])
        fig.curr_ax.plot(vs[:,0], vs[:,1], color='black', width=0.5)
        
        fig.curr_ax.text(ccn, size=28, pos=(x-0.15,y), align='right-middle')
        fig.curr_ax.text('(%s)'%cen, size=28, pos=(x+0.15,y), align='left-middle')
    
    fig.curr_ax.axis(visible=False)
    show()

@current_axes
def cmaps():
    """绘制可用的颜色映射表"""
    
    vs = np.array([[0, 1],[0, -13],[31, -13],[31, 1]])
    fig.curr_ax.surface(vs, color='#F0F0F0', method='Q')
    
    cms = fig.cm.cmap_help()
    for i in range(len(colors)):
        row, col = i//6, i%6
        x, y = 2.2+col*5, -row*0.5
        cen, ccn = colors[i]
        c = fig.cm.color2c(cen)
        
        vs = np.array([[x-0.1, y+0.1],[x-0.1, y-0.1],[x+0.1, y-0.1],[x+0.1, y+0.1]])
        fig.curr_ax.surface(vs, color=c, method='Q')
        
        vs = np.array([[x-0.1, y+0.1],[x-0.1, y-0.1],[x+0.1, y-0.1],[x+0.1, y+0.1],[x-0.1, y+0.1]])
        fig.curr_ax.plot(vs[:,0], vs[:,1], color='black', width=0.5)
        
        fig.curr_ax.text(ccn, size=32, pos=(x-0.15,y), align='right-middle')
        fig.curr_ax.text('(%s)'%cen, size=32, pos=(x+0.15,y), align='left-middle')
    
    fig.curr_ax.axis(visible=False)
    show()



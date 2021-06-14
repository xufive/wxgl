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


from . import figure as wff


fig = wff.WxGLFigure()


def figure(size=None, dist=None, view=None, elevation=None, azimuth=None):
    """设置画布"""
    
    if size:
        fig.size = size
    if dist:
        fig.kwds.update({'dist':dist})
    if view:
        fig.kwds.update({'view':view})
    if elevation:
        fig.kwds.update({'elevation':elevation})
    if azimuth:
        fig.kwds.update({'azimuth':azimuth})
    
    if fig.ff:
        fig.ff.SetSize(fig.size)
        fig.ff.Center()
        
        fig.ff.scene.set_posture(
            dist        = fig.kwds.get('dist', None), 
            azimuth     = fig.kwds.get('azimuth', None), 
            elevation   = fig.kwds.get('elevation', None), 
            save        = True
        )

def subplot(*args, **kwds):
    """添加子图"""
    
    fig.add_axes(*args, **kwds)

def show(*args, **kwds):
    """显示画布"""
    
    fig.show(*args, **kwds)

def savefig(*args, **kwds):
    """保存画布为文件"""
    
    fig.savefig(*args, **kwds)

def plot(*args, **kwds):
    """绘制点和线"""
    
    fig._create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    
    fig.curr_ax.plot(*args, **kwds)

colors = fig.cm.color_list
cmap_list = fig.cm.cmap_list
cmap = fig.cm.cmap

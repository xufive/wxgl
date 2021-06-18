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


def figure(size=(960,720), **kwds):
    """设置画布
        
        size        - 画布分辨率， 默认960x720
        kwds        - 关键字参数
                        dist        - 眼睛与ECS原点的距离，默认5
                        view        - 视景体， 默认[-1, 1, -1, 1, 2.6, 1000]
                        elevation   - 仰角，默认0°
                        azimuth     - 方位角，默认0°
    """
    for key in kwds:
            if key not in ['dist', 'view', 'elevation', 'azimuth']:
                raise KeyError('不支持的关键字参数：%s'%key)
    
    fig.size = size
    fig.kwds = kwds
    
    if fig.ff:
        fig.ff.SetSize(fig.size)
        fig.ff.Center()
        
        fig.ff.scene.set_posture(
            dist        = fig.kwds.get('dist', None), 
            azimuth     = fig.kwds.get('azimuth', None), 
            elevation   = fig.kwds.get('elevation', None), 
            save        = True
        )

def subplot(pos, padding=(20,20,20,20)):
    """添加子图
    
    pos         - 子图在场景中的位置和大小
                    三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                    四元组      - 以画布左下角为原点，宽度和高度都是1。四元组分别表示子图左下角在画布上的水平、垂直位置和宽度、高度
    padding     - 四元组，上、右、下、左四个方向距离边缘的留白像素
    """
    
    fig.add_axes(pos, padding=padding)

def show(rotate=None):
    """显示画布。rotate为每个定时周期内水平旋转的角度，浮点数，None表示无旋转"""
    
    fig.show(rotate=rotate)

def savefig(fn):
    """保存画布为文件。fn为文件名，支持.png和.jpg格式"""
    
    fig.savefig(fn)

def xlabel(text):
    """设置x轴名称，text为文本字符串"""
    
    fig._create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    
    fig.curr_ax.set_xlabel(text)

def ylabel(text):
    """设置y轴名称，text为文本字符串"""
    
    fig._create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    
    fig.curr_ax.set_ylabel(text)

def zlabel(text):
    """设置z轴名称，text为文本字符串"""
    
    fig._create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    
    fig.curr_ax.set_zlabel(text)

def title(text, size=64, color=None, **kwds):
    """绘制标题
    
    text        - 文本字符串
    size        - 文字大小，整形，默认64
    color       - 文本颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用默认颜色
    kwds        - 关键字参数
                    family      - （系统支持的）字体，None表示当前默认的字体
                    weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
    """
    
    fig._create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    
    fig.curr_ax.title(text, size=size, color=color, **kwds)

def colorbar(drange, cmap, **kwds):
    """绘制colorbar
    
    drange      - 值域范围，tuple类型
    cmap        - 调色板名称
    kwds        - 关键字参数
                    subject         - 标题
                    subject_size    - 标题字号，默认44
                    tick_size       - 刻度字号，默认40
                    tick_format     - 刻度标注格式化函数，默认str
                    density         - 刻度密度，最少和最多刻度线组成的元组，默认(3,6)
                    endpoint        - 刻度是否包含值域范围的两个端点值
    """
    
    fig._create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    
    fig.curr_ax.colorbar(drange, cmap, **kwds)

def text(text, size=40, color=None, pos=(0,0,0), **kwds):
    """绘制文本
    
    text        - 文本字符串
    size        - 文字大小，整形，默认40
    color       - 文本颜色，支持十六进制，以及浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用默认颜色
    pos         - 文本位置，list或numpy.ndarray类型
    kwds        - 关键字参数
                    family      - （系统支持的）字体
                    weight      - light/bold/normal分别表示字体的轻、重、正常（默认）
    """
    
    fig._create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    
    fig.curr_ax.text(text, size=size, color=color, pos=pos, **kwds)

def plot(x, y, z=None, color=None, cm=None, size=0.0, width=1.0, style='solid', method='SINGLE', **kwds):
    """绘制点和线
    
     x/y/z       - 顶点的x/y/z坐标集，元组、列表或一维数组，长度相等。若zs为None，则自动补为全0数组
    color       - 颜色，或每个顶点对应的颜色，或每个顶点对应的数据（此种情况下cm参数不能为None）
    cm          - 颜色映射表，仅当参数color为每个顶点对应的数据时有效
    size        - 顶点大小。若为0或None，则表示不绘制点，只绘制线
    width       - 线宽，0.0~10.0之间的浮点数。若为0或None，则表示不绘制线，只绘制点
    style       - 线型
                    'solid'     - 实线
                    'dashed'    - 虚线
                    'dotted'    - 点线
                    'dash-dot'  - 虚点线
    method      - 绘制方法
                    'MULTI'     - 线段
                    'SINGLE'    - 连续线段
                    'LOOP'      - 闭合线段
    kwds        - 关键字参数
                    name        - 模型名
                    visible     - 是否可见，默认可见
                    slide       - None或者display函数，以场景的自增计数器为输入，返回布尔值
                    inside      - 是否自动缩放至[-1,1]范围内，默认自动缩放
                    regulate    - 顶点集几何变换，None或者元组、列表，其元素为位移向量三元组，或由旋转角度、旋转向量组成的二元组
                    rotate      - None或者旋转函数，以场景的自增计数器为输入，返回旋转角度和旋转向量组成的元组
                    translate   - None或者位移函数，以场景的自增计数器为输入，返回位移元组
                    order       - 几何变换的顺序
                        None        - 无变换（默认）
                        'R'         - 仅旋转变换
                        'T'         - 仅位移变换
                        'RT'        - 先旋转后位移
                        'TR'        - 先位移后旋转
    """
    
    fig._create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    
    fig.curr_ax.plot(x, y, z=z, color=color, cm=cm, size=size, width=width, style=style, method=method, **kwds)

colors = fig.cm.color_list
cmap_list = fig.cm.cmap_list
cmap = fig.cm.cmap

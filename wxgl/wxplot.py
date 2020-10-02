# -*- coding: utf-8 -*-
#
# Copyright 2019 xufive@gmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 

"""
WxGL是一个基于pyopengl的三维数据展示库

WxGL以wx为显示后端，以加速渲染为第一追求目标
借助于wxpython，WxGL可以很好的融合matplotlib等其他数据展示技术
"""


from . import wxfigure


fig = wxfigure.Figure()

def figure(*args, **kwds):
    global fig
    fig = wxfigure.Figure(*args, **kwds)
    
    return fig

def show():
    fig.show()

def savefig(*args, **kwds):
    fig.savefig(*args, **kwds)

def subplot(*args, **kwds):
    return fig.add_axes(*args, **kwds)

def colorbar(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.colorbar(*args, **kwds)

def title(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.title(*args, **kwds)

def text(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.text(*args, **kwds)

def plot(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.plot(*args, **kwds)

def scatter(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.scatter(*args, **kwds)

def mesh(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.mesh(*args, **kwds)

def surface(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.surface(*args, **kwds)

def pipe(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.pipe(*args, **kwds)

def sphere(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.sphere(*args, **kwds)

def cube(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.cube(*args, **kwds)

def cylinder(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.cylinder(*args, **kwds)

def cone(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.cone(*args, **kwds)

def capsule(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.capsule(*args, **kwds)

def flow(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.flow(*args, **kwds)

def ticks(*args, **kwds):
    fig.create_frame()
    if not fig.curr_ax:
        fig.add_axes('111')
    fig.curr_ax.ticks(*args, **kwds)

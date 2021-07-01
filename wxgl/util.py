# -*- coding: utf-8 -*-

import numpy as np
from matplotlib import pyplot as mplt

def get_contour(data, xs, ys, levels):
    """返回等值线
    
    data        - 数据，类二维数组
    levels      - 分级数量，整数或升序的类一维数组
    """
    
    c = mplt.contour(xs, ys, data, levels=levels)
    contours = list()
    for g in c.collections:
        contours.append([item.vertices for item in g.get_paths()])
    
    
    return c.cvalues, contours

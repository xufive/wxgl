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


import os, json
import numpy as np
import warnings
warnings.filterwarnings('ignore')


class ColorMap(object):
    """颜色映射类"""
    
    def __init__(self, cmfile='colormap.cm'):
        """构造函数"""
        
        assert os.path.isfile(cmfile), u'调色板文件不存在'
        
        with open(cmfile, 'r') as fp:
            self.cms = json.loads(fp.read())
        
    def getColorMaps(self):
        """获取可用colormap的名字"""
        
        return self.cms.keys()
        
    def map(self, data, cm, invalid=np.nan, invalid_c=[0,0,0,0], mode="RGBA", datamax=None, datamin=None):
        """数值颜色映射
        
        data        - 数据
        cm          - colormap的名字
        invalid     - 无效数据的标识
        mode        - 返回结果的格式：RGBA|RGB
        datamax     - 数据最大值，默认为None
        datamin     - 数据最小值，默认为None
        """
        
        assert cm in self.cms, u'使用的调色板不存在'
        
        datashape = list(data.shape)
        data = data.ravel().astype(np.float64)
        if not np.isnan(invalid):
            data[data==invalid] = np.nan
        
        vlist = []
        for t in self.cms[cm]:
            vlist.append(t[0])
        cbmin = min(vlist)
        cbmax = max(vlist)
        
        if datamax is None:
            datamax = np.nanmax(data)
        
        if datamin is None:
            datamin = np.nanmin(data)
            
        if datamin > datamax:
            print ("WARNING! maximum is less than minimum!.")
        
        tempCM = []
        for i in range(len(self.cms[cm])):
            nv = ((datamax-datamin) * (self.cms[cm][i][0]-cbmin)* 1.0) / (cbmax - cbmin)
            nv += datamin
            tempCM.append([nv, self.cms[cm][i][1]])
            
        r = data.copy()
        g = data.copy()
        b = data.copy()
        
        r_left_index = np.where(data<=tempCM[0][0])
        g_left_index = r_left_index
        b_left_index = r_left_index
        r_right_index = np.where(data>=tempCM[-1][0])
        g_right_index = r_right_index
        b_right_index = r_right_index
        
        for i in range(1, len(tempCM)):
            v_max = tempCM[i][0]
            v_min = tempCM[i-1][0]
            index = np.where((data<v_max)&(data>=v_min))

            #red ------
            c_max = tempCM[i][1][0]
            c_min = tempCM[i-1][1][0]
            kr = (c_max - c_min)*1.0 / (v_max - v_min)
            vr = kr*v_min - c_min
            r[index] *= kr
            r[index] -= vr

            #gren ------
            c_max = tempCM[i][1][1]
            c_min = tempCM[i-1][1][1]
            kg = (c_max - c_min)*1.0 / (v_max - v_min)
            vg = kg*v_min - c_min
            g[index] *= kg
            g[index] -= vg

            #blue ------
            c_max = tempCM[i][1][2]
            c_min = tempCM[i-1][1][2]
            kb = (c_max - c_min)*1.0 / (v_max - v_min)
            vb = kb*v_min - c_min
            b[index] *= kb
            b[index] -= vb

        last_index = np.where(data==v_max)
        r[last_index] *= kr
        r[last_index] -= vr
        g[last_index] *= kg
        g[last_index] -= vg
        b[last_index] *= kb
        b[last_index] -= vb
        
        #大于最大值的使用最大值的颜色，小于最小值的数据使用最小值的颜色
        r[r_left_index]  = tempCM[0][1][0]
        g[g_left_index]  = tempCM[0][1][1]
        b[b_left_index]  = tempCM[0][1][2]
        r[r_right_index] = tempCM[-1][1][0]
        g[g_right_index] = tempCM[-1][1][1]
        b[b_right_index] = tempCM[-1][1][2]
        
        if mode == 'RGBA':
            alpha = 255*np.ones(data.shape)
            w = np.where(np.isnan(data)==True)
            r[w] = invalid_c[0] * 255
            g[w] = invalid_c[1] * 255
            b[w] = invalid_c[2] * 255
            alpha[w] = invalid_c[3] * 255
            color = np.dstack([r, g, b, alpha])/255
            datashape.append(4)
        else:
            w = np.where(np.isnan(data)==True)
            r[w] = invalid_c[0] * 255
            g[w] = invalid_c[1] * 255
            b[w] = invalid_c[2] * 255
            
            color = np.dstack([r, g, b])/255
            datashape.append(3)
        
        return color.reshape(tuple(datashape))


if __name__ == "__main__":
    cm = ColorMap()
    #组织数据
    #data = np.arange(201.0, 601.0)
    #data.shape = 400, 1
    #data = data.repeat(20, axis=1)
    #data[(data>250)&(data<300)] = np.nan
    #设置调色板名称
    data = np.ones((4,5,6))
    cmap = 'jet'
    
    #将颜色生成图片测试效果
    #from PIL import Image
    print (data.shape)
    cdata = cm.map(data, cmap, datamax=500, datamin=300)*255
    print (cdata.shape)
    #Image.fromarray(cdata.astype(np.uint8), mode='RGBA').save('test_RGBA.png')
    
    #cdata = cm.map(data, cmap, mode="RGB")*255
    #Image.fromarray(cdata.astype(np.uint8), mode='RGB').save('test_RGB.png')
    
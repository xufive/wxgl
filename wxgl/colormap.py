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
    
    def __init__(self):
        """构造函数"""
        self.cms = getCM()
        
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

def getCM():
    cms = {
        "autumn": [
            [
                0.0,
                [
                    255,
                    0,
                    0
                ]
            ],
            [
                1.0,
                [
                    255,
                    255,
                    0
                ]
            ]
        ],
        "brg": [
            [
                0.0,
                [
                    0,
                    0,
                    255
                ]
            ],
            [
                0.5,
                [
                    255,
                    0,
                    0
                ]
            ],
            [
                1.0,
                [
                    0,
                    255,
                    0
                ]
            ]
        ],
        "CMRmap": [
            [
                0.0,
                [
                    0,
                    0,
                    0
                ]
            ],
            [
                0.13,
                [
                    38,
                    38,
                    127
                ]
            ],
            [
                0.25,
                [
                    76,
                    38,
                    191
                ]
            ],
            [
                0.38,
                [
                    153,
                    51,
                    127
                ]
            ],
            [
                0.5,
                [
                    255,
                    63,
                    38
                ]
            ],
            [
                0.63,
                [
                    229,
                    127,
                    0
                ]
            ],
            [
                0.75,
                [
                    229,
                    191,
                    25
                ]
            ],
            [
                0.88,
                [
                    229,
                    229,
                    127
                ]
            ],
            [
                1.0,
                [
                    255,
                    255,
                    255
                ]
            ]
        ],
        "cool": [
            [
                0.0,
                [
                    0,
                    255,
                    255
                ]
            ],
            [
                1.0,
                [
                    255,
                    0,
                    255
                ]
            ]
        ],
        "cubehelix": [
            [
                0.0,
                [
                    0,
                    0,
                    0
                ]
            ],
            [
                0.1,
                [
                    25,
                    21,
                    48
                ]
            ],
            [
                0.2,
                [
                    21,
                    60,
                    77
                ]
            ],
            [
                0.3,
                [
                    30,
                    101,
                    65
                ]
            ],
            [
                0.4,
                [
                    83,
                    121,
                    46
                ]
            ],
            [
                0.5,
                [
                    160,
                    121,
                    73
                ]
            ],
            [
                0.6,
                [
                    207,
                    126,
                    146
                ]
            ],
            [
                0.7,
                [
                    207,
                    156,
                    217
                ]
            ],
            [
                0.8,
                [
                    193,
                    202,
                    243
                ]
            ],
            [
                0.9,
                [
                    210,
                    237,
                    238
                ]
            ],
            [
                1.0,
                [
                    255,
                    255,
                    255
                ]
            ]
        ],
        "gist_earth": [
            [
                0.0,
                [
                    0,
                    0,
                    0
                ]
            ],
            [
                0.0,
                [
                    0,
                    0,
                    42
                ]
            ],
            [
                0.01,
                [
                    1,
                    0,
                    56
                ]
            ],
            [
                0.03,
                [
                    4,
                    0,
                    110
                ]
            ],
            [
                0.03,
                [
                    5,
                    2,
                    115
                ]
            ],
            [
                0.11,
                [
                    18,
                    48,
                    119
                ]
            ],
            [
                0.16,
                [
                    27,
                    77,
                    122
                ]
            ],
            [
                0.21,
                [
                    35,
                    97,
                    124
                ]
            ],
            [
                0.28,
                [
                    47,
                    128,
                    127
                ]
            ],
            [
                0.46,
                [
                    69,
                    153,
                    72
                ]
            ],
            [
                0.47,
                [
                    73,
                    155,
                    70
                ]
            ],
            [
                0.52,
                [
                    104,
                    163,
                    78
                ]
            ],
            [
                0.55,
                [
                    118,
                    165,
                    81
                ]
            ],
            [
                0.55,
                [
                    120,
                    166,
                    82
                ]
            ],
            [
                0.7,
                [
                    182,
                    182,
                    94
                ]
            ],
            [
                0.78,
                [
                    192,
                    163,
                    101
                ]
            ],
            [
                0.79,
                [
                    192,
                    162,
                    103
                ]
            ],
            [
                0.79,
                [
                    193,
                    163,
                    105
                ]
            ],
            [
                0.8,
                [
                    195,
                    164,
                    110
                ]
            ],
            [
                0.81,
                [
                    198,
                    165,
                    115
                ]
            ],
            [
                0.82,
                [
                    200,
                    166,
                    120
                ]
            ],
            [
                0.87,
                [
                    214,
                    178,
                    152
                ]
            ],
            [
                0.87,
                [
                    217,
                    181,
                    157
                ]
            ],
            [
                0.88,
                [
                    219,
                    184,
                    162
                ]
            ],
            [
                0.89,
                [
                    221,
                    186,
                    167
                ]
            ],
            [
                0.89,
                [
                    222,
                    188,
                    169
                ]
            ],
            [
                0.9,
                [
                    223,
                    189,
                    172
                ]
            ],
            [
                0.94,
                [
                    236,
                    211,
                    205
                ]
            ],
            [
                0.96,
                [
                    240,
                    220,
                    217
                ]
            ],
            [
                0.96,
                [
                    242,
                    224,
                    223
                ]
            ],
            [
                1.0,
                [
                    251,
                    248,
                    247
                ]
            ],
            [
                1.0,
                [
                    253,
                    250,
                    250
                ]
            ]
        ],
        "gist_rainbow": [
            [
                0.0,
                [
                    255,
                    0,
                    40
                ]
            ],
            [
                0.03,
                [
                    255,
                    0,
                    0
                ]
            ],
            [
                0.21,
                [
                    255,
                    255,
                    0
                ]
            ],
            [
                0.4,
                [
                    0,
                    255,
                    0
                ]
            ],
            [
                0.59,
                [
                    0,
                    255,
                    255
                ]
            ],
            [
                0.77,
                [
                    0,
                    0,
                    255
                ]
            ],
            [
                0.95,
                [
                    255,
                    0,
                    255
                ]
            ],
            [
                1.0,
                [
                    255,
                    0,
                    191
                ]
            ]
        ],
        "gist_stern": [
            [
                0.0,
                [
                    0,
                    0,
                    0
                ]
            ],
            [
                0.05,
                [
                    255,
                    13,
                    27
                ]
            ],
            [
                0.25,
                [
                    6,
                    63,
                    127
                ]
            ],
            [
                0.5,
                [
                    89,
                    127,
                    255
                ]
            ],
            [
                0.73,
                [
                    167,
                    187,
                    0
                ]
            ],
            [
                1.0,
                [
                    255,
                    255,
                    255
                ]
            ]
        ],
        "gnuplot": [
            [
                0.0,
                [
                    0,
                    0,
                    0
                ]
            ],
            [
                0.1,
                [
                    80,
                    0,
                    149
                ]
            ],
            [
                0.2,
                [
                    114,
                    2,
                    242
                ]
            ],
            [
                0.3,
                [
                    139,
                    6,
                    242
                ]
            ],
            [
                0.4,
                [
                    161,
                    16,
                    149
                ]
            ],
            [
                0.5,
                [
                    180,
                    31,
                    0
                ]
            ],
            [
                0.6,
                [
                    197,
                    55,
                    0
                ]
            ],
            [
                0.7,
                [
                    213,
                    87,
                    0
                ]
            ],
            [
                0.8,
                [
                    228,
                    130,
                    0
                ]
            ],
            [
                0.9,
                [
                    241,
                    185,
                    0
                ]
            ],
            [
                1.0,
                [
                    255,
                    255,
                    0
                ]
            ]
        ],
        "gray": [
            [
                0.0,
                [
                    0,
                    0,
                    0
                ]
            ],
            [
                1.0,
                [
                    255,
                    255,
                    255
                ]
            ]
        ],
        "gray_r": [
            [
                0.0,
                [
                    255,
                    255,
                    255
                ]
            ],
            [
                1.0,
                [
                    0,
                    0,
                    0
                ]
            ]
        ],
        "hsv": [
            [
                0.0,
                [
                    255,
                    0,
                    0
                ]
            ],
            [
                0.16,
                [
                    255,
                    239,
                    0
                ]
            ],
            [
                0.17,
                [
                    247,
                    255,
                    0
                ]
            ],
            [
                0.33,
                [
                    7,
                    255,
                    0
                ]
            ],
            [
                0.35,
                [
                    0,
                    255,
                    15
                ]
            ],
            [
                0.51,
                [
                    0,
                    255,
                    255
                ]
            ],
            [
                0.67,
                [
                    0,
                    15,
                    255
                ]
            ],
            [
                0.68,
                [
                    7,
                    0,
                    255
                ]
            ],
            [
                0.84,
                [
                    247,
                    0,
                    255
                ]
            ],
            [
                0.86,
                [
                    255,
                    0,
                    239
                ]
            ],
            [
                1.0,
                [
                    255,
                    0,
                    23
                ]
            ]
        ],
        "jet": [
            [
                0.0,
                [
                    0,
                    0,
                    127
                ]
            ],
            [
                0.11,
                [
                    0,
                    0,
                    255
                ]
            ],
            [
                0.13,
                [
                    0,
                    0,
                    255
                ]
            ],
            [
                0.34,
                [
                    0,
                    219,
                    255
                ]
            ],
            [
                0.35,
                [
                    0,
                    229,
                    246
                ]
            ],
            [
                0.38,
                [
                    20,
                    255,
                    226
                ]
            ],
            [
                0.64,
                [
                    238,
                    255,
                    8
                ]
            ],
            [
                0.65,
                [
                    246,
                    245,
                    0
                ]
            ],
            [
                0.66,
                [
                    255,
                    236,
                    0
                ]
            ],
            [
                0.89,
                [
                    255,
                    18,
                    0
                ]
            ],
            [
                0.91,
                [
                    231,
                    0,
                    0
                ]
            ],
            [
                1.0,
                [
                    127,
                    0,
                    0
                ]
            ]
        ],
        "ocean": [
            [
                0.0,
                [
                    0,
                    127,
                    0
                ]
            ],
            [
                0.1,
                [
                    0,
                    89,
                    25
                ]
            ],
            [
                0.2,
                [
                    0,
                    50,
                    51
                ]
            ],
            [
                0.3,
                [
                    0,
                    12,
                    76
                ]
            ],
            [
                0.4,
                [
                    0,
                    25,
                    102
                ]
            ],
            [
                0.5,
                [
                    0,
                    63,
                    127
                ]
            ],
            [
                0.6,
                [
                    0,
                    102,
                    153
                ]
            ],
            [
                0.7,
                [
                    25,
                    140,
                    178
                ]
            ],
            [
                0.8,
                [
                    102,
                    178,
                    204
                ]
            ],
            [
                0.9,
                [
                    178,
                    216,
                    229
                ]
            ],
            [
                1.0,
                [
                    255,
                    255,
                    255
                ]
            ]
        ],
        "rainbow": [
            [
                0.0,
                [
                    127,
                    0,
                    255
                ]
            ],
            [
                0.1,
                [
                    76,
                    78,
                    251
                ]
            ],
            [
                0.2,
                [
                    25,
                    149,
                    242
                ]
            ],
            [
                0.3,
                [
                    25,
                    206,
                    227
                ]
            ],
            [
                0.4,
                [
                    76,
                    242,
                    206
                ]
            ],
            [
                0.5,
                [
                    127,
                    255,
                    180
                ]
            ],
            [
                0.6,
                [
                    178,
                    242,
                    149
                ]
            ],
            [
                0.7,
                [
                    229,
                    206,
                    115
                ]
            ],
            [
                0.8,
                [
                    255,
                    149,
                    78
                ]
            ],
            [
                0.9,
                [
                    255,
                    78,
                    39
                ]
            ],
            [
                1.0,
                [
                    255,
                    0,
                    0
                ]
            ]
        ],
        "spring": [
            [
                0.0,
                [
                    255,
                    0,
                    255
                ]
            ],
            [
                1.0,
                [
                    255,
                    255,
                    0
                ]
            ]
        ],
        "summer": [
            [
                0.0,
                [
                    0,
                    127,
                    102
                ]
            ],
            [
                1.0,
                [
                    255,
                    255,
                    102
                ]
            ]
        ],
        "summer": [
            [
                0.0,
                [
                    0,
                    127,
                    102
                ]
            ],
            [
                1.0,
                [
                    255,
                    255,
                    102
                ]
            ]
        ],
        "terrain": [
            [
                0.0,
                [
                    51,
                    51,
                    153
                ]
            ],
            [
                0.15,
                [
                    0,
                    153,
                    255
                ]
            ],
            [
                0.25,
                [
                    0,
                    204,
                    102
                ]
            ],
            [
                0.5,
                [
                    255,
                    255,
                    153
                ]
            ],
            [
                0.75,
                [
                    127,
                    91,
                    84
                ]
            ],
            [
                1.0,
                [
                    255,
                    255,
                    255
                ]
            ]
        ],
        "winter": [
            [
                0.0,
                [
                    0,
                    0,
                    255
                ]
            ],
            [
                1.0,
                [
                    0,
                    255,
                    127
                ]
            ]
        ],
        "Wistia": [
            [
                0.0,
                [
                    228,
                    255,
                    122
                ]
            ],
            [
                0.25,
                [
                    255,
                    232,
                    26
                ]
            ],
            [
                0.5,
                [
                    255,
                    189,
                    0
                ]
            ],
            [
                0.75,
                [
                    255,
                    160,
                    0
                ]
            ],
            [
                1.0,
                [
                    252,
                    127,
                    0
                ]
            ]
        ]
    }
    
    return cms
    
if __name__ == "__main__":
    pass
    
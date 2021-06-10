# -*- coding: utf-8 -*-

import re
import numpy as np
import matplotlib
from matplotlib import cm as mcm


class ColorManager:
    """颜色管理类"""
    
    def __init__(self):
        """构造函数"""
        
        self._colors = matplotlib.colors.cnames
        self._cmaps = [
            'Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap', 'CMRmap_r', 
            'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys', 'Greys_r', 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 
            'PRGn', 'PRGn_r', 'Paired', 'Paired_r', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBu_r', 
            'PuBuGn', 'PuBuGn_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy', 'RdGy_r', 
            'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r', 'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 
            'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r', 'YlGn', 'YlGn_r', 'YlGnBu', 'YlGnBu_r', 'YlOrBr', 'YlOrBr_r', 
            'YlOrRd', 'YlOrRd_r', 'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'binary', 'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 
            'bwr', 'bwr_r', 'cividis', 'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'cubehelix', 'cubehelix_r', 
            'flag', 'flag_r', 'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r', 'gist_ncar', 'gist_ncar_r', 
            'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gnuplot', 'gnuplot_r', 
            'gnuplot2', 'gnuplot2_r', 'gray', 'gray_r', 'hot', 'hot_r', 'hsv', 'hsv_r', 'inferno', 'inferno_r', 'jet', 'jet_r', 
            'magma', 'magma_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r', 
            'prism', 'prism_r', 'rainbow', 'rainbow_r', 'seismic', 'seismic_r', 'spring', 'spring_r', 'summer', 'summer_r', 'tab10', 'tab10_r', 
            'tab20', 'tab20_r', 'tab20b', 'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', 'terrain_r', 'twilight', 'twilight_r', 
            'twilight_shifted', 'twilight_shifted_r', 'viridis', 'viridis_r', 'winter', 'winter_r'
        ]
    
    @property    
    def color_list(self):
        """预设的颜色列表"""
        
        return list(self._colors.keys())
    
    @property
    def cmap_list(self):
        """预设的调色板列表"""
        
        return self._cmaps
    
    def cmap_help(self):
        """返回调色板分类列表"""
        
        return {
            '视觉均匀类': ['viridis', 'plasma', 'inferno', 'magma', 'cividis'], 
            '单调变化类': ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 
                           'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn'], 
            '近似单调类': ['binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer', 'autumn', 'winter', 
                           'cool', 'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper'], 
            '亮度发散类': ['PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic'], 
            '颜色循环类': ['twilight', 'twilight_shifted', 'hsv'],
            '分段阶梯类': ['Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2', 'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c'], 
            '专属定制类': ['flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 
                           'brg', 'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar']
        }
    
    def hex2color(self, str_hex):
        """以#为前缀的十六进制颜色转numpy数组颜色"""
        
        return np.array((int(str_hex[1:3],base=16)/255, int(str_hex[3:5],base=16)/255, int(str_hex[5:],base=16)/255), dtype=np.float64)

    def str2color(self, color):
        """字符串表示的颜色转numpy数组颜色"""
        
        if color in self._colors:
            return self.hex2color(self._colors[color])
        elif re.compile(r'#[\da-fA-F]{6}').match(color):
            return self.hex2color(color)
        else:
            raise ValueError('未定义的或不符合规则的颜色：%s'%color)
    
    def color2c(self, color):
        """字符串、元组、列表等类型的颜色转numpy数组颜色"""
        
        if isinstance(color, str):
            color = self.str2color(color)
        elif isinstance(color, (list, tuple)):
            color = np.array(color, dtype=np.float64)
        
        if not isinstance(color, np.ndarray) or color.ndim > 2 or color.shape[-1] not in (3,4):
             raise ValueError('未定义的或不符合规则的颜色')
        
        return color
    
    def cmap(self, data, cm, invalid=np.nan, invalid_c=[0,0,0,0], dmin=None, dmax=None, alpha=None):
        """数值映射到颜色
        
        data        - 数据
        cm          - 调色板
        invalid     - 无效数据的标识
        invalid_c   - 无效数据的颜色
        dmin        - 数据最小值，默认为None
        dmax        - 数据最大值，默认为None
        alpha       - 透明度，None表示返回RGB格式
        """
        
        assert cm in self._cmaps, '未定义的调色板%s'%cm
        assert isinstance(invalid_c, (list, tuple, np.ndarray)), '期望参数invalid_c是元组、列表或numpy数组'
        
        if not isinstance(invalid_c, np.ndarray):
            invalid_c = np.array(invalid_c, dtype=np.float64)
        
        if not np.isnan(invalid):
            data[data==invalid] = np.nan
        invalid_pos = np.where(data==np.nan) # 记录无效数据位置
        
        if dmin is None:
            dmin = np.nanmin(data)
        if dmax is None:
            dmax = np.nanmax(data)
        if dmin > dmax:
            raise ValueError('数据最小值%f大于数据最大值%f'%(dmax, dmin))
        
        
        data[data<dmin] = dmin
        data[data>dmax] = dmax
        
        cmo = mcm.get_cmap(cm)
        cmap, k = list(), 256/cmo.N
        for i in range(cmo.N):
            c = cmo(i)
            for j in range(int(i*k), int((i+1)*k)):
                cmap.append(c)
        cmap = np.array(cmap)
        
        data = np.uint8(255*(data-dmin)/(dmax-dmin))
        color = cmap[data]
        color[invalid_pos] = invalid_c
        
        if alpha is None:
            color = color.reshape(-1,4)
            color = color[:,:-1]
            color = color.reshape(*data.shape, 3)
        elif alpha < 1:
            color = color.reshape(-1,4)
            color[:,3] = alpha
            color = color.reshape(*data.shape, 4)
        
        return color

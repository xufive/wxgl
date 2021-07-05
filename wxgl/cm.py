# -*- coding: utf-8 -*-

import re
import numpy as np
import matplotlib
from matplotlib import cm as mcm


class ColorManager:
    """颜色管理类"""
    
    def __init__(self):
        """构造函数"""
        
        self.default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
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
    
    def color_help(self):
        """返回颜色中英文对照表"""
        
        return [
            ('aliceblue', '爱丽丝蓝'), ('antiquewhite', '古董白'), ('aqua', '青'), ('aquamarine', '碧绿'), ('azure', '青白'), 
            ('beige', '米'), ('bisque', '橘黄'), ('black', '黑'), ('blanchedalmond', '杏仁白'), ('blue', '蓝'), ('blueviolet', '蓝紫'), 
            ('brown', '褐'), ('burlywood', '硬木褐'), ('cadetblue', '军服蓝'), ('chartreuse', '查特酒绿'), ('chocolate', '巧克力'), 
            ('coral', '珊瑚红'), ('cornflowerblue', '矢车菊蓝'), ('cornsilk', '玉米穗黄'), ('crimson', '绯红'), ('cyan', '青'), 
            ('darkblue', '深蓝'), ('darkcyan', '深青'), ('darkgoldenrod', '深金菊黄'), ('darkgray', '暗灰'), ('darkgreen', '深绿'), 
            ('darkgrey', '暗灰'), ('darkkhaki', '深卡其'), ('darkmagenta', '深品红'), ('darkolivegreen', '深橄榄绿'), ('darkorange', '深橙'), 
            ('darkorchid', '深洋兰紫'), ('darkred', '深红'), ('darksalmon', '深鲑红'), ('darkseagreen', '深海藻绿'), ('darkslateblue', '深岩蓝'), 
            ('darkslategray', '深岩灰'), ('darkslategrey', '深岩灰'), ('darkturquoise', '深松石绿'), ('darkviolet', '深紫'), ('deeppink', '深粉'), 
            ('deepskyblue', '深天蓝'), ('dimgray', '昏灰'), ('dimgrey', '昏灰'), ('dodgerblue', '湖蓝'), ('firebrick', '火砖红'), 
            ('floralwhite', '花卉白'), ('forestgreen', '森林绿'), ('fuchsia', '洋红'), ('gainsboro', '庚氏灰'), ('ghostwhite', '幽灵白'), 
            ('gold', '金'), ('goldenrod', '金菊'), ('gray', '灰'), ('green', '绿'), ('greenyellow', '黄绿'),  ('honeydew', '蜜瓜绿'), 
            ('hotpink', '艳粉'), ('indianred', '印度红'), ('indigo', '靛蓝'), ('ivory', '象牙白'), ('khaki', '卡其'), ('lavender', '薰衣草紫'), 
            ('lavenderblush', '薰衣草红'), ('lawngreen', '草坪绿'), ('lemonchiffon', '柠檬绸黄'), ('lightblue', '浅蓝'), ('lightcoral', '浅珊瑚红'), 
            ('lightcyan', '浅青'), ('lightgoldenrodyellow', '浅金菊黄'), ('lightgray', '亮灰'), ('lightgreen', '浅绿'), ('lightgrey', '亮灰'), 
            ('lightpink', '浅粉'), ('lightsalmon', '浅鲑红'), ('lightseagreen', '浅海藻绿'), ('lightskyblue', '浅天蓝'), ('lightslategray', '浅岩灰'), 
            ('lightslategrey', '浅岩灰'), ('lightsteelblue', '浅钢青'), ('lightyellow', '浅黄'), ('lime', '绿'), ('limegreen', '青柠绿'), 
            ('linen', '亚麻'), ('magenta', '洋红'), ('maroon', '栗'), ('mediumaquamarine', '中碧绿'), ('mediumblue', '中蓝'), ('mediumorchid', '中洋兰紫'), 
            ('mediumpurple', '中紫'), ('mediumseagreen', '中海藻绿'), ('mediumslateblue', '中岩蓝'), ('mediumspringgreen', '中嫩绿'), 
            ('mediumturquoise', '中松石绿'), ('mediumvioletred', '中紫红'), ('midnightblue', '午夜蓝'), ('mintcream', '薄荷乳白'), 
            ('mistyrose', '雾玫瑰红'), ('moccasin', '鹿皮'), ('navajowhite', '土著白'), ('navy', '藏青'), ('oldlace', '旧蕾丝白'), ('olive', '橄榄'), 
            ('olivedrab', '橄榄绿'), ('orange', '橙'), ('orangered', '橘红'), ('orchid', '洋兰紫'), ('palegoldenrod', '白金菊黄'), ('palegreen', '白绿'), 
            ('paleturquoise', '白松石绿'), ('palevioletred', '白紫红'), ('papayawhip', '番木瓜橙'), ('peachpuff', '粉朴桃'), ('peru', '秘鲁红'), 
            ('pink', '粉'), ('plum', '李紫'), ('powderblue', '粉末蓝'), ('purple', '紫'), ('rebeccapurple', '丽贝卡紫'), ('red', '红'), 
            ('rosybrown', '玫瑰褐'), ('royalblue', '品蓝'), ('saddlebrown', '鞍褐'), ('salmon', '鲑红'), ('sandybrown', '沙褐'), ('seagreen', '海藻绿'), 
            ('seashell', '贝壳白'), ('sienna', '土黄赭'), ('silver', '银'), ('skyblue', '天蓝'), ('slateblue', '岩蓝'), ('slategray', '岩灰'), 
            ('slategrey', '岩灰'), ('snow', '雪白'), ('springgreen', '春绿'), ('steelblue', '钢青'), ('tan', '日晒褐'), ('teal', '鸭翅绿'), 
            ('thistle', '蓟紫'), ('tomato', '番茄红'), ('turquoise', '松石绿'), ('violet', '紫罗兰'), ('wheat', '麦'), ('white', '白'), 
            ('whitesmoke', '烟雾白'), ('yellow', '黄'), ('yellowgreen', '暗黄绿')
        ]
    
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
    
    def color2c(self, color, size=None, drop=False):
        """检查颜色参数，将字符串、元组、列表等类型的颜色转numpy数组颜色
        
        color       - 待处理的颜色
        size        - 返回的颜色数量，有3种可能的类型：None、整型、长度为2的元组或列表
        drop        - 舍弃alpha通道
        """
        
        if isinstance(color, str):
            color = self.str2color(color)
        elif isinstance(color, (list, tuple)):
            color = np.array(color, dtype=np.float64)
        
        if not isinstance(color, np.ndarray):
            raise ValueError('未定义的或不符合规则的颜色：%s'%str(color))
        if color.shape[-1] not in (3,4) or np.nanmin(color) < 0 or np.nanmax(color) > 255:
            raise ValueError('未定义的或不符合规则的颜色：%s'%str(color))
        
        if isinstance(size, int):
            if color.ndim == 1:
                color = np.tile(color, (size,1))
            elif color.ndim == 2:
                if color.shape[0] != size:
                    raise ValueError('未定义的或不符合规则的颜色：%s'%str(color))
            else:
                raise ValueError('未定义的或不符合规则的颜色：%s'%str(color))
        elif isinstance(size, (tuple, list)) and len(size) == 2:
            if color.ndim == 1:
                color = np.tile(color, (*size,1))
            elif color.ndim == 3:
                if color.shape[:-1] != size:
                    raise ValueError('未定义的或不符合规则的颜色：%s'%str(color))
            else:
                raise ValueError('未定义的或不符合规则的颜色：%s'%str(color))
        elif not size is None:
            raise ValueError('未定义的或不符合规则的颜色：%s'%str(color))
        
        if drop and color.shape[-1] == 4:
            color = color[..., :-1]
        
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

if __name__  == '__main__':
    cm = ColorManager()
    s1 = set(cm.color_list)
    s2 = set([item[1] for item in cm.color_help()])
    print(len(s1), len(s2))
    print(s1-s2)
    print(s2-s1)
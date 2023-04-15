# -*- coding: utf-8 -*-

import re
import numpy as np
import matplotlib
from matplotlib import cm as mcm

class ColorManager:
    """颜色管理类"""
 
    def __init__(self):
        """构造函数"""
 
        self.default_colors = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#1f77b4', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
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
    def colors(self):
        """全部颜色"""
 
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
            ('gold', '金'), ('goldenrod', '金菊'), ('gray', '灰'), ('green', '绿'), ('greenyellow', '黄绿'), ('grey', '灰'),  ('honeydew', '蜜瓜绿'), 
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
 
    @property
    def cmaps(self):
        """调色板列表"""
 
        return [
            ('视觉均匀类', ['viridis', 'plasma', 'inferno', 'magma', 'cividis']), 
            ('单调变化类', ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']), 
            ('近似单调类', ['binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper']), 
            ('亮度发散类', ['PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic']), 
            ('颜色循环类', ['twilight', 'twilight_shifted', 'hsv']),
            ('分段阶梯类', ['Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2', 'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c']), 
            ('专属定制类', ['flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg', 'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar'])
        ]

    def _hex2color(self, str_hex):
        """以#为前缀的十六进制颜色转numpy数组颜色"""
 
        if len(str_hex) == 3:
            color = np.array((int(str_hex[1:2],base=16)/16, int(str_hex[2:3],base=16)/16, int(str_hex[3:],base=16)/16), dtype=np.float32)
        else:
            color = np.array((int(str_hex[1:3],base=16)/255, int(str_hex[3:5],base=16)/255, int(str_hex[5:],base=16)/255), dtype=np.float32)
 
        return color

    def _str2color(self, color):
        """字符串表示的颜色转numpy数组颜色"""
 
        if color in self._colors:
            return self._hex2color(self._colors[color])
        elif re.compile(r'#[\da-fA-F]{3}$').match(color) or re.compile(r'#[\da-fA-F]{6}$').match(color):
            return self._hex2color(color)
        else:
            raise ValueError('未定义的或不符合规则的颜色：%s'%color)

    def format_color(self, color, cid=0, repeat=None):
        """检查颜色参数，将字符串、元组、列表等类型的颜色转为浮点型的numpy数组

        color       - 预定义颜色、十六进制颜色，或者浮点型元组、列表或numpy数组
        cid         - 缺省颜色id
        repeat      - 若color为单个颜色，repeat表示重复次数或重复行列数
        """

        if color is None:
            color = self._hex2color(self.default_colors[cid])
        elif isinstance(color, str):
            color = self._str2color(color)
        elif isinstance(color, (list, tuple, np.ndarray)):
            color = np.array(color, dtype=np.float32)
            cmin, cmax = color.min(), color.max()
            if cmax > 1 or cmin < 0:
                color = (color - cmin) / (cmax - cmin)
        else:
            raise ValueError('未定义的或不符合规则的颜色')

        if color.shape[-1] not in (3,4):
            raise ValueError('未定义的或不符合规则的颜色')

        if color.ndim == 1:
            if isinstance(repeat, int): 
                color = np.tile(color, (repeat,1))
            elif isinstance(repeat, (tuple, list)):
                color = np.tile(color, (*repeat,1))

        return color
 
    def cmap(self, data, cm, drange=None, alpha=None, invalid=np.nan, invalid_c=(0,0,0,0)):
        """数值映射到颜色
 
        data        - 数据
        cm          - 调色板
        drange      - 数据动态范围，None表示使用data的动态范围
        alpha       - 透明度，None表示不改变当前透明度
        invalid     - 无效数据的标识
        invalid_c   - 无效数据的颜色
        """
 
        data = np.float64(data)

        if not np.isnan(invalid):
            data[data==invalid] = np.nan
        invalid_pos = np.isnan(data) # 记录无效数据位置
 
        dmin, dmax = (np.nanmin(data), np.nanmax(data)) if drange is None else drange
        data[data<dmin] = dmin
        data[data>dmax] = dmax
        data = np.uint8(255*(data-dmin)/(dmax-dmin))
 
        cs = self.get_cm_colors(cm)
        color = cs[data]
        color[invalid_pos] = invalid_c
 
        if isinstance(alpha, (int, float)) and 0 <= alpha <= 1:
            color[..., 3] = alpha
 
        return color

    def get_cm_colors(self, cm):
        """返回给定调色板的颜色列表"""

        if cm not in self._cmaps:
            raise ValueError('未知的调色板%s'%cm)
 
        cmo = mcm.get_cmap(cm)
        cs, k = list(), 256/cmo.N
        for i in range(cmo.N):
            c = cmo(i)
            for j in range(int(i*k), int((i+1)*k)):
                cs.append(c)
        
        return np.array(cs)

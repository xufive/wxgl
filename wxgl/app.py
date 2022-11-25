#!/usr/bin/env python3

from . scheme import Scheme

#try:
#    from . wxfigure import WxFigure as Figure
#except:
#    from . glutfigure import GlutFigure as Figure

from . wxfigure import WxFigure as Figure
#from . qtfigure import QtFigure as Figure
#from . glutfigure import GlutFigure as Figure

class App(Scheme):
    """应用程序类"""

    def __init__(self, **kwds):
        """构造函数

        kwds        - 关键字参数
            size        - 窗口分辨率，默认960×640
            bg          - 画布背景色，默认(0.0, 0.0, 0.0)
            haxis       - 高度轴，默认y轴，可选z轴，不支持x轴
            fovy        - 相机水平视野角度，默认50°
            azim        - 方位角，默认0°
            elev        - 高度角，默认0°
            azim_range  - 方位角变化范围，默认-180°～180°
            elev_range  - 高度角变化范围，默认-180°～180°
            smooth      - 直线和点的反走样，默认True
        """

        for key in kwds:
            if key not in ['size', 'bg', 'haxis', 'fovy', 'azim', 'elev', 'azim_range', 'elev_range', 'smooth']:
                raise KeyError('不支持的关键字参数：%s'%key)
 
        self.kwds = kwds
        Scheme.__init__(self, haxis=kwds.get('haxis', 'y'), bg=kwds.get('bg', (0.0, 0.0, 0.0)))

    def show(self):
        """显示"""

        fig = Figure(self, **self.kwds)
        fig.loop()

        self.reset()


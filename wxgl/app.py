#!/usr/bin/env python3

import os
from . scheme import Scheme
from . glutfigure import show_figure

try:
    from . wxfigure import show_wxfigure
    wx_is_installed = True
except:
    wx_is_installed = False
    
try:
    from . qtfigure import show_qtfigure
    qt_is_installed = True
except:
    qt_is_installed = False

class App(Scheme):
    """应用程序类"""

    def __init__(self, backend='auto', **kwds):
        """构造函数

        backend     - 后端GUI库，可选wx或qt，None表示使用glut，默认auto（按照wx/qt/glut优先级自动选择）
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
 
        self.backend = backend
        self.kwds = kwds
        Scheme.__init__(self, haxis=kwds.get('haxis', 'y'), bg=kwds.get('bg', (0.0, 0.0, 0.0)))

    def show(self):
        """显示画布"""

        if self.backend in ('auto', 'Auto', 'AUTO'):
            if wx_is_installed:
                show_wxfigure(self)
            elif qt_is_installed:
                show_qtfigure(self)
            else:
                show_figure(self)
        elif self.backend in ('wx', 'Wx', 'WX'):
            if wx_is_installed:
                show_wxfigure(self)
            else:
                print('当前系统没有找到wxpython模块，程序将自动选择可用的后端组件') 
                if qt_is_installed:
                    show_qtfigure(self)
                else:
                    show_figure(self)
        elif self.backend in ('qt', 'Qt', 'QT'):
            if qt_is_installed:
                show_qtfigure(self)
            else:
                print('当前系统没有找到pyqt6模块，程序将自动选择可用的后端组件') 
                if wx_is_installed:
                    show_wxfigure(self)
                else:
                    show_figure(self)
        else:
            show_figure(self)

    def savefig(self, outfile, dpi=None, fps=25, frames=100, loop=0, quality=100):
        """保存画布为图像文件或动画文件。outfile为文件名，支持.png和.jpg格式

        outfile     - 输出文件名，支持的文件格式：'.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.avi', '.wmv', '.mov' 
        dpi         - 图像文件每英寸像素数
        fps         - 动画文件帧率
        frames      - 动画文件总帧数
        loop        - gif文件播放次数，0表示循环播放
        quality     - webp文件质量，100表示最高品质
        """
        
        fpath, fname = os.path.split(outfile)
        ext = os.path.splitext(fname)[-1].lower()

        if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.avi', '.wmv', '.mov'):
            raise ValueError('不支持的文件格式：%s'%ext)

        if not os.path.isdir(fpath):
            os.makedirs(fpath)

        show_figure(self, outfile=outfile, ext=ext, dpi=dpi, fps=fps, frames=frames, loop=loop, quality=quality)


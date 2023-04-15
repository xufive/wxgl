#!/usr/bin/env python3

import os, sys
from . scheme import Scheme

try:
    from . wxfigure import show_wxfigure
    wx_is_available = True
except:
    wx_is_available = False
    
try:
    from . qtfigure import show_qtfigure
    qt_is_available = True
except:
    qt_is_available = False
    
try:
    from . glutfigure import show_figure
    glut_is_available = True
except:
    glut_is_available = False

class App(Scheme):
    """应用程序类"""

    def __init__(self, backend='auto', **kwds):
        """构造函数

        backend     - 后端GUI库，可选wx或qt，默认auto（按照wx/qt优先级自动选择）
        kwds        - 关键字参数
            size        - 窗口分辨率，默认(960, 640)
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
 
        self.backend = backend.lower()
        self.kwds = kwds
        Scheme.__init__(self, haxis=kwds.get('haxis', 'y'), bg=kwds.get('bg', (0.0, 0.0, 0.0)))

    def savefig(self, outfile, dpi=None, fps=25, frames=100, loop=0, quality=100):
        """保存画布为图像文件或动画文件

        outfile     - 输出文件名，支持的文件格式：'.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.avi', '.wmv', '.mov' 
        dpi         - 图像文件每英寸像素数
        fps         - 动画文件帧率
        frames      - 动画文件总帧数
        loop        - gif文件播放次数，0表示循环播放
        quality     - webp文件质量，100表示最高品质
        """
        
        if outfile is None:
            ext = None
        else:
            fpath, fname = os.path.split(outfile)
            ext = os.path.splitext(fname)[-1].lower()

            if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.avi', '.wmv', '.mov'):
                raise ValueError('不支持的文件格式：%s'%ext)

            if sys.platform.lower() == 'darwin' and ext == '.webp':
                raise ValueError('MacOS平台上WxGL不支持的文件格式：.webp')

            if fpath and not os.path.isdir(fpath):
                os.makedirs(fpath)

        if self.backend == 'wx':
            if wx_is_available:
                show_wxfigure(self, outfile=outfile, ext=ext, dpi=dpi, fps=fps, frames=frames, loop=loop, quality=quality)
            else:
                print('当前系统导入wxpython失败，请检查或重新安装wxpython')
        elif self.backend =='qt':
            if qt_is_available:
                show_qtfigure(self, outfile=outfile, ext=ext, dpi=dpi, fps=fps, frames=frames, loop=loop, quality=quality)
            else:
                print('当前系统导入pyqt6失败，请检查或重新安装pyqt6')
        elif self.backend == 'glut':
            if glut_is_available:
                show_figure(self, outfile=outfile, ext=ext, dpi=dpi, fps=fps, frames=frames, loop=loop, quality=quality)
            else:
                print('当前版本的pyopengl自带的glut库不可用，请检查或重新安装pyopengl')
        else:
            if wx_is_available:
                show_wxfigure(self, outfile=outfile, ext=ext, dpi=dpi, fps=fps, frames=frames, loop=loop, quality=quality)
            elif qt_is_available:
                show_qtfigure(self, outfile=outfile, ext=ext, dpi=dpi, fps=fps, frames=frames, loop=loop, quality=quality)
            elif glut_is_available:
                print('未发现可用的显示后端，暂用glut替代（功能受限），建议安装wxpython或pyqt6')
                show_figure(self, outfile=outfile, ext=ext, dpi=dpi, fps=fps, frames=frames, loop=loop, quality=quality)
            else:
                print('未发现可用的显示后端，建议安装wxpython或pyqt6')

    def show(self):
        """显示画布"""

        self.savefig(None)
        self._reset()


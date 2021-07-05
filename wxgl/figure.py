# -*- coding: utf-8 -*-
#
# MIT License
# 
# Copyright (c) 2021 Tianyuan Langzi
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


"""
WxGL: 基于pyopengl的三维数据可视化库

WxGL以wx为显示后端，提供matplotlib风格的交互绘图模式
同时，也可以和wxpython无缝结合，在wx的窗体上绘制三维模型
"""


import os
import uuid
import wx
import wx.lib.agw.aui as aui
import numpy as np
import imageio
from PIL import Image

from . import scene
from . import axes
from . import cm


BASE_PATH = os.path.dirname(__file__)


class WxGLFrame(wx.Frame):
    """绘图窗口主界面"""
    
    ID_STYLE = wx.NewIdRef()    # 风格
    ID_RESTORE = wx.NewIdRef()  # 相机复位
    ID_SAVE = wx.NewIdRef()     # 保存
    ID_PAUSE = wx.NewIdRef()    # 动态显示
    ID_GRID = wx.NewIdRef()     # 网格
    
    id_white = wx.NewIdRef()    # 珍珠白
    id_black = wx.NewIdRef()    # 石墨黑
    id_gray = wx.NewIdRef()     # 国际灰
    id_blue = wx.NewIdRef()     # 太空蓝
    
    def __init__(self, parent, size):
        """构造函数"""
        
        wx.Frame.__init__(self, None, -1, 'wxPlot', style=wx.DEFAULT_FRAME_STYLE)
        self.SetSize(parent.size)
        self.Center()
        self.SetIcon(wx.Icon(os.path.join(BASE_PATH, 'res', 'wxplot.ico')))
        
        self.scene = scene.WxGLScene(self, style=parent.style3d, **parent.kwds)
        self.parent = parent
        self.csize = self.scene.GetClientSize()
        
        bmp_style = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_style_32.png'), wx.BITMAP_TYPE_ANY)
        bmp_restore = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_restore_32.png'), wx.BITMAP_TYPE_ANY)
        bmp_save = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_save_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_play = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_play_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_stop = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_stop_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_show = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_show_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_hide = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_hide_32.png'), wx.BITMAP_TYPE_ANY)
        
        self.tb = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize)
        self.tb.SetToolBitmapSize(wx.Size(32, 32))
        
        self.tb.AddSimpleTool(self.ID_STYLE, '风格', bmp_style, '绘图风格')
        self.tb.AddSeparator()
        self.tb.AddSimpleTool(self.ID_RESTORE, '复位', bmp_restore, '位置还原')
        self.tb.AddSimpleTool(self.ID_SAVE, '保存', bmp_save, '保存为文件')
        self.tb.AddSeparator()
        self.tb.AddSimpleTool(self.ID_GRID, '网格', self.bmp_hide, '显示/隐藏网格')
        self.tb.AddSimpleTool(self.ID_PAUSE, '动态显示', self.bmp_play, '停止/开启动态显示）')
        
        self.tb.SetToolDropDown(self.ID_STYLE, True)
        self.tb.Realize()
        
        self._mgr = aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        self._mgr.AddPane(self.scene, aui.AuiPaneInfo().Name('Scene').CenterPane().Show())
        self._mgr.AddPane(self.tb, aui.AuiPaneInfo().Name('ToolBar').ToolbarPane().Bottom().Floatable(False))
        self._mgr.Update()
        
        self.once_timer = wx.Timer() # 单次定时器
        self.once_timer.Bind(wx.EVT_TIMER, self.on_once_timer)
        
        self.folder = None
        self.fs = None
        self.fps = None
        self.format =None
        self.mod = None
        self.f = None
        self.last =None
        
        self.scene.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.on_style, id=self.ID_STYLE)
        
        self.Bind(wx.EVT_MENU, self.on_save, id=self.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_style, id=self.ID_STYLE)
        self.Bind(wx.EVT_MENU, self.on_pause, id=self.ID_PAUSE)
        self.Bind(wx.EVT_MENU, self.on_restore, id=self.ID_RESTORE)
        self.Bind(wx.EVT_MENU, self.on_grid, id=self.ID_GRID)
        
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_white)
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_black)
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_gray)
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_blue)
    
    def on_once_timer(self, evt):
        """单次定时器函数"""
        
        if self.f < self.fs:
            if self.scene.sys_n != self.last and self.scene.sys_n%self.mod == 0:
                fn = os.path.join(self.folder, '%03d_%d.png'%(self.f, self.scene.sys_n))
                self.scene.repaint()
                self.scene.save_scene(fn, alpha=True, crop=True)
                self.last = self.scene.sys_n
                self.f += 1
        else:
            self.once_timer.Stop()
            
            fns = os.listdir(self.folder)
            fns.sort()
            
            if self.format.lower() == 'gif':
                ims = [Image.open(os.path.join(self.folder,fn)) for fn in fns]
                imageio.mimsave(os.path.join(self.folder, 'out.gif'), ims, format='GIF', fps=self.fps, loop=0)
            elif self.format.lower() == 'mp4':
                writer = imageio.get_writer(os.path.join(self.folder, 'out.mp4'), fps=self.fps)
                for fn in fns:
                    writer.append_data(imageio.imread(os.path.join(self.folder,fn)))
                writer.close()
            
            self.Destroy()
    
    def on_color(self, evt):
        """选择风格"""
        
        idx = evt.GetId()
        if idx == self.id_black.Id:
            color = 'black'
        elif idx == self.id_gray.Id:
            color = 'gray'
        elif idx == self.id_blue.Id:
            color = 'blue'
        else:
            color = 'white'
        
        self.scene.set_style(color)
        self.parent.redraw()
        self.scene.Refresh(False)
    
    def on_style(self, evt):
        """设置背景颜色"""
        
        tb = evt.GetEventObject()
        tb.SetToolSticky(evt.GetId(), True)
        
        submenu = wx.Menu()
        bmp_white = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'white_16.png'), wx.BITMAP_TYPE_ANY)
        bmp_black = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'black_16.png'), wx.BITMAP_TYPE_ANY)
        bmp_gray = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'gray_16.png'), wx.BITMAP_TYPE_ANY)
        bmp_blue = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'blue_16.png'), wx.BITMAP_TYPE_ANY)
        
        m1 =  wx.MenuItem(submenu, self.id_white, "珍珠白")
        m1.SetBitmap(bmp_white)
        submenu.Append(m1)

        m2 =  wx.MenuItem(submenu, self.id_black, "石墨黑")
        m2.SetBitmap(bmp_black)
        submenu.Append(m2)

        m3 =  wx.MenuItem(submenu, self.id_gray, "国际灰")
        m3.SetBitmap(bmp_gray)
        submenu.Append(m3)

        m4 =  wx.MenuItem(submenu, self.id_blue, "太空蓝")
        m4.SetBitmap(bmp_blue)
        submenu.Append(m4)

        self.PopupMenu(submenu)
        tb.SetToolSticky(evt.GetId(), False)
        
    def on_resize(self, evt):
        """响应窗口尺寸改变事件"""
        
        self.csize = self.scene.GetClientSize()
        if self.scene.osize is None:
            self.scene.osize = self.csize
        self.scene.size = self.csize
        self.scene.tscale = (self.csize[0]/self.scene.osize[0], self.csize[1]/self.scene.osize[1])
        
        self.parent.redraw()
        self.scene.update_grid()
        self.scene.Refresh(False)
        
        evt.Skip()
    
    def on_restore(self, evt):
        """回到初始状态"""
        
        self.scene.restore_posture()
    
    def on_grid(self, evt):
        """显示/隐藏坐网格"""
        
        self.scene.grid_is_show = not self.scene.grid_is_show
        if self.scene.grid_is_show:
            self.tb.SetToolBitmap(self.ID_GRID, self.bmp_hide)
            self.tb.SetToolShortHelp(self.ID_GRID, '隐藏网格')
        else:
            self.tb.SetToolBitmap(self.ID_GRID, self.bmp_show)
            self.tb.SetToolShortHelp(self.ID_GRID, '显示网格')
        
        for ax in self.scene.subgraphs:
            for key in ax.reg_main.grid:
                if ax.grid_is_show and self.scene.grid_is_show:
                    ax.reg_main.show_model(ax.reg_main.grid[key])
                else:
                    ax.reg_main.hide_model(ax.reg_main.grid[key])
        
        self.tb.Realize()
        self.scene.update_grid()
        self.scene.Refresh(False)
    
    def on_pause(self, evt):
        """暂停/启动"""
        
        self.scene.pause_sys_timer()
        if self.scene.sys_timer.IsRunning():
            self.tb.SetToolBitmap(self.ID_PAUSE, self.bmp_stop)
            self.tb.SetToolShortHelp(self.ID_PAUSE, '停止动态显示')
        else:
            self.tb.SetToolBitmap(self.ID_PAUSE, self.bmp_play)
            self.tb.SetToolShortHelp(self.ID_PAUSE, '开启动态显示')
        
        self.tb.Realize()
    
    def on_save(self, evt):
        """保存为文件"""
        
        wildcard = 'PNG files (*.png)|*.png|JPEG file (*.jpg)|*.jpg'
        dlg = wx.FileDialog(self, message='保存为文件', defaultDir=os.getcwd(), defaultFile="", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        dlg.SetFilterIndex(0)
        
        if dlg.ShowModal() == wx.ID_OK:
            fn = dlg.GetPath()
            alpha = os.path.splitext(fn)[-1] == '.png'
            self.scene.save_scene(fn, alpha=alpha)
        
        dlg.Destroy()


def single_figure(cls):
    """画布类单实例模式装饰器"""
    
    _instance = {}

    def _single_figure(**kwds):
        for key in kwds:
            if key not in ['size', 'style2d', 'style3d', 'dist', 'view', 'elevation', 'azimuth', 'zoom']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        if cls not in _instance:
            _instance[cls] = cls(**kwds)
        else:
            if 'size' in kwds:
                _instance[cls].size = kwds['size']
            if 'style2d' in kwds:
                _instance[cls].style2d = kwds['style2d']
            if 'style3d' in kwds:
                _instance[cls].style3d = kwds['style3d']
            if 'dist' in kwds:
                _instance[cls].kwds.update({'dist': kwds['dist']})
            if 'view' in kwds:
                _instance[cls].kwds.update({'view': kwds['view']})
            if 'elevation' in kwds:
                _instance[cls].kwds.update({'elevation': kwds['elevation']})
            if 'azimuth' in kwds:
                _instance[cls].kwds.update({'azimuth': kwds['azimuth']})
            if 'zoom' in kwds:
                _instance[cls].kwds.update({'zoom': kwds['zoom']})
        
        return _instance[cls]

    return _single_figure


@single_figure
class WxGLFigure:
    """画布类"""
    
    def __init__(self, **kwds):
        """构造函数
        
        kwds        - 关键字参数
                        size        - 画布分辨率， 默认1280x960
                        style2d     - 2D模式下的默认风格，默认
                        style3d     - 3D模式下的默认风格
                        dist        - 眼睛与ECS原点的距离
                        view        - 视景体
                        elevation   - 仰角
                        azimuth     - 方位角
                        zoom        - 视口缩放因子
        """
        
        dist = kwds.get('dist', 5)
        view = kwds.get('view', [-1, 1, -1, 1, 2.6, 1000])
        elevation = kwds.get('elevation', 5)
        azimuth = kwds.get('azimuth', 25)
        zoom = kwds.get('zoom', 1.0)
        
        self.size = kwds.get('size', (1280,960))
        self.style2d = kwds.get('style2d', 'white')
        self.style3d = kwds.get('style3d', 'blue')
        self.kwds = {'dist':dist, 'view':view, 'elevation':elevation, 'azimuth':azimuth, 'zoom':zoom}
        
        self.app = None
        self.ff = None
        self.cm = cm.ColorManager()
        self.curr_ax = None
        self.assembly = list()
    
    def _create_frame(self):
        """生成窗体"""
        
        if not self.app:
            self.app = wx.App()
        
        if not self.ff:
            self.ff = WxGLFrame(self, self.size)
            self.curr_ax = None
            self.assembly = list()
    
    def _destroy_frame(self):
        """销毁窗体"""
        
        self.app.Destroy()
        
        del self.ff
        del self.app
        
        self.app = None
        self.ff = None
    
    def _draw(self):
        """绘制"""
        
        for item in self.assembly:
            getattr(item[0], item[1])(*item[2], **item[3])
        
        for ax in self.ff.scene.subgraphs:
            if self.ff.scene.mode == '2D':
                if ax.axis_is_show:
                    ax.reg_main.ticks2d(
                        xlabel=ax.labelx, ylabel=ax.labely, 
                        xf=ax.xf, yf=ax.yf, 
                        xd=ax.xd, yd=ax.yd, 
                        xrotate=ax.rotatex,
                        yreverse=ax.reversey,
                        grid=ax.grid_is_show
                    )
                
                cw, ch = self.ff.csize[0]*ax.reg_main.box[2], self.ff.csize[1]*ax.reg_main.box[3]
                w, h = ax.reg_main.r_x[1]-ax.reg_main.r_x[0], ax.reg_main.r_y[1]-ax.reg_main.r_y[0]
                cd, d = max(cw, ch), max(w, h)
                cw, ch = cw/cd, ch/cd
                w, h = w/d, h/d
                
                if ch < 1 and h < 1:
                    self.ff.scene.set_posture(zoom=1.5*max(ch, h), save=True)
                elif cw < 1 and w < 1:
                    self.ff.scene.set_posture(zoom=1.5*max(ch, h), save=True)
            else:
                if ax.grid_is_show:
                    ax.reg_main.ticks3d(
                        xlabel=ax.labelx, ylabel=ax.labely, zlabel=ax.labelz, 
                        xf=ax.xf, yf=ax.yf, zf=ax.zf, 
                        xd=ax.xd, yd=ax.yd, zd=ax.zd, 
                        bg=(0.9,1.0,0.6,0.1)
                    )
        
        if not self.ff.scene.sys_timer.IsRunning():
            self.ff.tb.EnableTool(self.ff.ID_PAUSE, False)
    
    def redraw(self):
        """重新绘制"""
        
        for reg in self.ff.scene.regions:
            reg.reset()
        
        self._draw()
    
    def show(self, rotate=None):
        """显示画布。rotate为每个定时周期内水平旋转的角度，浮点数，None表示无旋转"""
        
        if not rotate is None:
            self.ff.scene.rotate = rotate
            self.ff.scene.start_sys_timer()
        
        self._create_frame()
        try:
            self._draw()
            self.ff.Show()
            self.app.MainLoop()
        except Exception as e:
            print(str(e))
        finally:
            self._destroy_frame()
    
    def savefig(self, fn):
        """保存画布为文件。fn为文件名，支持.png和.jpg格式"""
        
        self._create_frame()
        try:
            self._draw()
            self.ff.scene.repaint()
            self.ff.scene.save_scene(fn, alpha=os.path.splitext(fn)[-1]=='.png')
        except:
            pass
        finally:
            self._destroy_frame()
    
    def capture(self, folder, fs=50, fps=10, format='gif', fi=0, mod=5, rotate=None):
        """连续保存缓冲区为图片文件
        
        folder      - 图片文件保存路径
        fs          - 总帧数
        fps         - 每秒帧数
        format      - 输出格式，支持GIF和MP4两种格式
        fi          - 计数器初值
        mod         - 计数器有效计数的间隔数
        rotate      - 视点坐标系旋转
        """
        
        assert os.path.isdir(folder), '%s不是一个合法的路径或该路径不存在'%folder
        
        if not rotate is None:
            self.ff.scene.rotate = rotate
        
        self._create_frame()
        try:
            self._draw()
            self.ff.scene.start_sys_timer()
            
            self.ff.folder = folder
            self.ff.fs = fs
            self.ff.fps = fps
            self.ff.format = format
            self.ff.mod = mod
            self.ff.f = 0
            
            self.ff.scene.sys_n = fi
            self.ff.last = self.ff.scene.sys_n
            self.ff.once_timer.Start(10)
            
            self.app.MainLoop()
        except:
            pass
        finally:
            self._destroy_frame()
    
    def add_axes(self, pos=111):
        """添加子图
        
        pos         - 子图在场景中的位置和大小
                        三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                        四元组      - 以画布左下角为原点，宽度和高度都是1。四元组分别表示子图左下角在画布上的水平、垂直位置和宽度、高度
        """
        
        self._create_frame()
        self.curr_ax = axes.WxGLAxes(self.ff.scene, pos)
        self.ff.scene.subgraphs.append(self.curr_ax)
        
        return self.curr_ax
    
    def add_widget(self, reg, func, *args, **kwds):
        """添加部件"""
        
        self.assembly.append([reg, func, list(args), kwds])

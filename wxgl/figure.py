# -*- coding: utf-8 -*-

import os, time
import platform
import wx
import wx.lib.agw.aui as aui
import wx.lib.buttons as wxbtn
import configparser

from . import scene
from . import axes


BASE_PATH = os.path.dirname(__file__)
PLAT_FORM = platform.system()

def single_figure(cls):
    """画布类单实例模式装饰器"""
    
    _instance = {}

    def _single_figure(**kwds):
        for key in kwds:
            if key not in ['size', 'proj', 'oecs', 'dist', 'azim', 'elev', 'near', 'far', 'zoom', 'smooth', 'azim_range', 'elev_range', 'style']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        if cls not in _instance:
            _instance[cls] = cls(**kwds)
        else:
            if 'size' in kwds:
                _instance[cls].size = kwds.pop('size')
            if 'style' in kwds:
                _instance[cls].style = kwds['style']
            
            _instance[cls].kwds3d.update(kwds)
        
        return _instance[cls]

    return _single_figure


@single_figure
class Figure:
    """画布类"""
    
    def __init__(self, size=(1152,648), **kwds):
        """构造函数
        
        size        - 窗口分辨率
        kwds        - 3D场景参数
            proj        - 投影模式，'ortho' - 正射投影，'frustum' - 透视投影（默认）
            oecs        - 视点坐标系ECS原点，默认与目标坐标系OCS原点重合
            dist        - 相机与ECS原点的距离，默认5个长度单位
            azim        - 方位角，默认0°
            elev        - 高度角，默认0°
            near        - 视锥体前面距离相机的距离，默认3个长度单位
            far         - 视锥体后面距离相机的距离，默认1000个长度单位
            zoom        - 视口缩放因子，默认1.0
            smooth      - 直线、多边形和点的反走样开关
            azim_range  - 方位角限位器，默认-180°~180°
            elev_range  - 仰角限位器，默认-180°~180°
            style       - 场景风格，默认太空蓝
                'white'     - 珍珠白
                'black'     - 石墨黑
                'gray'      - 国际灰
                'blue'      - 太空蓝
                'royal'     - 宝石蓝
        """
        
        self.size = size                            # 画布大小
        self.kwds3d = kwds                          # 3d场景的参数
        self.style = kwds.get('style', None)        # 背景色
        self.folder = os.getcwd()                   # 保存路径
        self.ext = '.gif'                           # 输出文件格式
        self.fps = 25                               # 输出GIF或视频的帧率
        self.loop = 0                               # GIF循环次数
        self.fn = 50                                # 输出文件总帧数
        
        self.app = None                             # wx.App对象
        self.ff = None                              # wx.Frame对象
        self.axes_list = list()                     # 子图列表
        self.curr_ax = None                         # 当前子图
        
        self.fn_cfg = os.path.join(BASE_PATH, "custom.ini")
        self.cfg = configparser.ConfigParser()
        
        if self.cfg.read(self.fn_cfg) and self.cfg.has_section('custom'):
            if self.style:
                self.cfg.set('custom', 'style', self.style)
            elif self.cfg.has_option('custom', 'style'):
                self.style = self.cfg.get('custom', 'style')
                self.kwds3d.update({'style':self.style})
            else:
                self.style = 'blue'
                self.cfg.set('custom', 'style', self.style)
                self.kwds3d.update({'style':self.style})
            
            if self.cfg.has_option('custom', 'folder'):
                self.folder = self.cfg.get('custom', 'folder')
            else:
                self.cfg.set('custom', 'folder', self.folder)
            
            if self.cfg.has_option('custom', 'ext'):
                self.ext = self.cfg.get('custom', 'ext')
            else:
                self.cfg.set('custom', 'ext', self.ext)
            
            if self.cfg.has_option('custom', 'fps'):
                self.fps = int(self.cfg.get('custom', 'fps'))
            else:
                self.cfg.set('custom', 'fps', str(self.fps))
            
            if self.cfg.has_option('custom', 'loop'):
                self.loop = int(self.cfg.get('custom', 'loop'))
            else:
                self.cfg.set('custom', 'loop', str(self.loop))
            
            if self.cfg.has_option('custom', 'fn'):
                self.fn = int(self.cfg.get('custom', 'fn'))
            else:
                self.cfg.set('custom', 'fn', str(self.fn))
        else:
            self.cfg.add_section('custom')
            if self.style is None:
                self.style = 'blue'
                self.kwds3d.update({'style':self.style})
            
            self.cfg.set('custom', 'style', self.style)
            self.cfg.set('custom', 'folder', self.folder)
            self.cfg.set('custom', 'ext', self.ext)
            self.cfg.set('custom', 'fps', str(self.fps))
            self.cfg.set('custom', 'loop', str(self.loop))
            self.cfg.set('custom', 'fn', str(self.fn))
        
        with open(self.fn_cfg, 'w') as fp:
            self.cfg.write(fp)
    
    def _create_frame(self):
        """生成窗体"""
        
        if not self.app:
            self.app = wx.App()
        
        if not self.ff:
            self.ff = FigureFrame(self)
            self.curr_ax = None
    
    def _destroy_frame(self):
        """销毁窗体"""
        
        self.axes_list.clear()
        self.app.Destroy()
        
        del self.ff
        del self.app
        
        self.app = None
        self.ff = None
    
    def _draw(self):
        """绘制"""
        
        for ax in self.axes_list:
            for item in ax.assembly:
                getattr(item[0], item[1])(*item[2], **item[3])
            
            ax.reg_main.ticks3d(
                visible=self.ff.scene.ticks_is_show, 
                xlabel=ax.xn, ylabel=ax.yn, zlabel=ax.zn, 
                xr=ax.xr, yr=ax.yr, zr=ax.zr, 
                xf=ax.xf, yf=ax.yf, zf=ax.zf, 
                xd=ax.xd, yd=ax.yd, zd=ax.zd
            )
        
        self.ff.scene.update_ticks()
    
    def redraw(self):
        """重新绘制"""
        
        for reg in self.ff.scene.regions:
            reg.reset()
        
        self._draw()
    
    def show(self):
        """显示画布"""
        
        self._create_frame()
        for ax in self.axes_list:
            ax._layout() # 子图布局
        
        self._draw()
        
        if self.ff.scene.islive:
            self.ff.tb.EnableTool(self.ff.ID_PAUSE, True)
            self.ff.cb_export.Enable(True)
        
        self.ff.Show()
        self.app.MainLoop()
        
        self._destroy_frame()
    
    def savefig(self, fn):
        """保存画布为文件。fn为文件名，支持.png和.jpg格式"""
        
        fpath = os.path.split(fn)[0]
        if not os.path.isdir(fpath):
            os.makedirs(fpath)
            
        self._create_frame()
        for ax in self.axes_list:
            ax._layout() # 子图布局
        
        self._draw()
        self.ff.scene.render()
        self.ff.scene.save_scene(fn, alpha=os.path.splitext(fn)[-1]=='.png')
        self._destroy_frame()
    
    def capture(self, out_file, fps=25, loop=0, fn=50):
        """生成mp4、avi、wmv或gif文件
        
        out_file    - 输出文件名，可带路径，支持gif和mp4、avi、wmv等格式
        fps         - 每秒帧数
        loop        - 循环播放次数（仅gif格式有效，0表示无限循环）
        fn          - 总帧数
        """
        
        ext = os.path.splitext(out_file)[1].lower()
        if not ext in ('.gif', '.mp4', '.avi', 'wmv'):
            raise ValueError('不支持的文件格式：%s'%ext)
        
        folder = os.path.split(out_file)[0]
        if folder and not os.path.isdir(folder):
            raise ValueError('路径不存在：%s'%folder)
        
        self._create_frame()
        for ax in self.axes_list:
            ax._layout() # 子图布局
        
        self._draw()
        self.ff.scene.start_record(out_file, fps, loop=loop, fn=fn)
        self.ff.capture_timer.Start(100)
        self.app.MainLoop()
        self._destroy_frame()
    
    def add_axes(self, pos=111):
        """添加子图
        
        pos         - 子图在场景中的位置和大小
                        三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                        四元组      - 以画布左下角为原点，宽度和高度都是1。四元组分别表示子图左下角在画布上的水平、垂直位置和宽度、高度
        """
        
        self._create_frame()
        self.curr_ax = axes.Axes(self.ff.scene, pos)
        self.axes_list.append(self.curr_ax)
    
    def cruise(self, func_cruise):
        """设置相机巡航函数"""
        
        self._create_frame()
        self.ff.scene.set_cam_cruise(func_cruise)


class FigureFrame(wx.Frame):
    """绘图窗口主界面"""
    
    ID_CONFIG = wx.NewIdRef()   # 设置
    ID_STYLE = wx.NewIdRef()    # 风格
    ID_RESTORE = wx.NewIdRef()  # 相机复位
    ID_SAVE = wx.NewIdRef()     # 保存
    ID_PAUSE = wx.NewIdRef()    # 动态显示
    ID_GRID = wx.NewIdRef()     # 网格
    
    id_white = wx.NewIdRef()    # 珍珠白
    id_black = wx.NewIdRef()    # 石墨黑
    id_gray = wx.NewIdRef()     # 国际灰
    id_blue = wx.NewIdRef()     # 太空蓝
    id_royal = wx.NewIdRef()    # 宝石蓝
    
    def __init__(self, fig):
        """构造函数"""
        
        wx.Frame.__init__(self, None, -1, 'wxPlot', style=wx.DEFAULT_FRAME_STYLE|wx.TRANSPARENT_WINDOW)
        
        self.fig = fig
        self.SetIcon(wx.Icon(os.path.join(BASE_PATH, 'res', 'wxplot.ico')))
        self.SetSize(self.fig.size)
        self.Center()
        
        self.scene = scene.Scene(self, **self.fig.kwds3d)
        
        self.gauge = None                                   # 保存文件的进度条窗口
        self.export = False                                 # 播放动画时生成GIF或视频文件
        self.ext = '.gif'                                   # 输出文件格式
        
        bmp_config = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_config_32.png'), wx.BITMAP_TYPE_ANY)
        bmp_style = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_style_32.png'), wx.BITMAP_TYPE_ANY)
        bmp_restore = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_restore_32.png'), wx.BITMAP_TYPE_ANY)
        bmp_save = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_save_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_play = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_play_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_stop = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_stop_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_show = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_show_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_hide = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_hide_32.png'), wx.BITMAP_TYPE_ANY)
        
        self.tb = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, agwStyle=aui.AUI_TB_DEFAULT_STYLE|aui.AUI_TB_OVERFLOW)
        self.tb.SetToolBitmapSize(wx.Size(32, 32))
        
        self.tb.AddSimpleTool(self.ID_CONFIG, '设置', bmp_config, '设置系统参数')
        self.tb.AddSimpleTool(self.ID_STYLE, '风格', bmp_style, '选择画布风格')
        self.tb.AddSeparator()
        self.tb.AddSimpleTool(self.ID_RESTORE, '复位', bmp_restore, '模型初始位置')
        self.tb.AddSimpleTool(self.ID_SAVE, '保存', bmp_save, '保存为文件')
        self.tb.AddSeparator()
        self.tb.AddSimpleTool(self.ID_GRID, '网格', self.bmp_show, '显示网格', kind=aui.ITEM_CHECK)
        self.tb.AddSimpleTool(self.ID_PAUSE, '动画', self.bmp_play, '播放动画', kind=aui.ITEM_CHECK)
        
        self.cb_export = wx.CheckBox(self.tb, -1, '屏幕录制')
        self.cb_export.SetBackgroundColour(wx.Colour(218,218,218))
        self.cb_export.SetValue(self.export)
        self.cb_export.Bind(wx.EVT_CHECKBOX, self.on_export)
        self.tb.AddControl(self.cb_export)
        
        self.tb.EnableTool(self.ID_PAUSE, False)
        self.cb_export.Enable(False)
        self.tb.Realize()
        
        self._mgr = aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        self._mgr.AddPane(self.scene, aui.AuiPaneInfo().Name('Scene').CenterPane().Show())
        self._mgr.AddPane(self.tb, aui.AuiPaneInfo().Name('ToolBar').ToolbarPane().Bottom().Floatable(False))
        self._mgr.Update()
        
        self.Bind(wx.EVT_MENU, self.on_config, id=self.ID_CONFIG)
        self.Bind(wx.EVT_MENU, self.on_style, id=self.ID_STYLE)
        self.Bind(wx.EVT_MENU, self.on_restore, id=self.ID_RESTORE)
        self.Bind(wx.EVT_MENU, self.on_ticks, id=self.ID_GRID)
        self.Bind(wx.EVT_MENU, self.on_save, id=self.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_pause, id=self.ID_PAUSE)
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_white)
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_black)
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_gray)
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_blue)
        self.Bind(wx.EVT_MENU, self.on_color, id=self.id_royal)
        
        self.recording_timer = wx.Timer() # 录屏操作定时器
        self.capture_timer = wx.Timer() # 离线录屏定时器
        self.recording_timer.Bind(wx.EVT_TIMER, self.after_stop_record)
        self.capture_timer.Bind(wx.EVT_TIMER, self.on_capture)
        
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
    def on_close(self, evt):
        """窗口关闭事件函数"""
        
        if self.scene.playing:
            self.scene.playing = False
            wx.CallLater(100, self.on_close, None)
        else:
            self.Destroy()
    
    def on_capture(self, evt):
        """离线录屏定时器函数"""
        
        if not self.scene.capturing and not self.scene.creating:
            self.capture_timer.Stop()
            self.Close()
    
    def on_export(self, evt):
        """录屏开关"""
        
        self.export = self.cb_export.GetValue()
    
    def on_color(self, evt):
        """选择风格"""
        
        idx = evt.GetId()
        if idx == self.id_black.Id:
            self.fig.style = 'black'
            self.fig.kwds3d.update({'style':self.fig.style})
        elif idx == self.id_gray.Id:
            self.fig.style = 'gray'
            self.fig.kwds3d.update({'style':self.fig.style})
        elif idx == self.id_blue.Id:
            self.fig.style = 'blue'
            self.fig.kwds3d.update({'style':self.fig.style})
        elif idx == self.id_white.Id:
            self.fig.style = 'white'
            self.fig.kwds3d.update({'style':self.fig.style})
        else:
            self.fig.style = 'royal'
            self.fig.kwds3d.update({'style':self.fig.style})
        
        self.fig.cfg.set('custom', 'style', self.fig.style)
        with open(self.fig.fn_cfg, 'w') as fp:
            self.fig.cfg.write(fp)
        
        self.scene.set_style(self.fig.style)
        self.fig.redraw()
    
    def on_config(self, evt):
        """参数设置"""
        
        def on_dir(evt):
            dlg = wx.DirDialog(self, "选择保存路径", defaultPath=self.fig.folder, style=wx.DD_DEFAULT_STYLE)
            if dlg.ShowModal() == wx.ID_OK:
                self.fig.folder = dlg.GetPath()
                tc_dir.SetValue(self.fig.folder)
                
                self.fig.cfg.set('custom', 'folder', self.fig.folder)
                with open(self.fig.fn_cfg, 'w') as fp:
                    self.fig.cfg.write(fp)
            
            dlg.Destroy()
        
        def on_text(evt):
            s = evt.GetString()
            if not s.isdigit():
                wx.MessageBox('该输入框仅接受数字输入！', '操作提示')
                if s:
                    evt.GetEventObject().SetValue(s[:-1])
                else:
                    evt.GetEventObject().SetValue('0')
        
        dlg = wx.Dialog(self, size=(640, 330), title='参数设置')
        dlg.CenterOnScreen()
        
        wx.StaticBox(dlg, -1, 'GIF/视频设置', pos=(20,90), size=(300,135))
        
        wx.StaticText(dlg, -1, '文件格式：', pos=(40,117), size=(80,-1), style=wx.ALIGN_RIGHT)
        rb_gif = wx.RadioButton(dlg, id=-1, label='.gif', pos=(120,115), size=(55,20), style=wx.RB_GROUP)
        rb_avi = wx.RadioButton(dlg, id=-1, label='.avi', pos=(175,115), size=(55,20))
        rb_mp4 = wx.RadioButton(dlg, id=-1, label='.mp4', pos=(230,115), size=(55,20))
        
        if self.fig.ext == '.gif':
            rb_gif.SetValue(True)
        elif self.fig.ext == '.avi':
            rb_avi.SetValue(True)
        else:
            rb_mp4.SetValue(True)
        
        wx.StaticText(dlg, -1, '帧率：', pos=(40,142), size=(80,-1), style=wx.ALIGN_RIGHT)
        tc_fps = wx.TextCtrl(dlg, -1, value='%d'%self.fig.fps, pos=(120,140), size=(60,20), style=wx.TE_CENTRE)
        wx.StaticText(dlg, -1, ' f/s', pos=(180,140))
        tc_fps.Bind(wx.EVT_TEXT, on_text)
        
        wx.StaticText(dlg, -1, '总帧数：', pos=(40,167), size=(80,-1), style=wx.ALIGN_RIGHT)
        tc_fn = wx.TextCtrl(dlg, -1, value='%d'%self.fig.fn, pos=(120,165), size=(60,20), style=wx.TE_CENTRE)
        tc_fn.Bind(wx.EVT_TEXT, on_text)
        
        wx.StaticText(dlg, -1, '循环播放：', pos=(40,192), size=(80,-1), style=wx.ALIGN_RIGHT)
        cb_loop = wx.CheckBox(dlg, -1, '（仅gif格式有效）', pos=(120,190))
        cb_loop.SetValue(self.fig.loop==0)
        
        wx.StaticBox(dlg, -1, '文件保存路径', pos=(20,20), size=(300,60))
        
        tc_dir = wx.TextCtrl(dlg, -1, value='%s'%self.fig.folder, pos=(40,45), size=(215,20))
        btn_dir = wx.Button(dlg, -1, '浏览', pos=(260,45), size=(40,20))
        btn_dir.Bind(wx.EVT_BUTTON, on_dir)
        
        info = wx.Panel(dlg, -1, pos=(350,25), size=(250,235), style=wx.BORDER_SUNKEN)
        info.SetBackgroundColour(wx.Colour(192, 255, 255))
        
        wx.StaticText(info, -1, '投影方式：', pos=(20,15), size=(80,-1), style=wx.ALIGN_RIGHT)
        wx.StaticText(info, -1, '透视投影' if self.scene.proj == 'frustum' else '正射投影', pos=(100,15))
        
        wx.StaticText(info, -1, 'ECS原点：', pos=(20,38), size=(80,-1), style=wx.ALIGN_RIGHT)
        wx.StaticText(info, -1, '[%.3f, %.3f, %.3f]'%(*self.scene.oecs,), pos=(100,38))
        
        wx.StaticText(info, -1, '相机位置：', pos=(20,61), size=(80,-1), style=wx.ALIGN_RIGHT)
        wx.StaticText(info, -1, '[%.3f, %.3f, %.3f]'%(*self.scene.cam,), pos=(100,61))
        
        wx.StaticText(info, -1, 'UP向量：', pos=(20,84), size=(80,-1), style=wx.ALIGN_RIGHT)
        wx.StaticText(info, -1, '[%.1f, %.1f, %.1f]'%(*self.scene.up,), pos=(100,84))
        
        wx.StaticText(info, -1, '视锥体近端：', pos=(20,107), size=(80,-1), style=wx.ALIGN_RIGHT)
        wx.StaticText(info, -1, '%.3f'%self.scene.near, pos=(100,107))
        
        wx.StaticText(info, -1, '视锥体远端：', pos=(20,130), size=(80,-1), style=wx.ALIGN_RIGHT)
        wx.StaticText(info, -1, '%.3f'%self.scene.far, pos=(100,130))
        
        wx.StaticText(info, -1, '方位角：', pos=(20,153), size=(80,-1), style=wx.ALIGN_RIGHT)
        wx.StaticText(info, -1, '%.3f°'%self.scene.azim, pos=(100,153))
        
        wx.StaticText(info, -1, '高度角：', pos=(20,176), size=(80,-1), style=wx.ALIGN_RIGHT)
        wx.StaticText(info, -1, '%.3f°'%self.scene.elev, pos=(100,176))
        
        wx.StaticText(info, -1, '距离：', pos=(20,199), size=(80,-1), style=wx.ALIGN_RIGHT)
        wx.StaticText(info, -1, '%.3f'%self.scene.dist, pos=(100,199))
        
        btn_cancel = wxbtn.GenButton(dlg, wx.ID_CANCEL, '取消', pos=(100,240), size=(60,-1))
        btn_cancel.SetBezelWidth(2)
        btn_cancel.SetBackgroundColour(wx.Colour(217,228,241))
        
        btn_ok = wxbtn.GenButton(dlg, wx.ID_OK, '确定', pos=(200,240), size=(60,-1))
        btn_ok.SetBezelWidth(2)
        btn_ok.SetBackgroundColour(wx.Colour(245,227,129))
        
        if dlg.ShowModal() == wx.ID_OK:
            if rb_avi.GetValue():
                self.fig.ext = '.avi'
            if rb_mp4.GetValue():
                self.fig.ext = '.mp4'
            else:
                self.fig.ext = '.gif'
            
            self.fig.fps = int(tc_fps.GetValue())
            self.fig.fn = int(tc_fn.GetValue())
            self.fig.loop = 1 - int(cb_loop.GetValue())
            
            self.fig.cfg.set('custom', 'ext', self.fig.ext)
            self.fig.cfg.set('custom', 'fps', str(self.fig.fps))
            self.fig.cfg.set('custom', 'fn', str(self.fig.fn))
            self.fig.cfg.set('custom', 'loop', str(self.fig.loop))
            
            with open(self.fig.fn_cfg, 'w') as fp:
                self.fig.cfg.write(fp)
    
    def on_style(self, evt):
        """背景颜色"""
        
        tb = evt.GetEventObject()
        tb.SetToolSticky(evt.GetId(), True)
        
        submenu = wx.Menu()
        
        m1 =  wx.MenuItem(submenu, self.id_blue, '太空蓝', kind=wx.ITEM_RADIO)
        submenu.Append(m1)
        if self.fig.style == 'blue':
            m1.Check(True)
        
        m2 =  wx.MenuItem(submenu, self.id_black, '石墨黑', kind=wx.ITEM_RADIO)
        submenu.Append(m2)
        if self.fig.style == 'black':
            m2.Check(True)
        
        m3 =  wx.MenuItem(submenu, self.id_white, '珍珠白', kind=wx.ITEM_RADIO)
        submenu.Append(m3)
        if self.fig.style == 'white':
            m3.Check(True)
        
        m4 =  wx.MenuItem(submenu, self.id_gray, '国际灰', kind=wx.ITEM_RADIO)
        submenu.Append(m4)
        if self.fig.style == 'gray':
            m4.Check(True)
        
        m5 =  wx.MenuItem(submenu, self.id_royal, '宝石蓝', kind=wx.ITEM_RADIO)
        submenu.Append(m5)
        if self.fig.style == 'royal':
            m5.Check(True)
        
        self.PopupMenu(submenu)
        tb.SetToolSticky(evt.GetId(), False)
    
    def on_restore(self, evt):
        """回到初始状态"""
        
        self.scene.restore_posture()
    
    def on_ticks(self, evt):
        """显示/隐藏坐标轴及刻度网格"""
        
        self.scene.ticks_is_show = not self.scene.ticks_is_show
        if self.scene.ticks_is_show:
            self.tb.SetToolBitmap(self.ID_GRID, self.bmp_hide)
            self.tb.SetToolShortHelp(self.ID_GRID, '隐藏网格')
        else:
            self.tb.SetToolBitmap(self.ID_GRID, self.bmp_show)
            self.tb.SetToolShortHelp(self.ID_GRID, '显示网格')
        self.tb.Realize()
        
        for ax in self.fig.axes_list:
            for key in ax.reg_main.ticks:
                ax.reg_main.set_model_visible(ax.reg_main.ticks[key], self.scene.ticks_is_show)
        
        self.scene.update_ticks()
        self.scene.render()
    
    def on_pause(self, evt):
        """暂停/启动"""
        
        if self.scene.playing:
            if self.export:
                self.scene.stop_record()
            else:
                self.tb.SetToolBitmap(self.ID_PAUSE, self.bmp_play)
                self.tb.SetToolShortHelp(self.ID_PAUSE, '播放动画')
                self.scene.stop_animate()
        else:
            self.tb.SetToolBitmap(self.ID_PAUSE, self.bmp_stop)
            self.tb.SetToolShortHelp(self.ID_PAUSE, '停止动画')
            
            if self.export:
                out_file = os.path.join(self.fig.folder, '%s%s'%(time.strftime('%Y%m%d_%H%M%S'), self.fig.ext))
                self.scene.start_record(out_file, self.fig.fps, loop=self.fig.loop, fn=self.fig.fn)
                self.recording_timer.Start(50)
            else:
                self.scene.start_animate()
        
        self.tb.Realize()
    
    def on_save(self, evt):
        """保存为文件"""
        
        wildcard = 'PNG files (*.png)|*.png|JPEG file (*.jpg)|*.jpg'
        dlg = wx.FileDialog(self, message='保存为文件', defaultDir=self.fig.folder, defaultFile="", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        dlg.SetFilterIndex(0)
        
        if dlg.ShowModal() == wx.ID_OK:
            fn = dlg.GetPath()
            self.fig.folder = os.path.split(fn)[0]
            
            self.fig.cfg.set('custom', 'folder', self.fig.folder)
            with open(self.fig.fn_cfg, 'w') as fp:
                self.fig.cfg.write(fp)
            
            alpha = os.path.splitext(fn)[-1] == '.png'
            self.scene.save_scene(fn, alpha=alpha)
        
        dlg.Destroy()
    
    def after_stop_record(self, evt):
        """自动或手动停止录屏后的操作"""
        
        if not self.scene.capturing:
            if self.scene.creating:
                self.tb.SetToolBitmap(self.ID_PAUSE, self.bmp_play)
                self.tb.SetToolShortHelp(self.ID_PAUSE, '播放动画')
                self.tb.ToggleTool(self.ID_PAUSE, False)
                self.tb.Realize()
                self.export = False
                self.cb_export.SetValue(self.export)
            
                if self.gauge is None:
                    self.gauge = ProcessDialog(self, '正在保存文件，请稍候...')
                    self.gauge.ShowModal()
            else:
                self.recording_timer.Stop()
                if not self.gauge is None:
                    self.gauge.EndModal(wx.ID_OK)
                    self.gauge = None
                
                if PLAT_FORM == 'Windows':
                    os.system("explorer %s" % self.fig.folder)
                else:
                    wx.MessageBox('文件已保存至：%s' % self.fig.folder, '操作提示')
        

class ProcessDialog(wx.Dialog):
    """显示进度对话框"""

    def __init__(self, parent, msg):
        """构造函数"""

        wx.Dialog.__init__(self, parent, -1, size=(300, 100), style=wx.NO_BORDER)
        
        # 初始化变量
        self.parent = parent
        self.start_sec = int(time.time())

        # 初始化界面
        sizer = wx.BoxSizer()
        grid = wx.GridBagSizer(10, 10)

        text = wx.StaticText(self, -1, msg)
        grid.Add(text, (0, 0), flag=wx.ALIGN_CENTER)

        self.gauge = wx.Gauge(self, -1)
        grid.Add(self.gauge, (1, 0), flag=wx.EXPAND)

        self.clock = wx.StaticText(self, -1, "00:00:00")
        grid.Add(self.clock, (2, 0), flag=wx.ALIGN_CENTER)

        grid.AddGrowableCol(0)
        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(sizer)
        self.Layout()

        self.CenterOnScreen()

        # 启动定时器
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.timer.Start(1000)

    def on_timer(self, evt):
        """定时器事件处理"""

        self.gauge.Pulse()
        delta = int(time.time()) - self.start_sec

        # 将秒转化为时间字符串
        hour = delta // 3600
        minute = (delta % 3600) // 60
        second = delta % 60
        self.clock.SetLabel("%02d:%02d:%02d"%(hour, minute, second))

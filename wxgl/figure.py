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
            if key not in ['size', 'proj', 'oecs', 'dist', 'azim', 'elev', 'vision', 'near', 'far', 'zoom', 'interval', 'smooth', 'azim_range', 'elev_range', 'style']:
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
            elev        - 仰角，默认0°
            vision      - 视锥体左右上下四个面距离ECS原点的距离，默认1个长度单位
            near        - 视锥体前面距离相机的距离，默认2.6个长度单位
            far         - 视锥体后面距离相机的距离，默认1000个长度单位
            zoom        - 视口缩放因子，默认1.0
            interval    - 动画定时间隔，默认20毫秒
            smooth      - 直线、多边形和点的反走样开关
            azim_range  - 方位角限位器，默认-90°~90°
            elev_range  - 仰角限位器，默认-90°~90°
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
        else:
            self.cfg.add_section('custom')
            if self.style:
                self.cfg.set('custom', 'style', self.style)
            else:
                self.style = 'blue'
                self.cfg.set('custom', 'style', self.style)
                self.kwds3d.update({'style':self.style})
            self.cfg.set('custom', 'folder', self.folder)
        
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
        
        #try:
        self._draw()
        if self.ff.scene.islive:
            self.ff.tb.EnableTool(self.ff.ID_PAUSE, True)
            self.ff.cb_export.Enable(True)
        self.ff.Show()
        self.app.MainLoop()
        #except Exception as e:
        #    print('画布显示异常，请通知xufive@gmail.com，并附上如下信息：\n%s'%str(e))
        #finally:
        self._destroy_frame()
    
    def savefig(self, fn):
        """保存画布为文件。fn为文件名，支持.png和.jpg格式"""
        
        fpath = os.path.split(fn)[0]
        if not os.path.isdir(fpath):
            os.makedirs(fpath)
            
        self._create_frame()
        for ax in self.axes_list:
            ax._layout() # 子图布局
        
        try: 
            self._draw()
            self.ff.scene.render()
            self.ff.scene.save_scene(fn, alpha=os.path.splitext(fn)[-1]=='.png')
        except Exception as e:
            print('画布显示异常，请通知xufive@gmail.com，并附上如下信息：\n%s'%str(e))
        finally:
            self._destroy_frame()
    
    def capture(self, out_file, fps=25, loop=0, fn=50):
        """生成mp4或gif文件
        
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
        
        try:
            self._draw()
            self.ff.scene.start_record(out_file, fps, loop=loop, fn=fn, callback=self.ff.scene.stop_animate)
            self.ff.capture_timer.Start(100)
            self.app.MainLoop()
        except Exception as e:
            print('画布显示异常，请通知xufive@gmail.com，并附上如下信息：\n%s'%str(e))
        finally:
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
        
        self.export = False                                 # 播放动画时生成GIF或视频文件
        self.ext = '.gif'                                   # 输出文件格式
        self.fps = 25                                       # 输出GIF或视频的帧率
        self.loop = 0                                       # GIF循环次数
        self.fn = 50                                        # 输出文件总帧数
        
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
        
        sb = wx.StaticBitmap(self.tb, -1, wx.Bitmap(os.path.join(BASE_PATH, 'res', 'info.png'), wx.BITMAP_TYPE_ANY))
        sb.Bind(wx.EVT_LEFT_UP, self.on_info)
        self.tb.AddControl(sb)
        
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
        
        self.capture_timer = wx.Timer() # 离线录屏定时器
        self.capture_timer.Bind(wx.EVT_TIMER, self.on_capture)
    
    def on_capture(self, evt):
        """离线录屏定时器函数"""
        
        if not self.scene.recording:
            self.capture_timer.Stop()
            #self.scene.threading_record.join()
            #self.fig._destroy_frame()
            #self.Destroy()
            self.Close()
    
    def on_export(self, evt):
        """录屏开关"""
        
        self.export = self.cb_export.GetValue()
    
    def on_info(self, evt):
        """关于录屏的说明"""
        
        wx.MessageBox('录屏时渲染频率降低90%，录屏结束后自动恢复。', '操作提示')
    
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
        
        dlg = wx.Dialog(self, size=(640, 370), title='参数设置')
        dlg.CenterOnScreen()
        
        wx.StaticBox(dlg, -1, '系统参数', pos=(20,20), size=(300,110))
        
        wx.StaticText(dlg, -1, '方位角限位：', pos=(40,47), size=(80,-1), style=wx.ALIGN_RIGHT)
        tc_azim_0 = wx.TextCtrl(dlg, -1, value='%d'%self.scene.azim_range[0], pos=(120,45), size=(60,20), style=wx.TE_CENTRE)
        wx.StaticText(dlg, -1, ' ° ~ ', pos=(180,45), size=(25,-1))
        tc_azim_1 = wx.TextCtrl(dlg, -1, value='%d'%self.scene.azim_range[1], pos=(205,45), size=(60,20), style=wx.TE_CENTRE)
        wx.StaticText(dlg, -1, ' °', pos=(265,45))
        tc_azim_0.Bind(wx.EVT_TEXT, on_text)
        tc_azim_0.Bind(wx.EVT_TEXT, on_text)
        
        wx.StaticText(dlg, -1, '仰角限位：', pos=(40,72), size=(80,-1), style=wx.ALIGN_RIGHT)
        tc_elev_0 = wx.TextCtrl(dlg, -1, value='%d'%self.scene.elev_range[0], pos=(120,70), size=(60,20), style=wx.TE_CENTRE)
        wx.StaticText(dlg, -1, ' ° ~ ', pos=(180,70), size=(25,-1))
        tc_elev_1 = wx.TextCtrl(dlg, -1, value='%d'%self.scene.elev_range[1], pos=(205,70), size=(60,20), style=wx.TE_CENTRE)
        wx.StaticText(dlg, -1, ' °', pos=(265,70))
        tc_elev_0.Bind(wx.EVT_TEXT, on_text)
        tc_elev_0.Bind(wx.EVT_TEXT, on_text)
        
        wx.StaticText(dlg, -1, '定时器间隔：', pos=(40,97), size=(80,-1), style=wx.ALIGN_RIGHT)
        tc_interval = wx.TextCtrl(dlg, -1, value='%d'%self.scene.interval, pos=(120,95), size=(60,20), style=wx.TE_CENTRE)
        wx.StaticText(dlg, -1, ' ms', pos=(180,97))
        tc_interval.Bind(wx.EVT_TEXT, on_text)
        
        wx.StaticBox(dlg, -1, 'GIF/视频', pos=(20,140), size=(300,160))
        
        wx.StaticText(dlg, -1, '保存路径：', pos=(40,167), size=(80,-1), style=wx.ALIGN_RIGHT)
        tc_dir = wx.TextCtrl(dlg, -1, value='%s'%self.fig.folder, pos=(120,165), size=(140,20))
        btn_dir = wx.Button(dlg, -1, '浏览', pos=(265,165), size=(40,20))
        btn_dir.Bind(wx.EVT_BUTTON, on_dir)
        
        wx.StaticText(dlg, -1, '文件格式：', pos=(40,192), size=(80,-1), style=wx.ALIGN_RIGHT)
        rb_gif = wx.RadioButton(dlg, id=-1, label='.gif', pos=(120,190), size=(55,20), style=wx.RB_GROUP)
        rb_avi = wx.RadioButton(dlg, id=-1, label='.avi', pos=(175,190), size=(55,20))
        rb_mp4 = wx.RadioButton(dlg, id=-1, label='.mp4', pos=(230,190), size=(55,20))
        
        wx.StaticText(dlg, -1, '帧率：', pos=(40,217), size=(80,-1), style=wx.ALIGN_RIGHT)
        tc_fps = wx.TextCtrl(dlg, -1, value='%d'%self.fps, pos=(120,215), size=(60,20), style=wx.TE_CENTRE)
        wx.StaticText(dlg, -1, ' f/s', pos=(180,217))
        tc_fps.Bind(wx.EVT_TEXT, on_text)
        
        wx.StaticText(dlg, -1, '最大帧数：', pos=(40,242), size=(80,-1), style=wx.ALIGN_RIGHT)
        tc_fn = wx.TextCtrl(dlg, -1, value='%d'%self.fn, pos=(120,240), size=(60,20), style=wx.TE_CENTRE)
        tc_fn.Bind(wx.EVT_TEXT, on_text)
        
        cb_loop = wx.CheckBox(dlg, -1, '循环播放（仅gif格式有效）', pos=(60,267))
        cb_loop.SetValue(self.loop==0)
        
        info = wx.Panel(dlg, -1, pos=(350,25), size=(250,230), style=wx.BORDER_SUNKEN)
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
        
        wx.StaticText(info, -1, '仰角：', pos=(20,176), size=(80,-1), style=wx.ALIGN_RIGHT)
        wx.StaticText(info, -1, '%.3f°'%self.scene.elev, pos=(100,176))
        
        wx.StaticText(info, -1, '距离：', pos=(20,199), size=(80,-1), style=wx.ALIGN_RIGHT)
        wx.StaticText(info, -1, '%.3f'%self.scene.dist, pos=(100,199))
        
        btn_cancel = wxbtn.GenButton(dlg, wx.ID_CANCEL, '取消', pos=(400,275), size=(60,-1))
        btn_cancel.SetBezelWidth(2)
        btn_cancel.SetBackgroundColour(wx.Colour(217,228,241))
        
        btn_ok = wxbtn.GenButton(dlg, wx.ID_OK, '确定', pos=(500,275), size=(60,-1))
        btn_ok.SetBezelWidth(2)
        btn_ok.SetBackgroundColour(wx.Colour(245,227,129))
        
        if dlg.ShowModal() == wx.ID_OK:
            self.scene.azim_range = int(tc_azim_0.GetValue()), int(tc_azim_1.GetValue())
            self.scene.elev_range = int(tc_elev_0.GetValue()), int(tc_elev_1.GetValue())
            self.scene.interval = int(tc_interval.GetValue())
            
            if rb_avi.GetValue():
                self.ext = '.avi'
            if rb_mp4.GetValue():
                self.ext = '.mp4'
            else:
                self.ext = '.gif'
            
            self.fps = int(tc_fps.GetValue())
            self.fn = int(tc_fn.GetValue())
            self.loop = 1 - int(cb_loop.GetValue())
    
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
        
        self.click_stop()
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
        
        if self.scene.timer.IsRunning():
            self.scene.stop_animate()
            self.tb.SetToolBitmap(self.ID_PAUSE, self.bmp_play)
            self.tb.SetToolShortHelp(self.ID_PAUSE, '播放动画')
            if self.export:
                self.scene.recording = False
                self.export = False
                self.cb_export.SetValue(self.export)
                
                if PLAT_FORM == 'Windows':
                    os.system("explorer %s" % self.fig.folder)
                else:
                    wx.MessageBox('文件已保存至：%s' % self.fig.folder, '操作提示')
        else:
            self.tb.SetToolBitmap(self.ID_PAUSE, self.bmp_stop)
            self.tb.SetToolShortHelp(self.ID_PAUSE, '停止动画')
            if self.export:
                out_file = os.path.join(self.fig.folder, '%s%s'%(time.strftime('%Y%m%d_%H%M%S'), self.ext))
                self.scene.start_record(out_file, self.fps, loop=self.loop, fn=self.fn, callback=self.click_stop)
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
    
    def click_stop(self):
        """模拟停止录屏"""
        
        if self.scene.timer.IsRunning():
            self.on_pause(None)
            self.tb.ToggleTool(self.ID_PAUSE, False)

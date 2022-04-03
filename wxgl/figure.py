# -*- coding: utf-8 -*-

import os, time
import platform
import wx
import wx.lib.agw.aui as aui
import wx.lib.buttons as wxbtn
import configparser

from . scene import Scene
from . axes import Axes


BASE_PATH = os.path.dirname(__file__)
PLAT_FORM = platform.system()

def single_figure(cls):
    """画布类单实例模式装饰器"""
    
    _instance = {}

    def _single_figure(**kwds):
        for key in kwds:
            if key not in ['size', 'smooth', 'style', 'proj', 'zoom', 'azim', 'elev', 'azim_range', 'elev_range']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        if cls not in _instance:
            size = kwds.pop('size') if 'size' in kwds else (1152,648)
            smooth = kwds.pop('smooth') if 'smooth' in kwds else True
            style = kwds.pop('style') if 'style' in kwds else None
            
            _instance[cls] = cls(size, smooth, style, **kwds)
        else:
            if 'size' in kwds:
                _instance[cls].size = kwds.pop('size')
            if 'smooth' in kwds:
                _instance[cls].size = kwds.pop('smooth')
            if 'style' in kwds:
                _instance[cls].style = kwds.pop('style')
            
            _instance[cls].args.update(kwds)
            
        
        return _instance[cls]

    return _single_figure


@single_figure
class Figure:
    """画布类"""
    
    def __init__(self, size, smooth, style, **kwds): 
        """构造函数
        
        size        - 窗口分辨率
        smooth      - 直线、多边形和点的反走样开关
        style       - 画布风格：'blue' | 'gray' | 'white' | 'black' | 'royal'
        kwds        - 关键字参数
            proj        - 投影模式：'O' - 正射投影，'P' - 透视投影（默认）
            zoom        - 视口缩放因子：默认1.0
            azim        - 方位角：-180°~180°范围内的浮点数，默认0°
            elev        - 高度角：-180°~180°范围内的浮点数，默认0°
            azim_range  - 方位角限位器：默认-180°~180°
            elev_range  - 仰角限位器：默认-180°~180°:
        """
        
        self.size = size                            # 画布大小
        self.smooth = smooth                        # 反走样开关
        self.style = style                          # 画布风格
        self.args = kwds                            # Axes主视区相机参数
        
        self.folder = os.getcwd()                   # 保存路径
        self.ext = None                             # 输出文件格式
        self.fps = 25                               # 输出GIF或视频的帧率
        self.loop = 0                               # 循环次数（仅GIF有效）
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
            else:
                self.style = 'blue'
                self.cfg.set('custom', 'style', self.style)
            
            if self.cfg.has_option('custom', 'folder'):
                self.folder = self.cfg.get('custom', 'folder')
            else:
                self.cfg.set('custom', 'folder', self.folder)
            
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
            
            self.cfg.set('custom', 'style', self.style)
            self.cfg.set('custom', 'folder', self.folder)
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
        self.args.clear()
    
    def _draw(self):
        """绘制"""
        
        for ax in self.axes_list:
            for item in ax.assembly:
                getattr(item[0], item[1])(*item[2], **item[3])
    
    def redraw(self):
        """重新绘制"""
        
        for reg in self.ff.scene.regions:
            reg.clear()
        
        self._draw()
    
    def show(self):
        """显示画布"""
        
        self._create_frame()
        for ax in self.axes_list:
            ax._layout() # 子图布局
        
        self._draw()
        
        if self.ff.scene.islive:
            self.ff.tb.EnableTool(self.ff.ID_ANIMATE, True)
        
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
    
    def capture(self, out_file, fps=25, fn=50, loop=0):
        """生成mp4、avi、wmv或gif文件
        
        out_file    - 输出文件名，可带路径，支持gif和mp4、avi、wmv等格式
        fps         - 每秒帧数
        fn          - 总帧数
        loop        - 循环播放次数（仅gif格式有效，0表示无限循环）
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
        self.ff.scene.start_record(out_file, fps, fn, loop)
        self.ff.capture_timer.Start(100)
        self.app.MainLoop()
        self._destroy_frame()
    
    def add_axes(self, pos, **kwds):
        """添加子图
        
        pos         - 子图在场景中的位置和大小
                        三位数字    - 指定分割画布的行数、列数和子图序号。例如，223表示两行两列的第3个位置
                        四元组      - 以画布左下角为原点，宽度和高度都是1。四元组分别表示子图左下角在画布上的水平、垂直位置和宽度、高度
        kwds        - 关键字参数
            azim        - 方位角：-180°~180°范围内的浮点数，默认0°
            elev        - 高度角：-180°~180°范围内的浮点数，默认0°
            azim_range  - 方位角限位器：默认-180°~180°
            elev_range  - 仰角限位器：默认-180°~180°
            zoom        - 视口缩放因子：默认1.0
        """
        
        self._create_frame()
        self.curr_ax = Axes(self.ff.scene, pos, **kwds)
        self.axes_list.append(self.curr_ax)

class GltScene(Scene):
    """重写Scene的鼠标左键函数"""
        
    def _on_left_down(self, evt):
        """响应鼠标左键按下事件"""
        
        self.leftdown = True
        self.mpos = evt.GetPosition()
        self.parent.sb.SetStatusText('', 1)
        
    def _on_left_up(self, evt):
        """响应鼠标左键弹起事件"""
        
        self.leftdown = False
        if self.parent.curr_reg:
            azim = self.parent.curr_reg.azim
            elev = self.parent.curr_reg.elev
            oecs = self.parent.curr_reg.oecs
            dist = self.parent.curr_reg.dist
            cam = self.parent.curr_reg.cam
            msg = '方位角：%0.2f°，高度角：%0.2f°，视点坐标：(%0.2f,%0.2f,%0.2f)，相机位置：(%0.2f,%0.2f,%0.2f)' % (azim, elev, *oecs, *cam)
            self.parent.sb.SetStatusText(msg, 1)
        
    def _on_mouse_motion(self, evt):
        """响应鼠标移动事件"""
        
        if evt.Dragging() and self.leftdown:
            pos = evt.GetPosition()
            dx, dy = pos - self.mpos
            self.mpos = pos
            
            for reg in self.regions:
                reg._motion(self.ctr, dx, dy)
            
            self.render()
        else:
            x, y = evt.GetPosition()
            y = self.csize[1] - y
            
            erase = True
            for reg in self.regions:
                if not reg.fixed and reg.pos[0] < x < (reg.pos[0]+reg.size[0]) and reg.pos[1] < y < (reg.pos[1]+reg.size[1]):
                    erase = False
                    if not reg is self.parent.curr_reg:
                        self.parent.curr_reg = reg
                        msg = '方位角：%0.2f°，高度角：%0.2f°，视点坐标：(%0.2f,%0.2f,%0.2f)，相机位置：(%0.2f,%0.2f,%0.2f)' % (reg.azim, reg.elev, *reg.oecs, *reg.cam)
                        self.parent.sb.SetStatusText(msg, 1)
                        break
            
            if erase:
                self.parent.sb.SetStatusText('', 1)
                self.parent.curr_reg = None
        
    def _on_right_up(self, evt):
        """响应鼠标右键弹起事件"""
        
        x, y = evt.GetPosition()
        self._render_pick(x, self.csize[1]-y)
        
        self.parent.update_select()

class FigureFrame(wx.Frame):
    """绘图窗口主界面"""
    
    ID_CONFIG = wx.NewIdRef()   # 设置
    ID_STYLE = wx.NewIdRef()    # 风格
    ID_RESTORE = wx.NewIdRef()  # 相机复位
    ID_SAVE = wx.NewIdRef()     # 保存
    ID_ANIMATE = wx.NewIdRef()  # 动态显示
    ID_SELECT = wx.NewIdRef()   # 网格
    
    id_white = wx.NewIdRef()    # 珍珠白
    id_black = wx.NewIdRef()    # 石墨黑
    id_gray = wx.NewIdRef()     # 国际灰
    id_blue = wx.NewIdRef()     # 太空蓝
    id_royal = wx.NewIdRef()    # 宝石蓝
    
    def __init__(self, fig):
        """构造函数"""
        
        wx.Frame.__init__(self, None, -1, '3d Plot Tool Kits', style=wx.DEFAULT_FRAME_STYLE|wx.TRANSPARENT_WINDOW)
        
        self.fig = fig
        self.SetIcon(wx.Icon(os.path.join(BASE_PATH, 'res', 'wxplot.ico')))
        self.SetSize(self.fig.size)
        self.Center()
        
        self.scene = GltScene(self, smooth=self.fig.smooth, style=self.fig.style)
        self.gauge = None
        self.curr_reg = None # 当前鼠标所在的视区
        
        bmp_config = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_config_32.png'), wx.BITMAP_TYPE_ANY)
        bmp_style = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_style_32.png'), wx.BITMAP_TYPE_ANY)
        bmp_restore = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_restore_32.png'), wx.BITMAP_TYPE_ANY)
        bmp_save = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_save_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_show = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_show_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_hide = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_hide_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_play = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_play_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_rplay = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_rplay_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_stop = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_stop_32.png'), wx.BITMAP_TYPE_ANY)
        self.bmp_rstop = wx.Bitmap(os.path.join(BASE_PATH, 'res', 'tb_rstop_32.png'), wx.BITMAP_TYPE_ANY)
        
        self.tb = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, agwStyle=aui.AUI_TB_OVERFLOW | aui.AUI_TB_VERTICAL)
        self.tb.SetToolBitmapSize(wx.Size(32, 32))
        
        self.tb.AddSimpleTool(self.ID_CONFIG, '设置', bmp_config, '参数设置')
        self.tb.AddSimpleTool(self.ID_STYLE, '风格', bmp_style, '画布风格')
        self.tb.AddSimpleTool(self.ID_SAVE, '保存', bmp_save, '保存画布')
        self.tb.AddSeparator()
        self.tb.AddSimpleTool(self.ID_SELECT, '选择', self.bmp_show, '显示隐藏的模型')
        self.tb.AddSimpleTool(self.ID_RESTORE, '复位', bmp_restore, '初始位置')
        self.tb.AddSimpleTool(self.ID_ANIMATE, '动画', self.bmp_play, '播放动画', kind=aui.ITEM_CHECK)
        
        self.tb.EnableTool(self.ID_ANIMATE, False)
        self.tb.Realize()
        
        self.sb = self.CreateStatusBar()
        self.sb.SetFieldsCount(4)
        self.sb.SetStatusWidths([-2, -12, -1, -1])
        self.sb.SetStatusStyles([wx.SB_RAISED, wx.SB_RAISED, wx.SB_RAISED, wx.SB_RAISED])
        
        proj = '正射投影' if self.fig.args.get('proj', 'P')[0].upper() == 'O' else '透视投影'
        self.sb.SetStatusText('投影方式：%s' % proj, 0)
        self.sb.SetStatusText('', 1)
        self.sb.SetStatusText('选中：0', 2)
        self.sb.SetStatusText('', 3)
        
        self._mgr = aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        self._mgr.AddPane(self.scene, aui.AuiPaneInfo().Name('Scene').CenterPane().Show())
        self._mgr.AddPane(self.tb, aui.AuiPaneInfo().Name('ToolBar').ToolbarPane().Left())
        self._mgr.Update()
        
        self.Bind(wx.EVT_MENU, self.on_config, id=self.ID_CONFIG)
        self.Bind(wx.EVT_MENU, self.on_style, id=self.ID_STYLE)
        self.Bind(wx.EVT_MENU, self.on_restore, id=self.ID_RESTORE)
        self.Bind(wx.EVT_MENU, self.on_select, id=self.ID_SELECT)
        self.Bind(wx.EVT_MENU, self.on_save, id=self.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_pause, id=self.ID_ANIMATE)
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
    
    def on_color(self, evt):
        """选择风格"""
        
        idx = evt.GetId()
        
        if idx == self.id_blue.Id:
            self.fig.style = 'blue'
        elif idx == self.id_gray.Id:
            self.fig.style = 'gray'
        elif idx == self.id_white.Id:
            self.fig.style = 'white'
        elif idx == self.id_black.Id:
            self.fig.style = 'black'
        else:
            self.fig.style = 'royal'
        
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
        
        dlg = wx.Dialog(self, size=(400, 330), title='参数设置')
        dlg.CenterOnScreen()
        
        wx.StaticBox(dlg, -1, 'GIF/视频设置', pos=(20,90), size=(350,135))
        
        wx.StaticText(dlg, -1, '文件格式：', pos=(40,117), size=(80,-1), style=wx.ALIGN_RIGHT)
        rb_gif = wx.RadioButton(dlg, id=-1, label='.gif', pos=(120,115), size=(55,20), style=wx.RB_GROUP)
        rb_avi = wx.RadioButton(dlg, id=-1, label='.avi', pos=(175,115), size=(55,20))
        rb_mp4 = wx.RadioButton(dlg, id=-1, label='.mp4', pos=(230,115), size=(55,20))
        rb_none = wx.RadioButton(dlg, id=-1, label='.无', pos=(295,115), size=(55,20))
        
        if self.fig.ext == '.gif':
            rb_gif.SetValue(True)
        elif self.fig.ext == '.avi':
            rb_avi.SetValue(True)
        elif self.fig.ext == '.mp4':
            rb_mp4.SetValue(True)
        else:
            rb_none.SetValue(True)
        
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
        
        wx.StaticBox(dlg, -1, '文件保存路径', pos=(20,20), size=(350,60))
        
        tc_dir = wx.TextCtrl(dlg, -1, value='%s'%self.fig.folder, pos=(40,45), size=(265,20))
        btn_dir = wx.Button(dlg, -1, '浏览', pos=(310,45), size=(40,20))
        btn_dir.Bind(wx.EVT_BUTTON, on_dir)
               
        btn_cancel = wxbtn.GenButton(dlg, wx.ID_CANCEL, '取消', pos=(120,240), size=(60,-1))
        btn_cancel.SetBezelWidth(2)
        btn_cancel.SetBackgroundColour(wx.Colour(217,228,241))
        
        btn_ok = wxbtn.GenButton(dlg, wx.ID_OK, '确定', pos=(230,240), size=(60,-1))
        btn_ok.SetBezelWidth(2)
        btn_ok.SetBackgroundColour(wx.Colour(245,227,129))
        
        if dlg.ShowModal() == wx.ID_OK:
            if rb_gif.GetValue():
                self.fig.ext = '.gif'
            elif rb_avi.GetValue():
                self.fig.ext = '.avi'
            elif rb_mp4.GetValue():
                self.fig.ext = '.mp4'
            else:
                self.fig.ext = None
            
            if self.fig.ext:
                self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_rplay)
                self.tb.SetToolShortHelp(self.ID_ANIMATE, '录制视频')
            else:
                self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_play)
                self.tb.SetToolShortHelp(self.ID_ANIMATE, '播放动画')
            self.tb.Realize()
            
            self.fig.fps = int(tc_fps.GetValue())
            self.fig.fn = int(tc_fn.GetValue())
            self.fig.loop = 1 - int(cb_loop.GetValue())
            
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
        
        m2 =  wx.MenuItem(submenu, self.id_gray, '国际灰', kind=wx.ITEM_RADIO)
        submenu.Append(m2)
        if self.fig.style == 'gray':
            m2.Check(True)
        
        m3 =  wx.MenuItem(submenu, self.id_black, '石墨黑', kind=wx.ITEM_RADIO)
        submenu.Append(m3)
        if self.fig.style == 'black':
            m3.Check(True)
        
        m4 =  wx.MenuItem(submenu, self.id_white, '珍珠白', kind=wx.ITEM_RADIO)
        submenu.Append(m4)
        if self.fig.style == 'white':
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
    
    def on_pause(self, evt):
        """暂停/启动"""
        
        if self.scene.playing:
            if self.fig.ext:
                self.scene.stop_record()
            else:
                self.scene.stop_animate()
                
                self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_play)
                self.tb.SetToolShortHelp(self.ID_ANIMATE, '播放动画')
                self.tb.EnableTool(self.ID_CONFIG, True)
                self.tb.EnableTool(self.ID_STYLE, True)
                self.tb.EnableTool(self.ID_SAVE, True)
                self.tb.EnableTool(self.ID_RESTORE, True)
                self.tb.EnableTool(self.ID_SELECT, True)
                self.sb.SetStatusText('%0.1ffps'%self.scene.estimate(), 3)
        else:
            self.tb.EnableTool(self.ID_CONFIG, False)
            self.tb.EnableTool(self.ID_STYLE, False)
            self.tb.EnableTool(self.ID_SAVE, False)
            self.tb.EnableTool(self.ID_RESTORE, False)
            self.tb.EnableTool(self.ID_SELECT, False)
            self.tb.SetToolShortHelp(self.ID_ANIMATE, '停止')
            self.sb.SetStatusText('', 3)
            
            if self.fig.ext:
                self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_rstop)
                
                out_file = os.path.join(self.fig.folder, '%s%s'%(time.strftime('%Y%m%d_%H%M%S'), self.fig.ext))
                self.scene.start_record(out_file, self.fig.fps, self.fig.fn, self.fig.loop)
                self.recording_timer.Start(50)
                
            else:
                self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_stop)
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
    
    def on_select(self, evt):
        """显示/隐藏模型"""
        
        if len(self.scene.selected) > 0:
            for reg, name in self.scene.selected:
                for m in reg.models[name]:
                    m.picked = False
                    m.visible = False
            
            self.scene.selected.clear()
            self.sb.SetStatusText('选中：0', 2)
            self.tb.Realize()
            
            self.tb.SetToolBitmap(self.ID_SELECT, self.bmp_show)
            self.tb.SetToolShortHelp(self.ID_SELECT, '显示隐藏的模型')
        else:
            for reg in self.scene.regions:
                for name in reg.models:
                    for m in reg.models[name]:
                        m.visible = True
        
        self.scene.render()
    
    def update_select(self):
        """选中或取消选中后更新按钮状态"""
        
        n = len(self.scene.selected)
        self.sb.SetStatusText('选中：%d'%n, 2)
        
        if n > 0:
            self.tb.SetToolBitmap(self.ID_SELECT, self.bmp_hide)
            self.tb.SetToolShortHelp(self.ID_SELECT, '隐藏选中的模型')
        else:
            self.tb.SetToolBitmap(self.ID_SELECT, self.bmp_show)
            self.tb.SetToolShortHelp(self.ID_SELECT, '显示隐藏的模型')
        
        self.tb.Realize()            
    
    def after_stop_record(self, evt):
        """自动或手动停止录屏后的操作"""
        
        if not self.scene.capturing:
            if self.fig.ext:
                self.fig.ext = None
                self.sb.SetStatusText('%0.1ffps'%self.scene.estimate(), 3)
                
                self.tb.EnableTool(self.ID_CONFIG, True)
                self.tb.EnableTool(self.ID_STYLE, True)
                self.tb.EnableTool(self.ID_SAVE, True)
                self.tb.EnableTool(self.ID_RESTORE, True)
                self.tb.EnableTool(self.ID_SELECT, True)
                self.tb.SetToolBitmap(self.ID_ANIMATE, self.bmp_play)
                self.tb.SetToolShortHelp(self.ID_ANIMATE, '播放动画')
                self.tb.ToggleTool(self.ID_ANIMATE, False)
                self.tb.Realize()
            
            if self.scene.creating:
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

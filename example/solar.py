import wxgl
import numpy as np
from skyfield.api import load, utc
from datetime import datetime, timedelta

class SolarSystemModel:
    """太阳系天体轨道计算类"""

     # 天体常量：半径r（km）、公转周期revo（太阳日）、自转周期spin（小时）和自转轴倾角tilt（度，相对于黄道面）
    CONST = {
        'sun':      {'r': 696300,   'revo': 0,          'spin': 24*24.47,   'tilt': 7},
        'mercury':  {'r': 2440,     'revo': 87.99,      'spin': 24*58.6,    'tilt': 0},
        'venus':    {'r': 6052,     'revo': 224.70,     'spin': 24*243,    'tilt': 177.3},
        'earth':    {'r': 6371,     'revo': 365.2564,   'spin': 23.934,     'tilt': 23.43},
        'mars':     {'r': 3398,     'revo': 686.97,     'spin': 24.617,     'tilt': 25.2},
        'jupiter':  {'r': 71492,    'revo': 4332.71,    'spin': 9.833,      'tilt': 3.1},
        'saturn':   {'r': 60268,    'revo': 10759.5,    'spin': 10.233,     'tilt': 26.7},
        'uranus':   {'r': 25559,    'revo': 30685,      'spin': 17.24,     'tilt': 97.8},
        'neptune':  {'r': 24718,    'revo': 60194.25,   'spin': 15.966,     'tilt': 28.3},
        'moon':     {'r': 1738,     'revo': 27.32,      'spin': 24*27.32,   'tilt': 1.5424}
    }

    def __init__(self, de_file, t_factor=28800, d_factor=1/50, r_factor=20, start_dt=None):
        """构造函数

        de_file         - JPL星历表文件
        t_factor        - 时间加速因子，默认模型中的1秒对应实际时间的28800秒（8小时）
        d_factor        - 距离缩放因子，默认以实际天体间距离的1/50绘制模型
        r_factor        - 除太阳外其他天体半径缩放因子，默认以实际半径的20倍绘制模型
        start_dt        - 开始日期时间字符串（YYYY-MM-DD hh:mm:ss），默认None，表示当前UTC时刻开始
        """

        self.t_factor = t_factor
        self.d_factor = d_factor
        self.r_factor = r_factor
        self.start_dt = datetime.utcnow().replace(tzinfo=utc) if start_dt is None else datetime.fromisoformat(start_dt).replace(tzinfo=utc)
        
        self.ts = load.timescale() # 创建处理时间的对象
        self.planets = load(de_file) # 加载星历文件
        self.k = 20000 * r_factor / (380000 * d_factor) # 地月距离缩放系数

    def get_ecliptic_xyz_at_dt(self, planet_name, dt):
        """根据日期时间计算天体在黄道坐标系中的坐标

        planet_name     - 天体名称
        dt              - datetime类型的日期时间
        """

        t = self.ts.from_datetime(dt)
        name = '%s_barycenter'%planet_name if planet_name in ('jupiter', 'saturn', 'uranus', 'neptune') else planet_name
        x, y, z = self.planets[name].at(t).ecliptic_xyz().km

        return x*self.d_factor, y*self.d_factor, z*self.d_factor

    def get_ecliptic_xyz(self, planet_name, time_delta):
        """计算天体在黄道坐标系中的坐标

        planet_name     - 天体名称
        time_delta      - 距离开始时刻的时间偏移量，以为毫秒单位
        """

        seconds = self.t_factor * time_delta / 1000 # 模型时间转换为实际时间偏移量
        dt = self.start_dt + timedelta(seconds=seconds)

        return self.get_ecliptic_xyz_at_dt(planet_name, dt)

    def get_ecliptic_orbit(self, planet_name):
        """计算天体单个公转周期的运行轨道，planet_name为天体名称"""

        days = round(self.CONST[planet_name]['revo'] - 366)
        dt = self.start_dt - timedelta(days=days) if days > 0 else self.start_dt 
        hours = np.linspace(0, self.CONST[planet_name]['revo'], 1001) * 24
        t = self.ts.utc(dt.year, dt.month, dt.day, hours)
        name = '%s_barycenter'%planet_name if planet_name in ('jupiter', 'saturn', 'uranus', 'neptune') else planet_name
        x, y, z = self.planets[name].at(t).ecliptic_xyz().km

        return np.stack((x*self.d_factor, y*self.d_factor, z*self.d_factor), axis=1)

    def get_sphere(self, planet_name):
        """返回天体球面网格的顶点坐标，planet_name为天体名称"""

        r = self.CONST[planet_name]['r'] if planet_name == 'sun' else  self.CONST[planet_name]['r'] * self.r_factor
        gv, gu = np.mgrid[np.pi/2:-np.pi/2:37j, 0:2*np.pi:73j]

        zs = r * np.sin(gv)
        xs = r * np.cos(gv) * np.cos(gu)
        ys = r * np.cos(gv) * np.sin(gu)

        return xs, ys, zs

    def get_axis(self, planet_name):
        """返回天体旋转轴的顶点坐标，planet_name为天体名称"""

        r = self.CONST[planet_name]['r'] * self.r_factor
        
        return [[0, 0, 1.5*r], [0, 0, -1.5*r]]

    def dt_func(self, t):
        """格式化日期时间的函数，用于在UI的状态栏显示模型对应的UTC时间"""

        return self.ts.from_datetime(self.start_dt + timedelta(seconds=self.t_factor*t/1000)).utc_iso()

    def tf_sun(self, t):
        """太阳模型变换函数，实现自转"""
    
        speed = 0.36 / (self.CONST['sun']['spin'] * 3600 / self.t_factor)
        phi = (t * speed) % 360

        return ((0, 0, 1, phi), )
    
    def tf_moon(self, t):
        """月球模型变换函数，跟随地球运动的同时实现自转、旋转轴倾斜和公转"""
    
        rotate = (0, 0, 1, (t * 0.36 / (self.CONST['moon']['spin'] * 3600 / self.t_factor)) % 360)
        tile = (-1, 0, 0, self.CONST['moon']['tilt'])
        xm, ym, zm = self.get_ecliptic_xyz('moon', t)
        xe, ye, ze = self.get_ecliptic_xyz('earth', t)
        shift = xe+(xm-xe)*self.k, ye+(ym-ye)*self.k, ze+(zm-ze)*self.k

        return (rotate, tile, shift)

    def tf_factory(self, planet_name):
        """天体模型变换函数生成器，返回实现天体自转、旋转轴倾斜、公转的变换函数"""
    
        def tf(t):
            rotate = (0, 0, 1, (t * 0.36 / (self.CONST[planet_name]['spin'] * 3600 / self.t_factor)) % 360)
            tile = (-1, 0, 0, self.CONST[planet_name]['tilt'])
            shift = self.get_ecliptic_xyz(planet_name, t)
    
            return (rotate, tile, shift)

        return tf
    
    def show_ecs(self):
        """绘制黄道坐标系模型"""

        app = wxgl.App(haxis='z', elev=15, fovy=35, backend='qt')
        app.title('太阳系模型')
        app.info(time_func=self.dt_func) # 在状态栏中显示日期时间信息
        
        # 绘制太阳
        xs, ys, zs = self.get_sphere('sun')
        app.mesh(xs, ys, zs, texture='res/sun.jpg', light=wxgl.BaseLight(), transform=self.tf_sun)

        # 绘制月球
        xs, ys, zs = self.get_sphere('moon')
        app.mesh(xs, ys, zs, texture='res/moon.jpg', light=wxgl.BaseLight(), transform=self.tf_moon)
        
        # 绘制8个行星
        names = ('mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune')
        colors = ('dodgerblue', 'gold', 'cyan', 'firebrick', 'burlywood', 'darksalmon', 'lightgray', 'lightskyblue')
        for name, color in zip(names, colors):
            # 绘制行星
            xs, ys, zs = self.get_sphere(name)
            app.mesh(xs, ys, zs, texture='res/%s.jpg'%name, light=wxgl.BaseLight(), transform=self.tf_factory(name))
            
            # 绘制行星自转轴
            vs = self.get_axis(name)
            app.line(vs, color=color, stipple='dash-dot', transform=self.tf_factory(name))
        
            # 绘制行星公转轨道线
            orbit = self.get_ecliptic_orbit(name)
            app.line(orbit, color=color)

        # 绘制春分、秋分、夏至和冬至标识
        for dt_str, word in (('03-21','春分'), ('06-22','夏至'), ('09-22','秋分'), ('12-23','冬至')):
            dt = datetime.fromisoformat('%d-%s'%(self.start_dt.year, dt_str)).replace(tzinfo=utc)
            x, y, z = self.get_ecliptic_xyz_at_dt('earth', dt)
            d = 4000 * self.r_factor
            box = [[x-2*d, y, z-d], [x-2*d, y, z-2*d], [x+2*d, y, z-2*d], [x+2*d, y, z-d]]

            app.line([[x, y, z+d], [x, y, z-d]], color='white', width=2)
            app.text3d(word, box, align='center')

        app.show()

if __name__ == '__main__':
    ssm = SolarSystemModel('res/de405.bsp', start_dt='1962-02-05 01:00:00') # 该日期七星连珠
    ssm.show_ecs()

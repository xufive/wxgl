import time
import threading

class PyTimer:
    """定时器类"""
    
    def __init__(self, func, *args, **kwargs):
        """构造函数"""
        
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.time_thread = None
        self.task_thread = None
        self.running = False
    
    def _run_func(self):
        """运行定时事件函数"""
        
        if self.task_thread is None or not self.task_thread.isAlive():
            self.task_thread = threading.Thread(target=self.func, args=self.args, kwargs=self.kwargs)
            self.task_thread.setDaemon(True)
            self.task_thread.start()
    
    def _start(self, interval, once):
        """启动定时器的线程函数"""
        
        if interval < 0.01:
            interval = 0.01
        
        if interval < 0.05:
            dt = 0.005
        else:
            dt = interval/10
        
        if once:
            deadline = time.time() + interval
            while time.time() < deadline:
                time.sleep(dt)
            
            # 定时时间到，调用定时事件函数
            self.func(*self.args, **self.kwargs)
        else:
            self.running = True
            deadline = time.time() + interval
            while self.running:
                while time.time() < deadline:
                    time.sleep(dt)
                
                # 更新下一次定时时间
                deadline += interval
                #t = time.time()
                #if deadline < t:
                #    deadline = t
                
                # 定时时间到，调用定时事件函数
                if self.running:
                    self._run_func()
                    #self.func(*self.args, **self.kwargs)
    
    def start(self, interval, once=False):
        """启动定时器
        
        interval    - 定时间隔，浮点型，以毫秒为单位，最高精度10毫秒
        once        - 是否仅启动一次，默认是连续的
        """
        
        if self.time_thread is None or not self.time_thread.isAlive():
            self.time_thread = threading.Thread(target=self._start, args=(interval/1000, once))
            self.time_thread.setDaemon(True)
            self.time_thread.start()
    
    def stop(self):
        """停止定时器"""
        
        self.running = False
        while self.time_thread and self.time_thread.isAlive():
            time.sleep(0.01)
        time.sleep(0.010)
    
    def IsRunning(self):
        """返回运行状态"""
        
        return self.running or self.time_thread and self.time_thread.isAlive()

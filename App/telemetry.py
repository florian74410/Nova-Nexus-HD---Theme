"""One shared psutil collector for every metric plugin; no duplicate sampling loops."""
import platform
import psutil
from PySide6.QtCore import QObject, QTimer, Signal

class Telemetry(QObject):
    sampled = Signal(dict)
    def __init__(self, interval_ms=2000, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setTimerType(__import__("PySide6.QtCore",fromlist=["Qt"]).Qt.CoarseTimer)
        self.timer.timeout.connect(self.collect)
        self.set_interval(interval_ms)
        psutil.cpu_percent(interval=None)
    def set_interval(self, milliseconds):
        self.timer.setInterval(max(500,min(60000,int(milliseconds))))
    def start(self):
        if not self.timer.isActive():
            self.timer.start()
            self.collect()
    def stop(self):
        self.timer.stop()
    def collect(self):
        freq=psutil.cpu_freq()
        temps={}
        try:
            for name, entries in psutil.sensors_temperatures().items():
                temps[name]=[{"label":e.label,"c":e.current,"high":e.high,"critical":e.critical} for e in entries]
        except (OSError,AttributeError,RuntimeError):
            pass
        self.sampled.emit({"cpu":{"model":platform.processor() or platform.machine(),
            "usage":psutil.cpu_percent(interval=None),
            "frequency_mhz":freq.current if freq else None,
            "min_mhz":freq.min if freq else None,
            "max_mhz":freq.max if freq else None,
            "logical":psutil.cpu_count(logical=True),
            "physical":psutil.cpu_count(logical=False),
            "per_core":psutil.cpu_percent(interval=None,percpu=True),
            "temperatures":temps}})

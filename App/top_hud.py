"""Event-driven top HUD for Linux X11; no polling or background timers."""
import sys
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QGuiApplication
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from .cpu_gauge import CPUGauge

def clamp(value, folded=False):
    low, high, default = (10, 20, 12) if folded else (20, 50, 30)
    try: return max(low, min(high, int(value)))
    except (TypeError, ValueError): return default

def strut(width, height):
    return [0, 0, height, 0, 0, 0, 0, 0, 0, width-1, 0, 0]

class TopHUD(QWidget):
    changed = Signal(bool)
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.folded = False
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4,0,6,0)
        self.cpu_gauge = CPUGauge(self)
        self.cpu_gauge.setFixedWidth(132)
        layout.addWidget(self.cpu_gauge)
        layout.addStretch()
        self.arrow = QPushButton("⌃")
        self.arrow.setFixedWidth(26)
        self.arrow.clicked.connect(self.toggle)
        layout.addWidget(self.arrow)
        screen = QGuiApplication.primaryScreen()
        if screen: screen.geometryChanged.connect(self.refresh)
        self.refresh()
    def values(self):
        return self.config.get("plugins", {}).get("nexus-top-hud", {})
    def height_for_state(self):
        v=self.values()
        return clamp(v.get("collapsed_height",12), True) if self.folded else clamp(v.get("expanded_height",30))
    def refresh(self, *_):
        screen=QGuiApplication.primaryScreen()
        if screen is None: return
        geo=screen.geometry()
        self.setGeometry(geo.x(),geo.y(),geo.width(),self.height_for_state())
        t=self.config["theme"]
        self.arrow.setText("⌄" if self.folded else "⌃")
        self.arrow.setToolTip("Déployer" if self.folded else "Rétracter")
        self.arrow.setStyleSheet("QPushButton{background:transparent;border:1px solid #9A324C;"
                                 "color:#FF365F;font-size:18px;padding:0;}")
        self.cpu_gauge.setVisible(not self.folded and self.config.get('plugins', {}).get('cpu-plugin', {}).get('enabled', True))
        self.reserve(self.height_for_state() if self.isVisible() else 0)
        self.update()
    def reserve(self, height):
        from PySide6.QtWidgets import QApplication
        if not sys.platform.startswith("linux") or QApplication.platformName() != "xcb": return
        con=None
        try:
            from Xlib import display, Xatom
            con=display.Display()
            root=con.screen().root
            win=con.create_resource_object("window",int(self.winId()))
            width=con.screen().width_in_pixels
            win.change_property(con.intern_atom("_NET_WM_STRUT_PARTIAL"),Xatom.CARDINAL,32,strut(width,height))
            win.change_property(con.intern_atom("_NET_WM_STRUT"),Xatom.CARDINAL,32,[0,0,height,0])
            win.change_property(con.intern_atom("_NET_WM_WINDOW_TYPE"),Xatom.ATOM,32,
                                [con.intern_atom("_NET_WM_WINDOW_TYPE_DOCK")])
            con.sync()
        except Exception:
            pass
        finally:
            if con is not None: con.close()
    def showEvent(self, event):
        super().showEvent(event)
        self.reserve(self.height_for_state())
    def hideEvent(self,event):
        self.reserve(0)
        super().hideEvent(event)
    def closeEvent(self,event):
        self.reserve(0)
        super().closeEvent(event)
    def set_sample(self,sample):
        self.cpu_gauge.set_sample(sample)

    def toggle(self):
        self.folded=not self.folded
        self.refresh()
        self.changed.emit(self.folded)
    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t=self.config["theme"]
        bg=QColor(t["background"])
        bg.setAlphaF(t["opacity"]/100)
        p.fillRect(self.rect(),bg)
        p.setPen(QPen(QColor(t["primary"]),1.5))
        p.drawLine(0,self.height()-1,self.width(),self.height()-1)
        for x in range(22,min(self.width()-40,390),110):
            p.drawLine(x,2,x+25,2)
            p.drawLine(x+25,2,x+33,min(self.height()-2,9))
            p.setBrush(QColor(t["secondary"]))
            p.drawEllipse(x+31,min(self.height()-5,7),3,3)
        p.end()

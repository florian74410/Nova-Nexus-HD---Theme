"""Event-driven top HUD for Linux X11; no polling or background timers."""
import sys
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QGuiApplication, QPainterPath, QPolygonF
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout

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
    def toggle(self):
        self.folded=not self.folded
        self.refresh()
        self.changed.emit(self.folded)
    def paintEvent(self,event):
        # NovaBar 1.0 styling: faceted glass, electric-blue perimeter,
        # PCB traces and red navigation; intentionally fully static.
        p=QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t=self.config["theme"]
        w,h=self.width(),self.height()
        if w<80 or h<8:
            p.end()
            return
        bg=QColor(t["background"])
        bg.setAlphaF(t["opacity"]/100)
        shape=QPainterPath()
        bevel=min(12,max(3,h//4))
        shape.addPolygon(QPolygonF([
            QPointF(0,bevel),QPointF(bevel,0),QPointF(w-bevel,0),
            QPointF(w,bevel),QPointF(w,h-bevel),QPointF(w-bevel,h),
            QPointF(bevel,h),QPointF(0,h-bevel)]))
        p.fillPath(shape,bg)
        blue=QColor("#31DCFF")
        blue.setAlpha(205)
        p.setPen(QPen(blue,1.3))
        p.drawPath(shape)
        p.setPen(QPen(QColor("#17639B"),1))
        p.drawLine(bevel+2,h-4,w-bevel-2,h-4)
        # Short routed PCB tracks echo the NovaBar 1.0 signature.
        if not self.folded:
            cyan=QColor(t["primary"])
            cyan.setAlpha(135)
            p.setPen(QPen(cyan,1.2))
            for x in range(35,max(36,w-160),145):
                end=min(x+74,w-65)
                p.drawLine(x,3,x+18,3)
                p.drawLine(x+18,3,x+25,min(h-5,10))
                p.drawLine(x+25,min(h-5,10),end,min(h-5,10))
                p.setBrush(QColor(t["secondary"]))
                p.drawEllipse(QPointF(end,min(h-5,10)),2.0,2.0)
        p.end()

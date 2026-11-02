"""Custom no-needle segmented dial, reused visual primitives by future plugins."""
import math
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget

def gradient(t):
    t=max(0,min(1,float(t)))
    stops=[(0,(25,215,115)),(.45,(217,225,43)),(.7,(255,145,35)),(1,(252,48,74))]
    for (x,a),(y,b) in zip(stops,stops[1:]):
        if t<=y:
            p=(t-x)/(y-x)
            return QColor(*[round(v+(w-v)*p) for v,w in zip(a,b)])
    return QColor(252,48,74)

class CPUGauge(QWidget):
    details_requested=Signal()
    def __init__(self,parent=None):
        super().__init__(parent)
        self.data={}
        self.setMinimumSize(50,10)
        self.setToolTip("Cliquer pour les détails du processeur")
    def set_sample(self, sample):
        self.data=sample.get("cpu",{})
        self.update()
    def mouseReleaseEvent(self,event):
        if event.button()==Qt.LeftButton: self.details_requested.emit()
        super().mouseReleaseEvent(event)
    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height()
        scale=min(w,h)
        rect=QRectF((w-scale)/2+6,(h-scale)/2+6,max(1,scale-12),max(1,scale-12))
        usage=self.data.get("usage")
        level=max(0,min(1,usage/100)) if isinstance(usage,(int,float)) else 0
        if h < 25:
            f=self.data.get('frequency_mhz')
            p.setPen(QColor('#DDFBFF'))
            p.setFont(QFont('Rajdhani',max(8,int(h*.65)),QFont.Bold))
            p.drawText(self.rect(),Qt.AlignCenter,f'{f/1000:.2f} GHz' if isinstance(f,(int,float)) else '-- GHz')
            p.end()
            return
        for i in range(32):
            ratio=i/31
            color=gradient(ratio) if ratio<=level else QColor(37,67,82,145)
            p.setPen(QPen(color,max(3,scale*.038),Qt.SolidLine,Qt.RoundCap))
            angle=215-i*(250/32)
            p.drawArc(rect,int(angle*16),int(-5.6*16))
        frequency=self.data.get("frequency_mhz")
        label=f"{frequency/1000:.2f}" if isinstance(frequency,(int,float)) else "--"
        big=QFont("Rajdhani",max(14,int(scale*.19)),QFont.Bold)
        p.setFont(big)
        p.setPen(QColor("#DDFBFF"))
        p.drawText(QRectF(0,h*.28,w,h*.3),Qt.AlignCenter,label)
        p.setFont(QFont("Exo 2",max(8,int(scale*.085))))
        p.setPen(QColor("#58DFFF"))
        p.drawText(QRectF(0,h*.57,w,h*.17),Qt.AlignCenter,"GHz")
        p.end()

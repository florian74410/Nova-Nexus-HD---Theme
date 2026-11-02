"""Shared electric-blue window buttons with font-independent red symbols."""
from PySide6 import QtCore as C, QtGui as G, QtWidgets as W


def _icon(action):
    from .theme_engine import get_active_theme
    theme=get_active_theme()
    pixmap = G.QPixmap(18, 18)
    pixmap.fill(C.Qt.transparent)
    painter = G.QPainter(pixmap)
    painter.setRenderHint(G.QPainter.Antialiasing)
    painter.setPen(G.QPen(G.QColor(theme['colors']['danger']), 2))
    if action == 'minimize':
        painter.drawLine(4, 12, 14, 12)
    elif action == 'close':
        painter.drawLine(5, 5, 13, 13)
        painter.drawLine(13, 5, 5, 13)
    elif action == 'restore':
        painter.drawRect(7, 4, 7, 7)
        painter.fillRect(4, 7, 7, 7, G.QColor('#071C30'))
        painter.drawRect(4, 7, 7, 7)
    else:
        painter.drawRect(4, 4, 10, 10)
        painter.drawLine(4, 7, 14, 7)
    painter.end()
    return G.QIcon(pixmap)


class WindowControls(C.QObject):
    """Keep maximize/restore state synchronized, including external WM changes."""
    def __init__(self, window, layout, *, close=None):
        super().__init__(window)
        self.window = window
        self.buttons = {}
        self.normal_geometry = None
        for action, label, callback in (
            ('minimize', 'Minimiser', window.showMinimized),
            ('maximize', 'Maximiser', self.toggle_maximized),
            ('close', 'Fermer', close or window.close),
        ):
            button = W.QPushButton()
            button.setObjectName('nova' + action.title())
            button.setFixedSize(26, 26)
            button.setAutoDefault(False)
            button.setIcon(_icon(action))
            button.setIconSize(C.QSize(18, 18))
            button.setToolTip(label)
            button.setAccessibleName(label)
            button.setStyleSheet('QPushButton{border:1px solid #00CBF3;'
                'background:#071C30;padding:0;border-radius:0;}'
                'QPushButton:hover{background:#124E75;border:2px solid #3EEBFF;}'
                'QPushButton:pressed{background:#156497;}'
                'QPushButton:focus{border:2px solid #76EEFF;}')
            button.clicked.connect(callback)
            layout.addWidget(button)
            self.buttons[action] = button
        window.minbtn = self.buttons['minimize']
        window.maxbtn = self.buttons['maximize']
        window.closebtn = self.buttons['close']
        window.installEventFilter(self)
        self.sync()

    def toggle_maximized(self):
        if self.window.isMaximized() or self.window.isFullScreen():
            geometry = self.normal_geometry or self.window.normalGeometry()
            self.window.showNormal()
            if geometry.isValid():
                self.window.setGeometry(geometry)
        else:
            self.normal_geometry = self.window.geometry()
            self.window.showMaximized()

    def sync(self):
        expanded = self.window.isMaximized() or self.window.isFullScreen()
        button = self.buttons['maximize']
        button.setIcon(_icon('restore' if expanded else 'maximize'))
        label = 'Restaurer' if expanded else 'Maximiser'
        button.setToolTip(label)
        button.setAccessibleName(label)

    def eventFilter(self, watched, event):
        if event.type() in (C.QEvent.Resize, C.QEvent.Move):
            if not (self.window.isMaximized() or self.window.isFullScreen() or self.window.isMinimized()):
                self.normal_geometry = self.window.geometry()
        if event.type() == C.QEvent.WindowStateChange:
            self.sync()
        return False

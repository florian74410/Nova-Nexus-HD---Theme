"""Procedural PCB artwork shared by Nexus 0.1 surfaces.

Grid-aligned, 45-degree routed copper paths, round vias, twin-layer strokes
and elapsed-time electric pulses; no asset textures or random paint-time work.
"""
from __future__ import annotations
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPen, QPainterPath

def traces(width, height, edge=False):
    """Return stable polylines that keep the central content area readable."""
    w, h = float(width), float(height)
    if w < 100 or h < 18:
        return []
    routes = []
    if edge:
        # Repeated trace lanes inside the upper and lower PCB rails.
        for row in range(3):
            y = 5 + row * 5
            for x in range(25, int(w)-110, 175):
                routes.append([(x, y), (x+40, y), (x+49, y+6),
                               (x+91, y+6), (x+102, y)])
        return routes
    # Left and right are especially dense, leaving the middle for controls.
    for row in range(7):
        y = 56 + row * max(36, (h-130)/7)
        left = 6 + (row % 3)*5
        routes.append([(left, y), (38+row%3*9, y),
                       (58+row%3*9, y+20), (118+row%2*17, y+20),
                       (139+row%2*17, y+41)])
        routes.append([(w-left, y+10), (w-38-row%3*9, y+10),
                       (w-58-row%3*9, y+30), (w-124-row%2*17, y+30)])
    for col in range(9):
        x = 36 + col * max(72,(w-80)/9)
        routes.append([(x, 5), (x+25, 5), (x+38, 18), (x+70, 18)])
        routes.append([(x, h-5), (x+22, h-5), (x+36, h-19), (x+65, h-19)])
    return routes

def point_along(points, distance):
    lengths = [math.hypot(b[0]-a[0], b[1]-a[1]) for a,b in zip(points,points[1:])]
    remaining = distance % max(1.0, sum(lengths))
    for a,b,length in zip(points,points[1:],lengths):
        if remaining <= length:
            ratio = remaining/max(0.001,length)
            return QPointF(a[0]+(b[0]-a[0])*ratio, a[1]+(b[1]-a[1])*ratio)
        remaining -= length
    return QPointF(*points[-1])

def paint_tracks(painter, width, height, seconds, theme, edge=False, animated=True):
    cyan = QColor(theme.get("primary", "#00DFFF"))
    routes = traces(width,height,edge=edge)
    painter.save()
    for index, points in enumerate(routes):
        path = QPainterPath(QPointF(*points[0]))
        for point in points[1:]:
            path.lineTo(QPointF(*point))
        # Copper shadow, inner conductor, light along its full routed length.
        painter.setPen(QPen(QColor(0,20,39,195), 5.0))
        painter.drawPath(path)
        painter.setPen(QPen(QColor(cyan.red(),cyan.green(),cyan.blue(),90),2.7))
        painter.drawPath(path)
        painter.setPen(QPen(QColor(cyan.red(),cyan.green(),cyan.blue(),180),0.95))
        painter.drawPath(path)
        end = QPointF(*points[-1])
        painter.setPen(QPen(cyan,0.9))
        painter.setBrush(QColor(1,23,37,240))
        painter.drawEllipse(end,3.5,3.5)
        painter.setBrush(QColor(cyan.red(),cyan.green(),cyan.blue(),215))
        painter.drawEllipse(end,1.45,1.45)
        if animated and index % 2 == 0:
            # 620 px/s; real elapsed time avoids slow segment-by-segment hopping.
            travel = seconds*620.0 + index*37.0
            q = point_along(points,travel)
            painter.setPen(QPen(QColor(0,220,255,36),11))
            painter.drawPoint(q)
            painter.setPen(QPen(QColor(0,245,255,105),6))
            painter.drawPoint(q)
            painter.setPen(QPen(QColor(238,255,255,245),2.5))
            painter.drawPoint(q)
    painter.restore()

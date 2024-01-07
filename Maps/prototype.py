from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QApplication, QVBoxLayout, QPushButton, QWidget, QSlider, \
    QGraphicsPathItem, QGraphicsItem
from PyQt6.QtGui import QPolygonF, QPainterPath, QPen, QBrush, QColor
from PyQt6.QtCore import QPointF, Qt
import sys
import json
import numpy as np
import math


class PolygonItem(QGraphicsPathItem):
    def __init__(self, path, properties):
        super().__init__(path)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.properties = properties
        self.setBrush(QBrush(QColor(255, 255, 255)))

    def mousePressEvent(self, event):
        if self.brush().color() == QColor(255, 255, 255):
            self.setBrush(QBrush(QColor(255, 0, 0)))
        else:
            self.setBrush(QBrush(QColor(255, 255, 255)))
        print(self.properties)


class View(QGraphicsView):
    def __init__(self, scene, initial_scale=100, initial_rotation=0, initial_mirror=False):
        super().__init__(scene)
        self.mirror = initial_mirror
        self.rotation = initial_rotation
        self.scale(initial_scale / 100, initial_scale / 100)
        self.rotate(self.rotation)
        if self.mirror:
            self.scale(1, -1)

    def rotateRight(self):
        self.rotation -= 50
        self.rotate(-50)

    def rotateLeft(self):
        self.rotation += 50
        self.rotate(50)

    def mirrorView(self):
        self.mirror = not self.mirror
        if self.mirror:
            self.scale(1, -1)
        else:
            self.scale(1, -1)

    def zoom(self, value):
        self.resetTransform()
        self.scale(value / 100, value / 100)
        self.rotate(self.rotation)
        if self.mirror:
            self.scale(1, -1)


def geojsonToQtPolygon(geojson):
    polygons = []
    all_points = []
    for feature in geojson['features']:
        if feature['geometry']['type'] == 'Polygon':
            coordinates = feature['geometry']['coordinates'][0]
            points = [QPointF(float(x), float(y)) for x, y in map(getCartesian, coordinates)]
            all_points.extend(points)
            polygons.append((QPolygonF(points), feature['properties']))
    return polygons, all_points


def getCartesian(coord):
    lon, lat = np.deg2rad(coord)
    R = 7000  # radius of the earth
    x = R * np.cos(lat) * np.cos(lon)
    y = R * np.cos(lat) * np.sin(lon)
    return x, y


def drawPolygons(polygons, center, initial_scale=100, initial_rotation=0, initial_mirror=False):
    app = QApplication(sys.argv)

    scene = QGraphicsScene()
    for polygon, properties in polygons:
        path = QPainterPath()
        path.addPolygon(polygon.translated(-center))
        item = PolygonItem(path, properties)
        scene.addItem(item)

    view = View(scene, initial_scale, initial_rotation, initial_mirror)

    rotate_right_button = QPushButton("Obróć w prawo")
    rotate_right_button.clicked.connect(view.rotateRight)

    rotate_left_button = QPushButton("Obróć w lewo")
    rotate_left_button.clicked.connect(view.rotateLeft)

    mirror_button = QPushButton("Odbicie lustrzane")
    mirror_button.clicked.connect(view.mirrorView)

    zoom_slider = QSlider(Qt.Orientation.Horizontal)
    zoom_slider.setRange(50, 200)
    zoom_slider.setValue(initial_scale)
    zoom_slider.valueChanged.connect(view.zoom)

    layout = QVBoxLayout()
    layout.addWidget(view)
    layout.addWidget(rotate_right_button)
    layout.addWidget(rotate_left_button)
    layout.addWidget(mirror_button)
    layout.addWidget(zoom_slider)

    widget = QWidget()
    widget.setLayout(layout)
    widget.show()

    sys.exit(app.exec())


with open('poland_map_low_quality.geojson', encoding='utf-8') as f:
    geojson = json.load(f)

polygons, all_points = geojsonToQtPolygon(geojson)
center = QPointF(sum(p.x() for p in all_points) / len(all_points), sum(p.y() for p in all_points) / len(all_points))
drawPolygons(polygons, center, initial_scale=100, initial_rotation=110, initial_mirror=True)

from qtpy.QtWidgets import QWidget, QListWidgetItem
from qtpy.QtGui import QPixmap, QPainter, QCursor, QColor, QPen
from qtpy.QtCore import QPointF, Qt, QFile
from shape import Rectangle, Polygon
from widgets.label_dialog import LabelDialog

import cv2
import rectilinear_polygon
import json
import datetime
import os

class Canvas(QWidget):
    def __init__(self, parent):
        super(Canvas, self).__init__()

        self.SELECT, self.RECTANGLE, self.AUTO_POLYGON, self.POLYGON = 0, 1, 2, 3

        self._painter = QPainter()
        self.pixmap = None
        self.cv2_image = None
        self.scale = 1.0
        self.mode = self.SELECT
        self.label_dir = ""
        self.parent = parent
        self.reset()

        self.labelDialog = LabelDialog(
            parent=self,
            listItem = self.parent.labels
        )

    def reset(self):
        self.points = []
        self.objects = []
        self.cur_object = -1
        self.parent.load_object_list(self.objects)

    # load image and label file
    def load_file(self, image_dir):
        self.reset()
        self.pixmap = QPixmap(image_dir)
        self.cv2_image = cv2.imread(image_dir)
        self.label_dir = os.path.splitext(image_dir)[0] + '.json'
        if QFile.exists(self.label_dir):
            with open(self.label_dir) as json_file:
                data = json.load(json_file)
                self.objects = []
                for obj in data['objects']:
                    points = []
                    for point in obj['points']:
                        points.append(QPointF(point['x'], point['y']))
                    if (obj['type'] == 'rectangle'):
                        self.objects.append(Rectangle(points, obj['label']))
                    elif (obj['type'] == 'polygon'):
                        self.objects.append(Polygon(points, obj['label']))
                self.cur_object = len(self.objects) - 1
                self.parent.load_object_list(self.objects)
                self.parent.object_list_widget.setCurrentRow(self.cur_object)


        self.repaint()

    def offset_to_center(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    def transform_pos(self, point):
        return point / self.scale - self.offset_to_center()

    def rescale(self, value):
        if value >= 0.2 and value <= 5:
            self.scale = value
            self.repaint()

    def in_pixmap(self, p):
        w, h = self.pixmap.width(), self.pixmap.height()
        return (0 <= p.x() < w and 0 <= p.y() < h)

    def close_enough(self, p1, p2):
        epsilon = 0.01
        return  abs(p1.x() - p2.x()) <= max(5, epsilon * self.pixmap.width()) and \
                abs(p1.y() - p2.y()) <= max(5, epsilon * self.pixmap.height())
    
    def next_obj(self):
        if len(self.objects) > 0:
            self.cur_object = (self.cur_object + 1) % len(self.objects)
            self.parent.object_list_widget.setCurrentRow(self.cur_object)

    def prev_obj(self):
        if len(self.objects) > 0:
            self.cur_object = (self.cur_object + len(self.objects) - 1) % len(self.objects)
            self.parent.object_list_widget.setCurrentRow(self.cur_object)

    def del_obj(self):
        if len(self.objects) > 0:
            if self.cur_object == len(self.objects) - 1:
                new_id = self.cur_object - 1
            else:
                new_id = self.cur_object
            self.objects = self.objects[:self.cur_object] + self.objects[self.cur_object + 1:]
            self.cur_object = new_id
            self.parent.load_object_list(self.objects)
            self.parent.object_list_widget.setCurrentRow(self.cur_object)
            self.repaint()
            self.auto_export_json()

    def add_obj(self, obj):
        self.objects.append(obj)
        self.cur_object = len(self.objects) - 1
        self.parent.load_object_list(self.objects)
        self.parent.object_list_widget.setCurrentRow(self.cur_object)
        self.repaint()
        self.auto_export_json()

    def auto_export_json(self):
        data = {}
        data['date'] = str(datetime.datetime.now())
        data['objects'] = []
        for obj in self.objects:
            data_obj = {}
            obj.export_json(data_obj)
            data['objects'].append(data_obj)

        with open(self.label_dir, 'w') as json_file:
            json.dump(data, json_file)
        
        self.parent.load_file_list()
        self.parent.file_list_widget.setCurrentRow(self.parent.file_id)

    def paintEvent(self, event):
        if self.pixmap == None:
            return super(Canvas, self).paintEvent(event)

        p = self._painter
        p.begin(self)

        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offset_to_center())
        p.drawPixmap(0, 0, self.pixmap)

        pen = QPen()
        pen.setWidth(2 / self.scale)
        p.setPen(pen)

        for i, obj in enumerate(self.objects):
            if self.cur_object == i:
                p.setBrush(QColor(255, 0, 0, 100))
            else:
                p.setBrush(QColor(255, 0, 0, 0))
            obj.draw(p)

        if self.mode != self.SELECT:
            for point in self.points:
                p.drawEllipse(point, 2 / self.scale, 2 / self.scale)
            for i in range(len(self.points) - 1):
                p.drawLine(self.points[i], self.points[i + 1])

        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.transform_pos(event.localPos())
            if self.in_pixmap(pos):
                self.points.append(pos)
                self.repaint()

                if self.mode == self.RECTANGLE and len(self.points) == 2:
                    left_x = int(min(self.points[0].x(), self.points[1].x()))
                    right_x = int(max(self.points[0].x(), self.points[1].x()))
                    left_y = int(min(self.points[0].y(), self.points[1].y()))
                    right_y = int(max(self.points[0].y(), self.points[1].y()))

                    text = self.labelDialog.pop_up()
                    self.add_obj(Rectangle(self.points, text))
                    self.points = []

                if self.mode == self.AUTO_POLYGON and len(self.points) == 2:
                    left_x = int(min(self.points[0].x(), self.points[1].x()))
                    right_x = int(max(self.points[0].x(), self.points[1].x()))
                    left_y = int(min(self.points[0].y(), self.points[1].y()))
                    right_y = int(max(self.points[0].y(), self.points[1].y()))

                    tmp = rectilinear_polygon.main(self.cv2_image[left_y:right_y, left_x:right_x])
                    points = [QPointF(left_x + x, left_y + y) for x, y in tmp]
                    if (len(points) > 0):
                        text = self.labelDialog.pop_up()
                        self.add_obj(Polygon(points, text))
                    self.points = []

                if self.mode == self.POLYGON and len(self.points) >= 4 \
                        and self.close_enough(self.points[0], self.points[-1]):
                    text = self.labelDialog.pop_up()
                    self.add_obj(Polygon(self.points[:-1], text))
                    self.points = []
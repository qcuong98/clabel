from qtpy.QtCore import QRectF
from qtpy.QtGui import QPolygonF
from qtpy.QtCore import Qt

class Obj:
    def __init__(self, p, label = ""):
        self.points = p
        self.label = label

    def set_label(self, label):
        self.label = label

    def export_json(self, data_obj, obj_type):
        data_obj['type'] = obj_type
        data_obj['label'] = self.label
        data_obj['points'] = []
        for point in self.points:
            data_obj['points'].append({
                'x': point.x(),
                'y': point.y(),
            })

class Rectangle(Obj):
    def draw(self, painter):
        painter.drawRect(QRectF(self.points[0], self.points[1]))

    def export_json(self, data_obj):
        super(Rectangle, self).export_json(data_obj, 'rectangle')

class Polygon(Obj):
    def draw(self, painter):
        painter.drawPolygon(QPolygonF(self.points))

    def export_json(self, data_obj):
        super(Polygon, self).export_json(data_obj, 'polygon')
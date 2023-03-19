from source.figures import *
from PyQt5 import QtGui, QtCore
from enum import Enum
import logging

LOGGER_NAME = '3d-editor.drawer'
LOGGER = logging.getLogger(LOGGER_NAME)


class Color(Enum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4


COLORS = {
    Color.BLACK: QtCore.Qt.black,
    Color.RED: QtCore.Qt.red,
    Color.GREEN: QtCore.Qt.green,
    Color.YELLOW: QtCore.Qt.yellow,
    Color.BLUE: QtCore.Qt.blue}


def set_painter_params(painter, pen_color=QtGui.QColor(230, 102, 0),
                       pen_width=5, pen_style=QtCore.Qt.SolidLine,
                       brush_color=QtGui.QColor(230, 102, 30),
                       brush_style=QtCore.Qt.SolidPattern):
    painter.setPen(QtGui.QPen(pen_color, pen_width, pen_style))
    painter.setBrush(QtGui.QBrush(brush_color, brush_style))


class Drawer:
    def __init__(self, model):
        self.model = model
        self.displayed_objects = []
        self.points_display_table = {}

        self.point_color = Color.GREEN
        self.line_color = Color.BLACK
        self.plane_color = Color.BLUE
        self.ellipse_color = Color.BLUE

        self.scene_style_preset = 81
        self.axiss_size = 50
        self.axiss_width = 3

        self.draw_table = {
            Point: self.paint_point,
            Line: self.paint_line,
            Place: self.paint_place,
            Ellipse: self.paint_ellipse
        }

    def update_scene(self, painter, resolution, split_coordinates, zoom):
        set_painter_params(painter)
        painter.fillRect(
            0, 0, resolution[0], resolution[1],
            QtGui.QGradient.Preset(self.scene_style_preset))

        self.draw_coordinates_system(painter)

        self.displayed_objects = []
        self.paint_objects(
            split_coordinates, zoom, painter)

    def paint_objects(self, split_coordinates, zoom, painter):
        for obj in self.model.figures:
            if isinstance(obj, Point):
                display_coord = self.model.display_vector(
                    obj.to_vector3())
                self.points_display_table[obj] = (int(display_coord[0] * zoom +
                                                      split_coordinates[0]),
                                                  int(display_coord[1] * zoom +
                                                      split_coordinates[1]))
            self.draw_table[type(obj)](obj, painter)
            self.displayed_objects.append(obj)

    def paint_point(self, point, painter):
        color = Color(point.color.value)
        set_painter_params(painter, pen_color=COLORS[color],
                           brush_color=COLORS[color])
        painter.drawEllipse(int(self.points_display_table[point][0] -
                                point.WIDTH / 2),
                            int(self.points_display_table[point][1] -
                                point.WIDTH / 2),
                            point.WIDTH, point.WIDTH)

    def paint_line(self, line, painter):
        color = Color(line.color.value)
        set_painter_params(painter, pen_color=COLORS[color])
        painter.pen().setWidth(line.WIDTH)
        painter.drawLine(
            *self.points_display_table[line.start],
            *self.points_display_table[line.end])

    def paint_place(self, place, painter):
        color = Color(place.color.value)
        set_painter_params(painter, pen_color=COLORS[color])
        painter.pen().setWidth(place.WIDTH)
        painter.drawConvexPolygon(
            *[QtCore.QPointF(*self.points_display_table[point])
              for point in place.points])

    def paint_ellipse(self, ellipse, painter):
        color = Color(ellipse.color.value)
        set_painter_params(painter, pen_color=COLORS[color])
        painter.pen().setWidth(ellipse.WIDTH)

        p1 = QtCore.QPoint(*self.points_display_table[ellipse.topLeft])
        p2 = QtCore.QPoint(*self.points_display_table[ellipse.bottomRight])
        rect1 = QtCore.QRect(p1, p2)
        rect2 = QtCore.QRect(p1, p2)
        rect3 = QtCore.QRect(p1, p2)

        if not ellipse.rx:
            ellipse.set_move_info(rect1.width() // 2,
                                  rect1.height() // 2)
        painter.drawEllipse(rect1)

        if abs(rect2.height()) < abs(ellipse.ry // 2):
            rect2.setHeight(ellipse.ry // 2)
        rect2.setWidth(ellipse.rx // 2)
        self.paint_exstra_ellipse(rect2, rect1, color, painter)

        if abs(rect3.width()) < abs(ellipse.rx // 2):
            rect3.setWidth(ellipse.rx // 2)
        rect3.setHeight(ellipse.ry // 2)
        self.paint_exstra_ellipse(rect3, rect1, color, painter)

        set_painter_params(painter, pen_color=COLORS[color],
                           brush_color=QtGui.QColor(0, 0, 0, 0))
        painter.drawEllipse(rect2)

    def paint_exstra_ellipse(self, rect, rect_base, color, painter):
        center = rect_base.center()
        if abs(rect.width()) <= abs(rect_base.width()) and abs(rect.height()) <= abs(rect_base.height()):
            set_painter_params(painter, pen_color=COLORS[color],
                               brush_color=QtGui.QColor(0, 0, 0, 0))
        rect.moveCenter(center)
        painter.drawEllipse(rect)


    def draw_coordinates_system(self, painter):
        width = 5
        vect = self.model.origin.to_vector3()
        display_origin = self.model.display_vector(vect)
        display_origin = (int(display_origin[0] + 1200),
                          int(display_origin[1] + 60))
        painter.drawEllipse(int(display_origin[0] - width / 2),
                            int(display_origin[1] - width / 2),
                            width, width)

        colors_axis = (QtCore.Qt.green, QtCore.Qt.blue, QtCore.Qt.red)
        i = 0
        for color in colors_axis:
            pen = QtGui.QPen(color, self.axiss_width, QtCore.Qt.DashLine)
            painter.setPen(pen)
            self.draw_axis(painter, self.model.basis[i], display_origin)
            i = i + 1

    def draw_axis(self, painter, basis_vector, display_origin):
        width = 5
        temp_point = Point(basis_vector.x * self.axiss_size,
                           basis_vector.y * self.axiss_size,
                           basis_vector.z * self.axiss_size)
        display_coord = self.model.display_vector(temp_point.to_vector3())
        display_coord = (int(display_coord[0] + 1200),
                         int(display_coord[1] + 60))
        painter.drawEllipse(int(display_coord[0] - width / 2),
                            int(display_coord[1] - width / 2),
                            width, width)
        painter.drawLine(
            *display_origin,
            *display_coord)

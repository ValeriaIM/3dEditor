from source.figures import *
from PyQt5 import QtGui, QtWidgets, QtCore
from enum import Enum
import logging

LOGGER_NAME = '3d-editor.drawer'
LOGGER = logging.getLogger(LOGGER_NAME)

class Color(Enum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3

COLORS = {
    Color.BLACK: QtCore.Qt.black,
    Color.RED: QtCore.Qt.red,
    Color.GREEN: QtCore.Qt.green,
    Color.YELLOW: QtCore.Qt.yellow}


class Drawer:
    DEFAULT_COLOR_LIGHT = (255, 102, 0)
    DEFAULT_COLOR_DARK = (230, 102, 30)

    def __init__(self, model):
        self.model = model
        self.displayed_objects = []  # to hide objects later
        self.points_display_table = {}

        self.style_settings = {}

        self.current_color = self.DEFAULT_COLOR_LIGHT
        self.point_color = Color.GREEN
        self.line_color = Color.BLACK

        self.scene_style_preset = 81
        self.axiss_size = 50
        self.axiss_width = 3

        self.draw_table = {
            Point: self.paint_pt,
            Line: self.paint_ln
        }

        self.check_to_visible = {
            Point: lambda point: model.get_plate_equation_value(
                point.x,
                point.y,
                point.z) >= 0,
            Line: lambda line: any(model.get_plate_equation_value(
                line.start.x,
                line.start.y,
                line.start.z) >= 0,
                model.get_plate_equation_value(
                line.end.x,
                line.end.y,
                line.end.z) >= 0)
        }

    def update_scene(self, painter, resolution, split_coordinates, zoom, objects_to_highlit=set()):
        self.set_painter_params(painter)
        painter.fillRect(
            0, 0, resolution[0], resolution[1],
            QtGui.QGradient.Preset(self.scene_style_preset))

        self.draw_coordinates_system(painter)

        self.displayed_objects = []
        for obj in self.model.objects:
            self.paint_object(
                obj, split_coordinates, zoom, painter, objects_to_highlit)

    def paint_object(self, obj, split_coordinates, zoom, painter, objects_to_highlit):
        for obj in self.model.objects:
            if isinstance(obj, Point):
                display_coord = self.model.display_vector(
                    obj.to_vector3())
                self.points_display_table[obj] = (int(display_coord[0] * zoom +
                                                  split_coordinates[0]),
                                                  int(display_coord[1] * zoom +
                                                  split_coordinates[1]))
            # if not obj in self.style_settings:
            #    self.update_style(obj)
            # if self.is_visible(obj): # for perspective need
            self.draw_table[type(obj)](obj, painter, zoom, objects_to_highlit)
            self.displayed_objects.append(obj)

    def is_visible(self, obj):
        return self.check_to_visible[type(obj)](obj)

    def set_painter_params(self, painter, pen_color=QtGui.QColor(230, 102, 0),
                           pen_width=5, pen_style=QtCore.Qt.SolidLine,
                           brush_color=QtGui.QColor(230, 102, 30),
                           brush_style=QtCore.Qt.SolidPattern):
        painter.setPen(QtGui.QPen(pen_color, pen_width, pen_style))
        painter.setBrush(QtGui.QBrush(brush_color, brush_style))

    def paint_pt(self, point, painter, zoom, objects_to_highlit):
        self.set_painter_params(painter, pen_color=COLORS[point.color],
                                brush_color=COLORS[point.color])
        painter.drawEllipse(int(self.points_display_table[point][0] -
                            point.WIDTH / 2),
                            int(self.points_display_table[point][1] -
                            point.WIDTH / 2),
                            point.WIDTH, point.WIDTH)

    def paint_ln(self, line, painter, zoom, objects_to_highlit):
        self.set_painter_params(painter, pen_color=COLORS[line.color])
        painter.pen().setWidth(line.WIDTH)
        painter.drawLine(
            *self.points_display_table[line.start],
            *self.points_display_table[line.end])

    def draw_coordinates_system(self, painter):
        painter.setPen(QtGui.QPen(QtCore.Qt.white, self.axiss_width,
                                  QtCore.Qt.SolidLine))
        width = 5
        display_origin = self.model.display_vector(
            self.model.origin.to_vector3())
        display_origin = (int(display_origin[0] + 1200),
                          int(display_origin[1] + 60))
        painter.drawEllipse(int(display_origin[0] - width / 2),
                            int(display_origin[1] - width / 2),
                            width, width)

        painter.setPen(QtGui.QPen(QtCore.Qt.green, self.axiss_width,
                                  QtCore.Qt.DashLine))
        self.draw_axis(painter, self.model.basis[0], display_origin)

        painter.setPen(QtGui.QPen(QtCore.Qt.blue, self.axiss_width,
                                  QtCore.Qt.DashLine))
        self.draw_axis(painter, self.model.basis[1], display_origin)

        painter.setPen(QtGui.QPen(QtCore.Qt.red, self.axiss_width,
                                  QtCore.Qt.DashLine))
        self.draw_axis(painter, self.model.basis[2], display_origin)

        painter.setPen(QtGui.QPen(QtGui.QColor(
            255, 102, 0), 5, QtCore.Qt.SolidLine))

    def draw_axis(self, painter, basis_vector, display_origin):
        width = 5
        temp_point = Point(basis_vector.x * self.axiss_size,
                           basis_vector.y * self.axiss_size,
                           basis_vector.z * self.axiss_size)
        display_coord = self.model.display_vector(
            temp_point.to_vector3())
        display_coord = (int(display_coord[0] + 1200),
                         int(display_coord[1] + 60))
        painter.drawEllipse(int(display_coord[0] - width / 2),
                            int(display_coord[1] - width / 2),
                            width, width)
        painter.drawLine(  # from start to end
            *display_origin,
            *display_coord)
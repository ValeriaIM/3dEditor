import time
from PyQt5 import QtGui, QtWidgets, QtCore
from source import model
from source.algebra import *
from source.figures import *
from editor.drawer import Drawer
import math
from enum import Enum
import logging

RESOLUTION = (1280, 720)

LOGGER_NAME = '3d-editor.editor'
LOGGER = logging.getLogger(LOGGER_NAME)


class Mode(Enum):
    VIEW = 0
    POINT = 1
    LINE = 2
    PLACE = 3


style_sheet = """
            QMenuBar {
                background-color: rgb(220,150,120);
            }

            QMenuBar::item {
                background: rgb(220,150,120);
            }"""


def get_distance(x0, y0, x1, y1):
    return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)


class SceneWindow(QtWidgets.QLabel):
    def __init__(self, window):
        super().__init__(window)

        canvas = QtGui.QPixmap(RESOLUTION[0], RESOLUTION[1])
        canvas.fill(QtGui.QColor('grey'))
        self.setPixmap(canvas)

        self.last_x = 0
        self.last_y = 0
        self.zoom = 1

        self.object_to_interact = None
        self.object_to_modify = None
        self.model = None
        self.drawer = None

        self.origin_coordinates = [640, 360]

    def timerEvent(self, event):
        self.update_statusbar()

    def update_scene_display(self):
        with self.get_painter() as painter:
            self.drawer.update_scene(
                painter, RESOLUTION, self.origin_coordinates, self.zoom)

        self.update_statusbar()

    def get_painter(self):
        return QtGui.QPainter(self.pixmap())

    def update_statusbar(self):
        pos = QtGui.QCursor.pos()
        global_coord = (self.parent().model.display_plate_basis[0] *
                        (pos.x() / self.zoom - self.origin_coordinates[0]) +
                        self.parent().model.display_plate_basis[1] *
                        (pos.y() / self.zoom - self.origin_coordinates[1]))
        self.parent().statusBar().showMessage(
            f'Mode: {str(self.parent().mode)[5:]};' +
            f' x={round(global_coord.x, 1)} ' +
            f' y={round(global_coord.y, 1)} ' +
            f' z={round(global_coord.z, 1)};' +
            f' Zoom: {round(self.zoom, 2)}')

    def mousePressEvent(self, event):
        if self.parent().mode == Mode.POINT:
            self.set_point(event)
        elif self.parent().mode == Mode.LINE:
            self.choose_line_points(event)
        elif self.parent().mode == Mode.PLACE:
            self.choose_place_points(event)

        self.object_to_interact = None
        self.refresh_interaction_variables(event)
        self.parent().update_display()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.parent().mode == Mode.VIEW:
            self.origin_coordinates[0] += event.x() / self.zoom - self.last_x
            self.origin_coordinates[1] += event.y() / self.zoom - self.last_y

        self.refresh_interaction_variables(event)
        self.parent().update_display()

    def refresh_interaction_variables(self, event):
        self.last_x = event.x() / self.zoom
        self.last_y = event.y() / self.zoom

    def set_point(self, event):
        x = self.origin_coordinates[0]
        y = self.origin_coordinates[1]
        self.parent().model.add_point((self.parent(
        ).model.display_plate_basis[0] *
                                       ((event.x() - x) / self.zoom)) +
                                      (self.parent(
                                      ).model.display_plate_basis[1] *
                                       ((event.y() - y) / self.zoom)),
                                      self.drawer.point_color)

    def choose_line_points(self, event):
        self.update_object_to_interact(event)
        if self.object_to_interact and isinstance(self.object_to_interact,
                                                  Point):
            self.parent().buffer.append(self.object_to_interact)
        if len(self.parent().buffer) == 2:
            self.parent().model.add_line(self.parent().buffer[0],
                                         self.parent().buffer[1],
                                         self.drawer.line_color)
            self.parent().buffer = []

    def choose_place_points(self, event):
        self.update_object_to_interact(event)
        obj = self.object_to_interact
        if obj and isinstance(obj, Point):
            parent = self.parent()
            if obj in parent.buffer:
                if len(parent.buffer) >= 3:
                    self.parent().model.add_place(self.parent().buffer,
                                              self.drawer.plane_color)
            else:
                self.parent().buffer.append(self.object_to_interact)

    def update_object_to_interact(self, event):
        self.object_to_interact = None
        for obj in self.drawer.displayed_objects:
            if isinstance(obj, Point):
                distance = self.get_distance_to_point(event, obj)
                if obj.WIDTH > distance:
                    self.object_to_interact = obj
                    break

    def get_distance_to_point(self, event, point):
        return get_distance(event.x(), event.y(),
                            *self.drawer.points_display_table[point])


def set_checkable(action, mode):
    condition = 'Mode.' + action.iconText().upper()
    if action.isChecked() and condition != str(mode):
        action.setCheckable(False)
        action.setCheckable(True)


class RedactorWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.label = None
        self.toolbar = None
        self.mode_menu = None
        self.modifybar = None
        self.model = None
        self.buffer = []
        self.drawer = None

        self.modes = {
            QtCore.Qt.Key_V: Mode.VIEW}

        self.display_axis = True

        rotate_angle = math.pi / 90
        self.rotate_matrix = {
            'xplus': Matrix(3, 3, math.cos(rotate_angle),
                            -math.sin(rotate_angle), 0,
                            math.sin(rotate_angle),
                            math.cos(rotate_angle),
                            0, 0, 0, 1),
            'zplus': Matrix(3, 3, 1, 0, 0, 0,
                            math.cos(rotate_angle),
                            -math.sin(rotate_angle), 0,
                            math.sin(rotate_angle),
                            math.cos(rotate_angle)),
            'zminus': Matrix(3, 3, 1, 0, 0, 0,
                             math.cos(-rotate_angle),
                             -math.sin(-rotate_angle), 0,
                             math.sin(-rotate_angle),
                             math.cos(-rotate_angle)),
            'xminus': Matrix(3, 3, math.cos(-rotate_angle),
                             -math.sin(-rotate_angle), 0,
                             math.sin(-rotate_angle),
                             math.cos(-rotate_angle),
                             0, 0, 0, 1),
            'yminus': Matrix(3, 3, math.cos(rotate_angle), 0,
                             math.sin(rotate_angle), 0, 1, 0,
                             -math.sin(rotate_angle), 0,
                             math.cos(rotate_angle)),
            'yplus': Matrix(3, 3, math.cos(-rotate_angle), 0,
                            math.sin(-rotate_angle), 0, 1, 0,
                            -math.sin(-rotate_angle), 0,
                            math.cos(-rotate_angle))
        }

        self.mode = Mode.VIEW
        self.init_GUI()
        self.init_new_model()

    def init_GUI(self):
        self.setGeometry(0, 0, RESOLUTION[0], RESOLUTION[1])
        icon = QtGui.QIcon('pictures/icon.png')
        self.setWindowIcon(icon)
        self.setWindowTitle('3D-editor')

        menubar = self.menuBar()
        menubar.setStyleSheet(style_sheet)

        rotations = menubar.addMenu('Rotates')
        actions_rotate = self.get_actions_rotate()
        for action_rotate in actions_rotate:
            rotations.addAction(action_rotate)

        self.mode_menu = menubar.addMenu('Modes')
        actions_mode = self.get_actions_mode()
        for action_mode in actions_mode:
            action_mode.setCheckable(True)
            self.mode_menu.addAction(action_mode)

        self.toolbar = QtWidgets.QToolBar(self)
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbar)
        actions_figures = self.get_actions_figures()
        for action_figures in actions_figures:
            action_figures.setCheckable(True)
            self.toolbar.addAction(action_figures)

        self.modifybar = QtWidgets.QToolBar(self)
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.modifybar)

        self.statusBar()

        self.label = SceneWindow(self)
        self.setCentralWidget(self.label)

    def get_actions_rotate(self):
        action_rotate_x_add = self.new_action(
            'X+', lambda _: self.rotate('xplus'), shortcut='S')
        action_rotate_x_sub = self.new_action(
            'X-', lambda _: self.rotate('xminus'), shortcut='W')
        action_rotate_y_add = self.new_action(
            'Y+', lambda _: self.rotate('yplus'), shortcut='A')
        action_rotate_y_sub = self.new_action(
            'Y-', lambda _: self.rotate('yminus'), shortcut='D')
        action_rotate_z_add = self.new_action(
            'Z+', lambda _: self.rotate('zplus'), shortcut='R')
        action_rotate_z_sub = self.new_action(
            'Z-', lambda _: self.rotate('zminus'), shortcut='Shift+R')
        return (action_rotate_x_add, action_rotate_x_sub,
                action_rotate_y_add, action_rotate_y_sub,
                action_rotate_z_add, action_rotate_z_sub)

    def get_actions_figures(self):
        action_point = self.new_action(
            'Point', lambda _: self.set_mode(Mode.POINT),
            'pictures/point.png', '1')
        action_line = self.new_action(
            'Line', lambda _: self.set_mode(Mode.LINE),
            'pictures/line.png', '2')
        action_place = self.new_action(
            'Place', lambda _: self.set_mode(Mode.PLACE),
            'pictures/plate.png', '3')
        return action_point, action_line, action_place

    def get_actions_mode(self):
        action_mode_view = self.new_action(
            'View', lambda _: self.set_mode(Mode.VIEW), shortcut='V')
        return action_mode_view, action_mode_view

    def new_action(self, name, connect_with, icon=None, shortcut=None):
        action = QtWidgets.QAction(
            QtGui.QIcon(icon), name, self)
        action.triggered.connect(connect_with)
        if shortcut:
            action.setShortcut(shortcut)
        return action

    def update_display(self):
        self.label.update_scene_display()
        self.update()

    def set_mode(self, mode: Mode):
        if self.mode == Mode.PLACE and len(self.buffer) > 2:
            self.model.add_place(self.buffer,
                                 self.label.drawer.plane_color)
        self.buffer = []
        self.mode = mode
        for action in self.toolbar.actions():
            set_checkable(action, mode)
        for action in self.mode_menu.actions():
            set_checkable(action, mode)
        self.update_display()

    def rotate(self, axis):
        self.model.update_display_matrix(self.rotate_matrix[axis])
        self.update_display()

    def init_new_model(self):
        del self.model
        self.model = model.Model()
        self.label.drawer = Drawer(self.model)
        self.label.zoom = 1
        self.update_display()

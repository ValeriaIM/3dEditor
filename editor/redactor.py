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

LOGGER_NAME = '3d-editor.redactor'
LOGGER = logging.getLogger(LOGGER_NAME)

class Mode(Enum):
    VIEW = 0
    EDIT = 1
    POINT = 2
    LINE = 3


class SceneWindow(QtWidgets.QLabel):
    def __init__(self, window):
        super().__init__(window)

        canvas = QtGui.QPixmap(RESOLUTION[0], RESOLUTION[1])
        canvas.fill(QtGui.QColor('grey'))
        self.setPixmap(canvas)

        self.last_x = 0
        self.last_y = 0
        self.zoom = 1
        self.last_time_clicked = time.time()
        self.forget_object_delay = 0.15
        self.object_to_interact = None

        self.split_coordinates = [640, 360]

        self.drawer = None
        self.style_preset = 81

        self.startTimer(20)

    def timerEvent(self, event):
        self.update_statusbar()

    def update_scene_display(self):
        with self.get_painter() as painter:
            self.drawer.update_scene(
                painter, RESOLUTION, self.split_coordinates, self.zoom)

        self.update_statusbar()

    def get_painter(self):
        return QtGui.QPainter(self.pixmap())

    def update_statusbar(self):
        pos = QtGui.QCursor.pos()
        global_coord = (self.parent().model.display_plate_basis[0] *
                        (self.calc_x(pos.x()) - self.split_coordinates[0]) +
                        self.parent().model.display_plate_basis[1] *
                        (self.calc_y(pos.y()) - self.split_coordinates[1]))
        self.parent().statusBar().showMessage(
            f'Mode: {str(self.parent().mode)[5:]};' +
            f' x={round(global_coord.x, 1)} ' +
            f'y={round(global_coord.y, 1)} z={round(global_coord.z, 1)};' +
            f' Zoom: {round(self.zoom, 2)}')

    def mousePressEvent(self, event):
        if self.parent().mode == Mode.POINT:
            self.set_point(event)
        elif self.parent().mode == Mode.LINE:
            self.choose_line_points(event)

        self.object_to_interact = None
        self.refresh_interaction_variables(event)
        self.parent().update_display()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.parent().mode == Mode.VIEW:
            self.split_coordinates[0] += self.calc_x(event.x()) - self.last_x
            self.split_coordinates[1] += self.calc_y(event.y()) - self.last_y
        elif self.parent().mode == Mode.EDIT:
            self.edit_object(event)

        self.refresh_interaction_variables(event)
        self.parent().update_display()

    def calc_x(self, x):
        return x / self.zoom

    def calc_y(self, y):
        return y / self.zoom

    def refresh_interaction_variables(self, event):
        self.last_x = self.calc_x(event.x())
        self.last_y = self.calc_y(event.y())
        self.last_time_clicked = time.time()

    def set_point(self, event):
        self.parent().model.add_point((self.parent(
        ).model.display_plate_basis[0] *
                                       (self.calc_x(event.x() -
                                                    self.split_coordinates[0]))) +
                                      (self.parent(
                                      ).model.display_plate_basis[1] *
                                       (self.calc_y(event.y() -
                                                    self.split_coordinates[1]))),
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

    def choose_object_to_modify(self, event):
        self.update_object_to_interact(event)
        self.object_to_modify = self.object_to_interact
        self.parent().update_modifybar()

    def edit_object(self, event):
        if (self.object_to_interact and time.time() - self.last_time_clicked <
                self.forget_object_delay):  # maybe need more
            self.object_to_interact + (
                    self.parent().model.display_plate_basis[0] *
                    (self.calc_x(event.x()) - self.last_x) +
                    self.parent().model.display_plate_basis[1] *
                    (self.calc_y(event.y()) - self.last_y))
        else:
            self.update_object_to_interact(event)

    # can we interact with poly or line ?... hmmm
    def update_object_to_interact(self, event):
        self.object_to_interact = None
        for obj in self.drawer.displayed_objects:
            if isinstance(obj, Point):
                distance = self.get_distance_to_point(event, obj)
                if obj.WIDTH > distance:
                    self.object_to_interact = obj
                    break
            elif isinstance(obj, Line):
                distance = self.get_distance_to_line(event, obj)
                if obj.WIDTH > distance:
                    self.object_to_interact = obj
                    break

    def get_distance(self, x0, y0, x1, y1):
        return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)

    def get_distance_to_point(self, event, point):
        return self.get_distance(event.x(), event.y(),
                                 *self.drawer.points_display_table[point])

    def get_distance_to_line(self, event, line):
        return (self.get_distance_to_point(event, line.start) +
                self.get_distance_to_point(event, line.end) -
                self.get_distance(
                    *self.drawer.points_display_table[line.start],
                    *self.drawer.points_display_table[line.end]))

class RedactorWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = None
        self.buffer = []
        self.drawer = None

        self.modes = {
            QtCore.Qt.Key_Q: Mode.EDIT,
            QtCore.Qt.Key_E: Mode.VIEW,
            QtCore.Qt.Key_L: Mode.LINE}

        self.display_axiss = True

        rotate_angle = math.pi / 90
        self.rotate_matrixes = {
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
        self.setGeometry(0, 0, RESOLUTION[0], RESOLUTION[1])  # x y wide tall
        icon = QtGui.QIcon('pictures/icon.png')
        self.setWindowIcon(icon)
        self.setWindowTitle('Black Box editor')

        rotate_xplus_action = self.new_action(
            '', lambda _: self.rotate('xplus'), shortcut='S')
        rotate_xminus_action = self.new_action(
            '', lambda _: self.rotate('xminus'), shortcut='W')
        rotate_yplus_action = self.new_action(
            '', lambda _: self.rotate('yplus'), shortcut='A')
        rotate_yminus_action = self.new_action(
            '', lambda _: self.rotate('yminus'), shortcut='D')
        rotate_zplus_action = self.new_action(
            '', lambda _: self.rotate('zplus'), shortcut='R')
        rotate_zminus_action = self.new_action(
            '', lambda _: self.rotate('zminus'), shortcut='Shift+R')

        point_action = self.new_action(
            'Point', lambda _: self.set_mode(Mode.POINT),
            'pictures/point.png', '1')
        line_action = self.new_action(
            'Line', lambda _: self.set_mode(Mode.LINE),
            'pictures/line.png', '2')
        edit_mode = self.new_action(
            'Edit', lambda _: self.set_mode(Mode.EDIT), shortcut='Q')
        view_mode = self.new_action(
            'View', lambda _: self.set_mode(Mode.VIEW), shortcut='E')

        menubar = self.menuBar()
        menubar.setStyleSheet("""QMenuBar {
                 background-color: rgb(220,150,120);
                }

             QMenuBar::item {
                 background: rgb(220,150,120);
             }""")
        rotations = menubar.addMenu('')
        rotations.addAction(rotate_xplus_action)
        rotations.addAction(rotate_yplus_action)
        rotations.addAction(rotate_zplus_action)
        rotations.addAction(rotate_xminus_action)
        rotations.addAction(rotate_yminus_action)
        rotations.addAction(rotate_zminus_action)
        menubar.setStyleSheet("""QMenuBar {
         background-color: rgb(220,150,120);
        }
     QMenuBar::item {
         background: rgb(220,150,120);
     }""")
        rotations = menubar.addMenu('')
        fileMenu = menubar.addMenu('Scene')
        settings = menubar.addMenu('Settings')
        pt_settings = settings.addMenu('Point')
        ln_settings = settings.addMenu('Line')
        self.mode_menu = menubar.addMenu('Modes')
        edit_mode.setCheckable(True)
        view_mode.setCheckable(True)

        self.toolbar = QtWidgets.QToolBar(self)
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbar)
        point_action.setCheckable(True)
        line_action.setCheckable(True)
        self.toolbar.addAction(point_action)
        self.toolbar.addAction(line_action)

        self.modifybar = QtWidgets.QToolBar(self)
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.modifybar)
        self.statusBar()

        self.label = SceneWindow(self)
        self.setCentralWidget(self.label)

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

    def set_mode(self, mode: Mode):  # deconstructors for modes
        self.buffer = []
        self.mode = mode
        for action in self.toolbar.actions():
            if action.isChecked() and 'Mode.' + action.iconText().upper() != str(mode):
                action.setCheckable(False)
                action.setCheckable(True)
        for action in self.mode_menu.actions():
            if action.isChecked() and 'Mode.' + action.iconText().upper() != str(mode):
                action.setCheckable(False)
                action.setCheckable(True)
        self.update_display()

    def rotate(self, axis):
        self.model.update_display_matrix(self.rotate_matrixes[axis])
        self.update_display()

    def init_new_model(self):
        del (self.model)
        self.model = model.Model()
        self.label.drawer = Drawer(self.model)
        self.label.zoom = 1
        self.update_display()

import time

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QPoint

from source import model
from source.algebra import *
from source.figures import *
from editor.drawer import Drawer
import math
from enum import Enum
import logging
import sys

RESOLUTION = (1280, 720)

LOGGER_NAME = '3d-editor.editor'
LOGGER = logging.getLogger(LOGGER_NAME)

ERROR_DRAW_OBJ = 6
ERROR_SAVE = 7
ERROR_SCREEN = 8
ERROR_OPEN = 9


class Mode(Enum):
    VIEW = 0
    EDIT = 1
    POINT = 2
    LINE = 3
    PLACE = 4
    ELLIPSE = 5


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

        self.last_time_clicked = time.time()
        self.forget_object_delay = 0.05

        self.object_to_interact = None
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
        try:
            if self.parent().mode == Mode.POINT:
                self.set_point(event)
                LOGGER.info('point has been added')
            elif self.parent().mode == Mode.LINE:
                self.choose_line_points(event)
                LOGGER.info('line has been added')
            elif self.parent().mode == Mode.PLACE:
                self.choose_place_points(event)
                LOGGER.info('place has been added')
            elif self.parent().mode == Mode.ELLIPSE:
                self.choose_ellipse_points(event)
                LOGGER.info('ellipse has been added')
        except Exception as e:
            import traceback
            LOGGER.error('Error: %s\n%s', e,
                         ''.join(traceback.format_tb(sys.exc_info()[-1])))
            print(e, file=sys.stderr)
            sys.exit(ERROR_DRAW_OBJ)

        self.object_to_interact = None
        self.refresh_interaction_variables(event)
        self.parent().update_display()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.parent().mode == Mode.VIEW:
            self.origin_coordinates[0] += event.x() / self.zoom - self.last_x
            self.origin_coordinates[1] += event.y() / self.zoom - self.last_y
        elif self.parent().mode == Mode.EDIT:
            self.edit_object(event)

        self.refresh_interaction_variables(event)

        self.parent().update_display()

    def refresh_interaction_variables(self, event):
        self.last_x = event.x() / self.zoom
        self.last_y = event.y() / self.zoom
        self.last_time_clicked = time.time()

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
                self.parent().buffer.append(obj)

    def choose_ellipse_points(self, event):
        self.update_object_to_interact(event)
        obj = self.object_to_interact
        if obj and isinstance(obj, Point):
            self.parent().buffer.append(obj)
        if len(self.parent().buffer) == 2:
            self.parent().model.add_ellipse(self.parent().buffer[0],
                                            self.parent().buffer[1],
                                            self.drawer.ellipse_color)
            self.parent().buffer = []

    def edit_object(self, event):
        if self.object_to_interact:
            if time.time() - self.last_time_clicked < self.forget_object_delay:
                self.object_to_interact + (
                        self.parent().model.display_plate_basis[0] *
                        (event.x() / self.zoom - self.last_x) +
                        self.parent().model.display_plate_basis[1] *
                        (event.y() / self.zoom - self.last_y))
        else:
            self.update_object_to_interact(event)

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
            elif isinstance(obj, Place):
                is_inside = self.is_inside_place(event, obj)
                if is_inside:
                    self.object_to_interact = obj
                    break
            elif isinstance(obj, Ellipse):
                is_inside = self.is_inside_ellipse(event, obj)
                if is_inside:
                    self.object_to_interact = obj
                    break

    def get_distance_to_point(self, event, point):
        return get_distance(event.x(), event.y(),
                            *self.drawer.points_display_table[point])

    def get_distance_to_line(self, event, line):
        return (self.get_distance_to_point(event, line.start) +
                self.get_distance_to_point(event, line.end) -
                get_distance(
                    *self.drawer.points_display_table[line.start],
                    *self.drawer.points_display_table[line.end]))

    def is_inside_place(self, event, place):
        num_points = len(place.points)
        x, y = event.x(), event.y()
        sign = None

        for i in range(num_points):
            p1 = place.points[i]
            p2 = place.points[(i + 1) % num_points]
            x1, y1 = self.drawer.points_display_table[p1]
            x2, y2 = self.drawer.points_display_table[p2]

            # вычисляем векторы стороны и вектор до точки
            vx, vy = x2 - x1, y2 - y1
            wx, wy = x - x1, y - y1

            # выч-м знак векторного произведения
            cross_product = vx * wy - vy * wx

            if sign is None:
                sign = cross_product
            elif cross_product != 0 and cross_product * sign < 0:
                return False

        return True

    def is_inside_ellipse(self, event, ellipse):
        is_inside = self.check_ellipse(event, ellipse)
        if is_inside:
            return True

        if ellipse.extra_el:
            for el in ellipse.extra_el:
                is_inside = self.check_ellipse(event, el)
                if is_inside:
                    return True
        else:
            return False

    def check_ellipse(self, event, ellipse):
        x, y = event.x(), event.y()
        x1, y1 = 0, 0
        x2, y2 = 0, 0
        if isinstance(ellipse.topLeft, QPoint):
            x1, y1 = ellipse.topLeft.x(), ellipse.topLeft.y()
            x2, y2 = ellipse.bottomRight.x(), ellipse.bottomRight.y()
        else:
            x1, y1 = self.drawer.points_display_table[ellipse.topLeft]
            x2, y2 = self.drawer.points_display_table[ellipse.bottomRight]
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        a = (x2 - x1) / 2
        b = (y2 - y1) / 2
        d = math.sqrt(((x - cx) / a) ** 2 + ((y - cy) / b) ** 2)
        return d < 1

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

        self.rotate_matrix = self.get_initial_rotate_matrix()

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

        self.add_Menus(menubar)

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

    def get_initial_rotate_matrix(self):
        rotate_angle = math.pi / 90
        rotate_matrix = {
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
        return rotate_matrix

    def add_Menus(self, menubar):
        file = menubar.addMenu('File')
        actions_file = self.get_actions_file()
        for action_file in actions_file:
            file.addAction(action_file)

        rotations = menubar.addMenu('Rotates')
        actions_rotate = self.get_actions_rotate()
        for action_rotate in actions_rotate:
            rotations.addAction(action_rotate)

        self.mode_menu = menubar.addMenu('Modes')
        actions_mode = self.get_actions_mode()
        for action_mode in actions_mode:
            action_mode.setCheckable(True)
            self.mode_menu.addAction(action_mode)

    def get_actions_file(self):
        action_new = self.new_action(
            'New', self.init_new_model, shortcut='Ctrl+N')
        action_save = self.new_action(
            'Save', self.save_model, shortcut='Ctrl+S')
        screen_action = self.new_action(
            'Save scr', self.screenshot, shortcut='Ctrl+Shift+S')
        action_open = self.new_action(
            'Open', self.open_model, shortcut='Ctrl+O')
        return action_new, action_save, screen_action, action_open

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
        action_ellipse = self.new_action(
            'Ellipse', lambda _: self.set_mode(Mode.ELLIPSE),
            'pictures/ellipse.png', '4'
        )
        return action_point, action_line, action_place, action_ellipse

    def get_actions_mode(self):
        action_mode_view = self.new_action(
            'View', lambda _: self.set_mode(Mode.VIEW), shortcut='V')
        action_mode_edit = self.new_action(
            'Edit', lambda _: self.set_mode(Mode.EDIT), shortcut='E')
        return action_mode_view, action_mode_edit

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

    def save_model(self):  # show the window where we can write filename
        if not self.model:
            return
        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self, 'save')
        if not ok:
            return
        LOGGER.info('model is saving')
        try:
            with open(filename, 'w', encoding='utf8') as file:
                self.model.save(file)
        except OSError as e:
            import traceback
            LOGGER.error('Error: %s\n%s', e,
                         ''.join(traceback.format_tb(sys.exc_info()[-1])))
            print(e, file=sys.stderr)
            sys.exit(ERROR_SAVE)
            QtWidgets.QMessageBox.about(self, 'Error', 'OSError')
        LOGGER.info('model has been saved')
        self.update_display()

    def screenshot(self):
        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self,
                                                             'save',
                                                             'screen.png')
        if not ok:
            return
        screen = QtWidgets.QApplication.primaryScreen()
        if not filename.endswith('.png') and not filename.endswith('.bmp'):
            filename += '.png'
        LOGGER.info('screenshot is saving')
        try:
            screen.grabWindow(self.winId()).save(filename, 'png')
        except PermissionError as e:
            import traceback
            LOGGER.error('Error: %s\n%s', e,
                         ''.join(traceback.format_tb(sys.exc_info()[-1])))
            print(e, file=sys.stderr)
            sys.exit(ERROR_SCREEN)
            QtWidgets.QMessageBox.about(self, 'Error', 'Permission Error')
        LOGGER.info('screenshot has been saved')

    def open_model(self):
        filename, ok = QtWidgets.QFileDialog.getOpenFileName(self, 'open')
        if not ok:
            return
        self.model = model.Model()
        LOGGER.info('model is opening')
        try:
            with open(filename, 'r', encoding='utf8') as file:
                self.model.open(file)
        except OSError as e:
            import traceback
            LOGGER.error('Error: %s\n%s', e,
                         ''.join(traceback.format_tb(sys.exc_info()[-1])))
            print(e, file=sys.stderr)
            sys.exit(ERROR_OPEN)
            QtWidgets.QMessageBox.about(self, 'Error', 'Error')
        self.label.drawer = Drawer(self.model)
        self.update_display()
        LOGGER.info('model has been opened')

    def rotate(self, axis):
        self.model.update_display_matrix(self.rotate_matrix[axis])
        self.update_display()

    def init_new_model(self):
        del self.model
        self.model = model.Model()
        self.label.drawer = Drawer(self.model)
        self.label.zoom = 1
        self.buffer = []
        self.set_mode(Mode.VIEW)
        self.update_display()

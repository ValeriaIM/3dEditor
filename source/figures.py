import math

from .algebra import Vector3
from enum import Enum


class Color(Enum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4


class Point:
    WIDTH = 10
    NAME = 'Point'

    def __init__(self, x: int, y: int, z: int,
                 color=Color.BLACK,
                 width=WIDTH):
        self.x = x
        self.y = y
        self.z = z
        self.color = color
        self.WIDTH = width

    def __add__(self, other):
        if isinstance(other, Vector3):
            self.x += other.x
            self.y += other.y
            self.z += other.z

    def distance_to_viewer(self, model):
        display_p = model.display_vector(self.to_vector3())
        return int(display_p[2])

    def to_vector3(self):
        return Vector3(self.x, self.y, self.z)

    def to_dict(self):
        return {"name": self.NAME,
                "x": self.x,
                "y": self.y,
                "z": self.z,
                "color": self.color.value,
                "width": self.WIDTH}

    # Нужно во время отладки
    def __str__(self):
        return f'pt,{int(self.x)},{int(self.y)},{int(self.z)}'

    def __hash__(self):
        return hash((self.x, self.y, self.x))

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y and self.z == other.z

    # Пока не актуально
    def close_equal(self, point):
        return abs(self.x - point.x) < 1e-5 and \
               abs(self.y - point.y) < 1e-5 and \
               abs(self.z - point.z) < 1e-5


class Line:
    WIDTH = 5
    NAME = 'Line'

    def __init__(self, start: Point, end: Point,
                 color=Color.BLACK,
                 width=WIDTH):
        self.start = start
        self.end = end
        self.color = color
        self.WIDTH = width

    def __add__(self, other):
        if isinstance(other, Vector3):
            self.start + other
            self.end + other

    # Нужно во время отладки
    def __str__(self):
        return f'ln!|{str(self.start)}||{str(self.end)}|'

    def to_dict(self):
        return {"name": self.NAME,
                "start": self.start.to_dict(),
                "end": self.end.to_dict(),
                "color": self.color.value,
                "width": self.WIDTH}

    def distance_to_viewer(self, model):
        points = [self.start, self.end]
        z_min = None
        for point in points:
            display_p = model.display_vector(point.to_vector3())
            if z_min is None:
                z_min = display_p[2]
            if z_min < display_p[2]:
                z_min = display_p[2]

        return z_min


class Place:
    WIDTH = 5
    NAME = 'Place'

    def __init__(self, points,
                 color=Color.BLACK,
                 width=WIDTH):
        if points:
            self.points = [point for point in points]
        self.color = color
        self.WIDTH = width

    def __add__(self, other):
        if isinstance(other, Vector3):
            for point in self.points:
                point + other

    def __str__(self):
        str_place = 'pl!'
        for point in self.points:
            str_place += f'|{str(point)}|'
        return str_place

    def to_dict(self):
        return {"name": self.NAME,
                "points": [point.to_dict() for point in self.points],
                "color": self.color.value,
                "width": self.WIDTH}

    def distance_to_viewer(self, model):
        z_min = None
        for point in self.points:
            display_p = model.display_vector(point.to_vector3())
            if z_min is None:
                z_min = display_p[2]
            if z_min < display_p[2]:
                z_min = display_p[2]

        return z_min

class Ellipse:
    WIDTH = 5
    NAME = 'Ellipse'

    def __init__(self, topLeft: Point, bottomRight: Point,
                 color=Color.BLACK, width=WIDTH):
        self.rx = None
        self.ry = None
        self.WIDTH = width
        self.extra_el = []

        if topLeft and bottomRight:
            self.topLeft = topLeft
            self.bottomRight = bottomRight
        self.color = color

    def set_move_info(self, rx: int, ry: int):
        self.rx = rx
        self.ry = ry

    def add_extra_el(self, el):
        self.extra_el.append(el)

    def __add__(self, other):
        if isinstance(other, Vector3):
            self.topLeft + other
            self.bottomRight + other
            self.rx = None
            self.ry = None

    def __str__(self):
        str_el = 'el!'
        str_el += f'|{str(self.pt_topLeft)}|'
        str_el += f'|{str(self.pt_bottomRight)}|'
        return str_el

    def to_dict(self):
        return {"name": self.NAME,
                "topLeft": self.topLeft.to_dict(),
                "bottomRight": self.bottomRight.to_dict(),
                "rx": self.rx,
                "ry": self.ry,
                "color": self.color.value,
                "width": self.WIDTH}

    def distance_to_viewer(self, model):
        points = [self.topLeft, self.bottomRight]
        for el in self.extra_el:
            points.append(el.topLeft)
            points.append(el.bottomRight)
        z_min = None
        for point in self.points:
            display_p = model.display_vector(point.to_vector3())
            if z_min is None:
                z_min = display_p[2]
            if z_min < display_p[2]:
                z_min = display_p[2]

        return z_min

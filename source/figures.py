from .algebra import Vector3
import json

from enum import Enum


class Color(Enum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3


class Point():
    WIDTH = 10
    NAME = 'Point'

    def __init__(self, x: int, y: int, z: int,
                 color=Color.GREEN):
        self.x = x
        self.y = y
        self.z = z
        self.color = color

    def __add__(self, other):
        if isinstance(other, Vector3):
            self.x += other.x
            self.y += other.y
            self.z += other.z

    def to_vector3(self):
        return Vector3(self.x, self.y, self.z)

    def __str__(self):
        return f'pt,{int(self.x)},{int(self.y)},{int(self.z)}'

    def set_style(self, drawer):
        self.color = drawer.point_color

    def almost_equal(self, point):
        return abs(self.x - point.x) < 1e-5 and \
               abs(self.y - point.y) < 1e-5 and \
               abs(self.z - point.z) < 1e-5

    @staticmethod
    def from_string(str_representation, objects=None):
        params = str_representation.split(',')
        return Point(float(params[1]), float(params[2]),
                     float(params[3]))

    @staticmethod
    def from_dict(obj_dict):
        point = Point(None, None, None)
        point.initialize(obj_dict)
        return point


class Line():
    WIDTH = 5
    NAME = 'Line'

    def __init__(self, start: Point, end: Point,
                 color=Color.BLACK):
        self.start = start
        self.end = end
        self.color = color

    def get_guide_vector(self):
        return Vector3(self.end.x - self.start.x,
                       self.end.y - self.start.y,
                       self.end.z - self.start.z)

    def is_inside_line(self, vector: Vector3) -> bool:
        if not vector:
            return False
        return abs(Vector3.distance(self.start.to_vector3(),
                                    self.end.to_vector3()) -
                   Vector3.distance(self.start.to_vector3(), vector) -
                   Vector3.distance(self.end.to_vector3(), vector)) < 1e-8

    def __add__(self, other):
        if isinstance(other, Vector3):
            self.start + other
            self.end + other

    def __str__(self):
        return f'ln!|{str(self.start)}||{str(self.end)}|'

    def extra_initialize(self, objects):
        start = Point.from_dict(self.start)
        end = Point.from_dict(self.end)

        self.start = None
        self.end = None

        self.color = Color(self.color)

        for obj in objects:
            if self.start and self.end:
                return
            if not self.start and str(start) == str(obj):
                self.start = obj
            if not self.end and str(end) == str(obj):
                self.end = obj

    def set_style(self, drawer):
        self.color = drawer.line_color
        self.style = drawer.line_style

    @staticmethod
    def from_string(str_representation: str, objects):
        str_points = str_representation.split('|')
        points = []
        for obj in objects:
            if (str(obj) == str_points[1] or
                    str(obj) == str_points[3]):
                points.append(obj)
        return Line(points[0], points[1])

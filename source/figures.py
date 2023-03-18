from .algebra import Vector3
from enum import Enum


class Color(Enum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3


class Point:
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

    # Нужно во время отладки
    def __str__(self):
        return f'pt,{int(self.x)},{int(self.y)},{int(self.z)}'

    # Пока не актуально
    def close_equal(self, point):
        return abs(self.x - point.x) < 1e-5 and \
               abs(self.y - point.y) < 1e-5 and \
               abs(self.z - point.z) < 1e-5


class Line:
    WIDTH = 5
    NAME = 'Line'

    def __init__(self, start: Point, end: Point,
                 color=Color.BLACK):
        self.start = start
        self.end = end
        self.color = color

    def __add__(self, other):
        if isinstance(other, Vector3):
            for point in self.points:
                point + other

    # Нужно во время отладки
    def __str__(self):
        return f'ln!|{str(self.start)}||{str(self.end)}|'


class Place:
    WIDTH = 5
    Name = 'Place'

    def __init__(self, points,
                 color=Color.GREEN):
        if points:
            self.points = [point for point in points]
        self.color = color

    def __str__(self):
        str_place = 'pl!'
        for point in self.points:
            str_place += f'|{str(point)}|'
        return str_place

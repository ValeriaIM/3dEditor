from .algebra import *
from .figures import *
from enum import Enum


class Color(Enum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3


class Model:
    def __init__(self):
        self.matrix_of_display = None
        self.display_plate_basis = None
        self.basis = (Vector3(1, 0, 0), Vector3(0, 1, 0), Vector3(0, 0, 1))
        self.origin = Point(0, 0, 0)
        self.init_display_settings()
        self.objects = []

    def init_display_settings(self):
        self.display_plate_basis = [Vector3(0, 0, 1),
                                    Vector3(0, 1, 0),
                                    Vector3(1, 0, 0)]
        self.matrix_of_display = None
        self.update_display_matrix(None)

    def add_point(self, vector, color=Color.GREEN):
        if isinstance(vector, Vector3):
            self.objects.append(Point(vector.x, vector.y, vector.z, color))
        elif isinstance(vector, Point):
            self.objects.append(vector)

    def add_line(self, point1, point2, color):
        self.objects.append(Line(point1, point2, color))

    def add_place(self, points, color):
        self.objects.append(Place(points, color))

    def add_ellipse(self, point1, point2, color):
        self.objects.append(Ellipse(point1, point2, color))

    def display_vector(self, vector: Vector3) -> tuple:
        return (self.matrix_of_display * vector).to_tuple()

    def update_display_matrix(self, ort_matrix: Matrix):
        if not ort_matrix:
            a, b, c = self.display_plate_basis
            self.matrix_of_display = Matrix(
                3, 3, a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z)
        else:
            self.display_plate_basis[0] = Vector3(
                *((ort_matrix * self.display_plate_basis[0]).to_tuple()))
            self.display_plate_basis[1] = Vector3(
                *((ort_matrix * self.display_plate_basis[1]).to_tuple()))
            self.display_plate_basis[2] = Vector3(
                *((ort_matrix * self.display_plate_basis[2]).to_tuple()))
            self.update_display_matrix(None)

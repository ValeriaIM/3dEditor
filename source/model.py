from .algebra import *
from .figures import *
from enum import Enum
import json


class Color(Enum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4


class Model:
    def __init__(self):
        self.matrix_of_display = None
        self.display_plate_basis = None
        self.basis = (Vector3(1, 0, 0), Vector3(0, 1, 0), Vector3(0, 0, 1))
        self.origin = Point(0, 0, 0)
        self.init_display_settings()
        self.figures = []

    def init_display_settings(self):
        self.display_plate_basis = [Vector3(0, 0, 1),
                                    Vector3(0, 1, 0),
                                    Vector3(1, 0, 0)]
        self.matrix_of_display = None
        self.update_display_matrix(None)

    def add_point(self, vector, color=Color.GREEN):
        if isinstance(vector, Vector3):
            self.figures.append(Point(vector.x, vector.y, vector.z, color))
        elif isinstance(vector, Point):
            self.figures.append(vector)

    def add_line(self, point1, point2, color):
        self.figures.append(Line(point1, point2, color))

    def add_place(self, points, color):
        self.figures.append(Place(points, color))

    def add_ellipse(self, point1, point2, color):
        self.figures.append(Ellipse(point1, point2, color))

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

    def save(self, file):
        file.write(str(self))

    def __str__(self):
        description = f'''{json.dumps([vector.to_dict() for vector in self.basis])}
                          {json.dumps(self.origin.to_dict())}
                          {json.dumps([vector.to_dict() for vector in self.display_plate_basis])}
                       '''
        for obj in self.figures:
            description += f'{json.dumps(obj.to_dict())}\n'
        return description

    def open(self, file):
        data = file.read()
        lines = data.strip().split('\n')

        basis_data = json.loads(lines[0])
        self.basis = [Vector3(**v_dict) for v_dict in basis_data]

        origin_data = json.loads(lines[1])
        del origin_data['name']
        origin_data['color'] = Color(origin_data['color'])
        self.origin = Point(**origin_data)

        display_plate_basis_data = json.loads(lines[2])
        self.display_plate_basis = [Vector3(**v_dict) for v_dict in display_plate_basis_data]

        for line in lines[3:]:
            figure_dict = json.loads(line)
            figure_name = figure_dict.pop('name')
            if figure_name == 'Point':
                figure_dict['color'] = Color(figure_dict['color'])
                figure = Point(**figure_dict)
            elif figure_name == 'Line':
                del figure_dict['start']['name']
                figure_dict['start']['color'] = Color(figure_dict['start']['color'])
                del figure_dict['end']['name']
                figure_dict['end']['color'] = Color(figure_dict['end']['color'])

                figure_dict['start'] = Point(**figure_dict['start'])
                figure_dict['end'] = Point(**figure_dict['end'])

                figure_dict['color'] = Color(figure_dict['color'])

                figure = Line(**figure_dict)
            elif figure_name == 'Place':
                points = []
                for point_data in figure_dict['points']:
                    del point_data['name']
                    point_data['color'] = Color(point_data['color'])
                    point = Point(**point_data)
                    points.append(point)

                figure_dict['points'] = points
                figure_dict['color'] = Color(figure_dict['color'])

                figure = Place(**figure_dict)
            elif figure_name == 'Ellipse':
                del figure_dict['topLeft']['name']
                figure_dict['topLeft']['color'] = Color(figure_dict['topLeft']['color'])
                del figure_dict['bottomRight']['name']
                figure_dict['bottomRight']['color'] = Color(figure_dict['bottomRight']['color'])

                figure_dict['topLeft'] = Point(**figure_dict['topLeft'])
                figure_dict['bottomRight'] = Point(**figure_dict['bottomRight'])

                figure_dict['color'] = Color(figure_dict['color'])
                rx = figure_dict.pop('rx')
                ry = figure_dict.pop('ry')

                figure = Ellipse(**figure_dict)
                figure.set_move_info(rx, ry)
            else:
                raise ValueError(f"Unknown figure name: {figure_name}")
            self.figures.append(figure)

        self.update_display_matrix(None)

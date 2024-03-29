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
        self.viewer_position = Vector3(0, 0, 2000)

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
        info = f'''{json.dumps([vector.to_dict() for vector in self.basis])}
        {json.dumps(self.origin.to_dict())}
        {json.dumps([vector.to_dict() for vector in self.display_plate_basis])}
        '''
        for obj in self.figures:
            info += f'{json.dumps(obj.to_dict())}\n'
        return info

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
        self.display_plate_basis = [Vector3(**v_dict) for
                                    v_dict in display_plate_basis_data]

        for line in lines[3:]:
            figure_dict = json.loads(line)
            figure_name = figure_dict.pop('name')
            if figure_name == 'Point':
                figure_dict['color'] = Color(figure_dict['color'])
                figure = Point(**figure_dict)
            elif figure_name == 'Line':
                del figure_dict['start']['name']
                color = Color(figure_dict['start']['color'])
                figure_dict['start']['color'] = color
                del figure_dict['end']['name']
                color = Color(figure_dict['end']['color'])
                figure_dict['end']['color'] = color

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
                color = Color(figure_dict['topLeft']['color'])
                figure_dict['topLeft']['color'] = color
                del figure_dict['bottomRight']['name']
                color = Color(figure_dict['bottomRight']['color'])
                figure_dict['bottomRight']['color'] = color

                figure_dict['topLeft'] = Point(**figure_dict['topLeft'])
                p = Point(**figure_dict['bottomRight'])
                figure_dict['bottomRight'] = p

                figure_dict['color'] = Color(figure_dict['color'])
                rx = figure_dict.pop('rx')
                ry = figure_dict.pop('ry')

                figure = Ellipse(**figure_dict)
                figure.set_move_info(rx, ry)
            else:
                raise ValueError(f"Unknown figure name: {figure_name}")
            self.figures.append(figure)

        self.update_display_matrix(None)

    @staticmethod
    def newell_algorithm(vertices):
        # Initialize normal vector
        normal = [0, 0, 0]

        # Calculate the normal vector using Newell's algorithm
        for i in range(len(vertices)):
            j = (i + 1) % len(vertices)
            normal[0] += (vertices[i].y - vertices[j].y) * (vertices[i].z + vertices[j].z)
            normal[1] += (vertices[i].z - vertices[j].z) * (vertices[i].x + vertices[j].x)
            normal[2] += (vertices[i].x - vertices[j].x) * (vertices[i].y + vertices[j].y)

        # Normalize the normal vector
        magnitude = (normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2) ** 0.5
        normal = [n / magnitude for n in normal]

        return normal
    @staticmethod
    def check_overlap(place1, place2):
        # Check if the bounding boxes of the places overlap in the Z direction
        min_z1 = min([v.z for v in place1])
        max_z1 = max([v.z for v in place1])
        min_z2 = min([v.z for v in place2])
        max_z2 = max([v.z for v in place2])
        if min_z1 > max_z2 or max_z1 < min_z2:
            return False

        # Check for X and Y overlap
        min_x1 = min([v.x for v in place1])
        max_x1 = max([v.x for v in place1])
        min_x2 = min([v.x for v in place2])
        max_x2 = max([v.x for v in place2])
        if max_x1 < min_x2 or min_x1 > max_x2:
            return False

        min_y1 = min([v.y for v in place1])
        max_y1 = max([v.y for v in place1])
        min_y2 = min([v.y for v in place2])
        max_y2 = max([v.y for v in place2])
        if max_y1 < min_y2 or min_y1 > max_y2:
            return False

        # Check that all vertices of P are behind the plane of Q
        normal = Model.newell_algorithm(place2)
        for vertex in place1:
            v = [vertex.x, vertex.y, vertex.z]
            dot_product = sum([v[i] * normal[i] for i in range(3)])
            if dot_product >= normal[2]:
                return False

        # Check that all vertices of Q are in front of the plane of P
        normal = Model.newell_algorithm(place1)
        for vertex in place2:
            v = [vertex.x, vertex.y, vertex.z]
            dot_product = sum([v[i] * normal[i] for i in range(3)])
            if dot_product <= normal[2]:
                return False

        # Check that the rasterization of P and Q do not overlap
        # тут должно быть разделение плоскостей и повторная проверка

        return True

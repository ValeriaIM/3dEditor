class Vector3:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def distance(vector1, vector2) -> float:
        return ((vector1.x - vector2.x) ** 2 + (vector1.y - vector2.y) ** 2 +
                (vector1.z - vector2.z) ** 2) ** 0.5

    def __add__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x + other.x,
                           self.y + other.y,
                           self.z + other.z)

    def __sub__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x - other.x,
                           self.y - other.y,
                           self.z - other.z)

    def __mul__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.y * other.z - self.z * other.y,
                           self.z * other.x - self.x * other.z,
                           self.x * other.y - self.y * other.x)
        elif isinstance(other, float) or isinstance(other, int):
            return Vector3(self.x * other, self.y * other, self.z * other)

    @staticmethod
    def dot_product(v1, v2):
        t1 = v1.to_tuple()
        t2 = v2.to_tuple()
        return sum(i * j for i, j in zip(t1, t2))

    def __eq__(self, other):
        return (isinstance(other, Vector3) and self.x == other.x and
                self.y == other.y and self.z == other.z)

    def __str__(self):
        return f'{float(self.x)},{float(self.y)},{float(self.z)}'

    def to_matrix(self):
        return Matrix(3, 1, self.x, self.y, self.z)

    def to_tuple(self):
        return self.x, self.y, self.z

    def to_dict(self):
        return {"x": self.x, "y": self.y, "z": self.z}


class Matrix:
    def __init__(self, string: int, column: int, *args: float):
        self.table = []
        self.zero_string = [0 for _ in range(column)]
        self.column = column
        for _ in range(string):
            self.table.append([])
        for i in range(column * string):
            self.table[i // column].append(args[i])

    def __getitem__(self, key):
        return self.table[key]

    def __mul__(self, other):
        if isinstance(other, Matrix):
            if self.column != len(other.table):
                raise ValueError("Incorrect multiply")
            ceils = []
            for i in range(len(self.table)):
                for j in range(other.column):
                    res = 0
                    for x in range(self.column):
                        res += self[i][x] * other[x][j]
                    ceils.append(res)
            return Matrix(len(self.table), other.column, *ceils)
        if isinstance(other, Vector3):
            return self * (other.to_matrix())

    def transpose(self):
        if len(self.table) != self.column:
            raise ValueError()
        ceils = []
        for i in range(self.column):
            for j in range(self.column):
                ceils.append(self[j][i])
        return Matrix(self.column, self.column, *ceils)

    def to_tuple(self):
        line = []
        for string in self.table:
            for element in string:
                line.append(element)
        return tuple(line)

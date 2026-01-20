import copy

class Box:
    def __init__(self, name, max_weight):
        self._name = name
        self._max_weight = max_weight if max_weight > 0 else None
        self._things = []
        self.copy = []

    def add_thing(self, obj: tuple[str, int]):
        self.copy = copy.deepcopy(self._things)
        self.copy.append(obj)
        if self._max_weight < sum([x[1] for x in self.copy]):
            raise ValueError('превышен суммарный вес вещей')
        self._things = self.copy

class BoxDefender:
    def __init__(self, box: Box):
        self.box = box
        self.copy = copy.deepcopy(box)

    def __enter__(self):
        return self.copy

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.box._things = self.copy._things
            # print(self.box.__dict__)
            return False

        return False

class MissionStatus:

    design = 1
    design_review = 2
    code = 3
    code_review = 4
    completed = 5

    name = {
        design: "design",
        design_review: "design_review",
        code: "code",
        code_review: "code_review",
        completed: "completed",
    }

    def __init__(self, value: int):
        self.value = value

    def has_value(self, value: int):
        return self.value == value

    def get_field(self):
        return self.__str__()

    def __str__(self):
        return self.name[self.value]

    @classmethod
    def of_string(cls, s: str):
        for (value, name) in cls.name.items():
            if s == name:
                return cls(value=value)

    def next(self):
        if self.has_value(self.completed):
            return None
        else:
            return MissionStatus(value=self.value + 1)

    def previous(self):
        if self.has_value(self.design):
            return None
        else:
            return MissionStatus(value=self.value - 1)

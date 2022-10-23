class MissionStatus:
    design_val = 1
    design_review_val = 2
    code = 3
    code_review = 4
    completed = 5

    def __init__(self, value):
        self.value = value

    @staticmethod
    def design():
        return MissionStatus(value = MissionStatus.design_val)

    @staticmethod
    def design_review():
        return MissionStatus(value = MissionStatus.design_review_val)

    @staticmethod
    def code():
        return MissionStatus(value = MissionStatus.code_val)

    @staticmethod
    def code_review():
        return MissionStatus(value = MissionStatus.code_review_val)

    @staticmethod
    def completed():
        return MissionStatus(value = MissionStatus.completed_val)

    @staticmethod
    def is_design(self):
        return self.value == MissionStatus.design_val

    @staticmethod
    def is_design_review(self):
        return self.value == MissionStatus.design_review_val

    @staticmethod
    def is_code(self):
        return self.value == MissionStatus.code_val

    @staticmethod
    def is_code_review(self):
        return self.value == MissionStatus.code_review_val

    @staticmethod
    def is_completed(self):
        return self.value == MissionStatus.completed_val
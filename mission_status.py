class MissionStatus:
    design_val = 1
    design_review_val = 2
    code_val = 3
    code_review_val = 4
    completed_val = 5

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

    def is_design(self):
        return self.value == MissionStatus.design_val

    def is_design_review(self):
        return self.value == MissionStatus.design_review_val

    def is_code(self):
        return self.value == MissionStatus.code_val

    def is_code_review(self):
        return self.value == MissionStatus.code_review_val

    def is_completed(self):
        return self.value == MissionStatus.completed_val

    def __str__(self):
        if self.is_design():
            return 'design'
        elif self.is_design_review():
            return 'design-review'
        elif self.is_code():
            return 'code'
        elif self.is_code_review():
            return 'code-review'
        elif self.is_completed():
            return 'completed'

    @staticmethod
    def of_string(s: str):
        if s == 'design':
            return MissionStatus.design()
        elif s == 'design-review':
            return MissionStatus.design_review()
        elif s == 'code':
            return MissionStatus.code()
        elif s == 'code-review':
            return MissionStatus.code_review()
        elif s == 'completed':
            return MissionStatus.completed()
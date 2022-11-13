from question import Question


class GoogleClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def create_link(self, mission_question: Question):
        return "some link"

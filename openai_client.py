import copy
import json
import requests

from question import Question

headers = {'authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsidXNlcl9pZCI6InVzZXItakFWQVJOSXJaSGQ2MWtwZGpZb2VEQ3FvIn0sImlzcyI6Imh0dHBzOi8vYXV0aDAub3BlbmFpLmNvbS8iLCJzdWIiOiJhdXRoMHw2MDliN2RmMDYyYzZlZjAwNjg5YjA3Y2QiLCJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSIsImh0dHBzOi8vb3BlbmFpLmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE2NzAwMDA0NDUsImV4cCI6MTY3MDAwNzY0NSwiYXpwIjoiVGRKSWNiZTE2V29USHROOTVueXl3aDVFNHlPbzZJdEciLCJzY29wZSI6Im9wZW5pZCBlbWFpbCBwcm9maWxlIG1vZGVsLnJlYWQgbW9kZWwucmVxdWVzdCBvcmdhbml6YXRpb24ucmVhZCBvZmZsaW5lX2FjY2VzcyJ9.dmdeqTNSRmDuLLrwogYwVgwslXWzkXnQg9KJUE5KHEmMeHAyIj6CWSvdRHn7K_9ZKWUH3qMjQ2xjon7DWd80JuLGEVBCBDzFDyWjg7XpIdvRd6sSn676ogMzTX3ISuNqAvHWQNY5-P82sq3GFq37bKuwtPt5ECcE0ShOMRiEO09vVbcarcJcSZp6AScaFceOmdXnIxtWmcuHJxrnv_NXpSHgWF_rWRku-a2TEFavIKBZ8PBDYMHyJe_gVGmYf1eWQXvp7xmIUSRAuau3KcbHZXUjyxdX0Nr086pqYIBqyT_-e4Pv6EHxf43yHVVxuw2XBds263uXVGa1mW3vjZfY-w'}


class OpenaiClient:
    def __init__(self):
        self.url = 'https://chat.openai.com/backend-api/conversation'
        self.headers = headers
        self.body = {'action': 'next',
                      'messages': [{'id': '9f799277-ca57-4104-9aaa-409027cd757f',
                                       'role': 'user',
                                       'content': {'content_type': 'text',
                                                       'parts': []}}],
                      'conversation_id': '1c6bfedc-1d32-4bf7-82c4-9406a94ef67e',
                      'parent_message_id': '1e09b661-9a4c-4471-8f37-1f2189fb3cf5',
                      'model': 'text-davinci-002-render'}

    def get_design_feedback(self, link: str, users_work: str):
        body = copy.deepcopy(self.body)
        body['messages'][0]['content']['parts'] = [f"Give me feedback on my solution to: {link}\n\n{users_work}"]
        design = requests.post(self.url, json=body, headers=self.headers)
        return json.loads(design.content.decode().split('\n\n')[-3].split('data: ')[1])['message']['content']['parts'][0].replace('\n\n', '\n')

    def get_design(self, link: str):
        body = copy.deepcopy(self.body)
        body['messages'][0]['content']['parts'] = [f"Describe an algorithm to solve: {link}"]
        design = requests.post(self.url, json=body, headers=self.headers)
        return json.loads(design.content.decode().split('\n\n')[-3].split('data: ')[1])['message']['content']['parts'][0]

    def get_code(self, link: str):
        body = copy.deepcopy(self.body)
        body['messages'][0]['content']['parts'] = [f"Implement that solution in python (for the previous question): {link}"]
        code = requests.post(self.url, json=body, headers=self.headers)
        return json.loads(code.content.decode().split('\n\n')[-3].split('data: ')[1])['message']['content']['parts'][0]

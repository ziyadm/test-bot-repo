from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from openai_client import OpenaiClient
from question import Question

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]
ACCOUNT_FILE = "token.json"


class GoogleClient:
    SUMMARIZED_FEEDBACK_FOR_ATTRIBUTES = {
            "sentences_too_long": "Split your sentences up to be short/simple to understand (< 10 words ideally).\n",
            "hard_to_read": "Change from paragraph format to bullet points\n",
            "needs_runtime": "Doesn't include runtime complexity.",
            "needs_space": "Doesn't include space complexity.",
            "slow_to_complete": "Too slow to complete.",
    }
    NEGATIVE_FEEDBACK_FOR_ATTRIBUTES = {
            "sentences_too_long": "Sentences too long.",
            "hard_to_read": "Hard to read.",
            "needs_runtime": "Doesn't include runtime complexity.",
            "needs_space": "Doesn't include space complexity.",
            "slow_to_complete": "Too slow to complete.",
    }
    POSITIVE_FEEDBACK_FOR_ATTRIBUTES = {
            "sentences_too_long": "Simple and clear sentences.",
            "hard_to_read": "Easy to read and understand.",
            "needs_runtime": "Includes runtime complexity.",
            "needs_space": "Includes space complexity.",
            "slow_to_complete": "Completed quickly.",
    }

    def __init__(self):
        credentials = Credentials.from_service_account_file(ACCOUNT_FILE, scopes=SCOPES)
        self.drive_service = build("drive", "v3", credentials=credentials)
        self.docs_service = build("docs", "v1", credentials=credentials)

    def create_template_instance(self, mission_question: Question):
        file_id = "1N1RvJ9sFoaJpsGDJ3f1gg6dYpvmKLBaEWpte60RSeok"
        copied_template = (
            self.drive_service.files()
            .copy(
                fileId=file_id,
                fields="id",
                body={"name": f"Mission: {mission_question.fields.question_id}"},
            )
            .execute()
        )
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": "{{question_id}}", "matchCase": "true"},
                    "replaceText": mission_question.fields.question_id,
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": "{{question_description}}", "matchCase": "true"},
                    "replaceText": mission_question.fields.description.strip(),
                }
            },
            {
                "updateTextStyle": {
                    "textStyle": {"link": {"url": f"{mission_question.fields.leetcode_url}"}},
                    "range": {"startIndex": 24, "endIndex": 28},
                    "fields": "link",
                }
            },
        ]
        result = (
            self.docs_service.documents()
            .batchUpdate(
                documentId=copied_template.get("id"),
                body={"requests": requests},
                fields="documentId",
            )
            .execute()
        )
        permission = {
            "type": "anyone",
            "role": "writer",
        }
        self.drive_service.permissions().create(
            fileId=result.get("documentId"), body=permission
        ).execute()
        return f"https://docs.google.com/document/d/{result.get('documentId')}/edit"

    def _get_ai_feedback(self, question_to_prepare: Question, users_work: str):
        openai_client = OpenaiClient()
        return openai_client.get_design_feedback(question_to_prepare.fields.leetcode_url, users_work)

    def _get_ai_suggested_design(self, question_to_prepare: Question):
        openai_client = OpenaiClient()
        return openai_client.get_design(question_to_prepare.fields.leetcode_url)

    def prepare_document(self, link: str, feedback: dict, question_to_prepare: Question, users_work: str):
        the_good = []
        the_bad = []
        comments = []

        for feedback_key, feedback_value in feedback.items():
            if feedback_value:
                the_bad.append(GoogleClient.NEGATIVE_FEEDBACK_FOR_ATTRIBUTES[feedback_key])
            else:
                the_good.append(GoogleClient.POSITIVE_FEEDBACK_FOR_ATTRIBUTES[feedback_key])

        good_message = ""
        for good_item in the_good:
            good_message += f"✅ {good_item}\n"
        good_message = good_message.strip("\n")
            
        bad_message = ""
        for bad_item in the_bad:
            bad_message += f"❌ {bad_item}\n"
        bad_message = bad_message.strip("\n")

        feedback_message = self._get_ai_feedback(question_to_prepare, users_work)
        suggested_design_message = self._get_ai_suggested_design(question_to_prepare)
        
        feedback_field = "Your reviewer will give you feedback on your design here."
        suggested_design_field = "Your reviewer will give you design suggestions here."
        good_list_field = "Your reviewer will list the good about your design here."
        bad_list_field = "Your reviewer will list the bad about your design here."

        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": feedback_field , "matchCase": "true"},
                    "replaceText": feedback_message,
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": suggested_design_field, "matchCase": "true"},
                    "replaceText": suggested_design_message,
                }
            },

            {
                "replaceAllText": {
                    "containsText": {"text": good_list_field, "matchCase": "true"},
                    "replaceText": good_message,
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": bad_list_field, "matchCase": "true"},
                    "replaceText": bad_message,
                }
            }
        ]

        file = (
            self.docs_service.documents()
            .batchUpdate(
                documentId=self.get_document_id(link),
                body={"requests": requests},
                fields="documentId",
            )
            .execute()
        )

        return f"https://docs.google.com/document/d/{file.get('documentId')}/edit"

    def update_document(self, link: str, stage_value: str):
        pass
        """feedback_message = "some feedback"
        good_list_message = "✅ first thing\n✅ second thing"
        bad_list_message = "❌ bad thing\n❌ bad thing 2"
        
        in_design = stage_value == "design"
        feedback_field = "Your reviewer will give you feedback on your design here." if in_design else "Your reviewer will give you feedback on your code here."
        good_list_field = "design_good_list" if in_design else "code_good_list"
        bad_list_field = "design_bad_list" if in_design else "code_bad_list"

        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": feedback_field , "matchCase": "true"},
                    "replaceText": feedback_message,
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": good_list_field, "matchCase": "true"},
                    "replaceText": good_list_message,
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": bad_list_field, "matchCase": "true"},
                    "replaceText": bad_list_message,
                }
            }
        ]

        file = (
            self.docs_service.documents()
            .batchUpdate(
                documentId=self.get_document_id(link),
                body={"requests": requests},
                fields="documentId",
            )
            .execute()
        )

        return f"https://docs.google.com/document/d/{file.get('documentId')}/edit"""

    def approve_document(self, link: str, score_field: str, score_value: float):
        in_design = score_field == "design_score"
        score_message = f"{score_value}/10"

        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": score_field, "matchCase": "true"},
                    "replaceText": score_message,
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": "NOT APPROVED", "matchCase": "true"},
                    "replaceText": "APPROVED"
                }
            }
        ]

        file = (
            self.docs_service.documents()
            .batchUpdate(
                documentId=self.get_document_id(link),
                body={"requests": requests},
                fields="documentId",
            )
            .execute()
        )

        return f"https://docs.google.com/document/d/{file.get('documentId')}/edit"

    def get_document_id(self, link: str):
        return link.split("/d/")[1].split("/edit")[0]

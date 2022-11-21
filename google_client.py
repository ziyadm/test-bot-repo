import io

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from question import Question

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]
ACCOUNT_FILE = "token.json"


class GoogleClient:
    def __init__(self):
        credentials = Credentials.from_service_account_file(ACCOUNT_FILE, scopes=SCOPES)
        self.drive_service = build("drive", "v3", credentials=credentials)
        self.docs_service = build("docs", "v1", credentials=credentials)

    def create_link(self, mission_question: Question):
        doc_body = (
            f"{mission_question.fields.leetcode_url}\n\n{mission_question.fields.description}"
        )
        media_body = MediaIoBaseUpload(
            io.BytesIO(bytes(doc_body, encoding="utf8")),
            mimetype="text/plain",
            resumable=True,
        )

        file_metadata = {
            "name": f"Mission: {mission_question.fields.question_id}",
            "mimeType": "application/vnd.google-apps.document",
            "uploadType": "media",
        }
        file = (
            self.drive_service.files()
            .create(body=file_metadata, media_body=media_body, fields="id")
            .execute()
        )
        fileId = file.get("id")

        permission = {
            "type": "anyone",
            "role": "writer",
        }
        self.drive_service.permissions().create(fileId=fileId, body=permission).execute()

        return f"https://docs.google.com/document/d/{fileId}/edit"

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
                    "replaceText": mission_question.fields.description,
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

    def add_to_document(self, content: str, file_id: str):
        existing_file = (
            self.drive_service.files().export(fileId=file_id, mimeType="text/plain").execute()
        )

        additional_doc_body = f"\n\n***Solution:***\n\n{content}"

        media_body = MediaIoBaseUpload(
            io.BytesIO(existing_file + bytes(additional_doc_body, encoding="utf8")),
            mimetype="text/plain",
            resumable=True,
        )

        file_metadata = {
            "mimeType": "application/vnd.google-apps.document",
            "uploadType": "media",
        }

        file = (
            self.drive_service.files()
            .update(fileId=file_id, body=file_metadata, media_body=media_body, fields="id")
            .execute()
        )

        return f"https://docs.google.com/document/d/{file.get('id')}/edit"

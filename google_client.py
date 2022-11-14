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
        self.service = build("drive", "v3", credentials=credentials)

    def create_link(self, mission_question: Question):
        doc_body = f"{mission_question.fields.leetcode_url}\n\n{mission_question.fields.description}"
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
            self.service.files()
            .create(body=file_metadata, media_body=media_body, fields="id")
            .execute()
        )
        fileId = file.get("id")

        permission = {
            "type": "anyone",
            "role": "writer",
        }
        self.service.permissions().create(fileId=fileId, body=permission).execute()

        return f"https://docs.google.com/document/d/{file.get('id')}/edit"

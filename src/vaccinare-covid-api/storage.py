#!/usr/bin/env python3

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class GoogleDriveUploader:
    def __init__(self, token_path="var/token.pickle", credentials_path="var/credentials.json"):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(token_path):
            with open(token_path, "rb") as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, "wb") as token:
                pickle.dump(creds, token)
        self.service = build("drive", "v3", credentials=creds)

    def upload(self, local_file_path, remote_file_name):
        results = self.service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results._get("files", [])

        file_id = None
        for item in items:
            if item["name"] == remote_file_name:
                file_id = item["id"]
                break

        if not file_id:
            file_metadata = {
                "name": remote_file_name,
                "mimeType": "application/vnd.google-apps.spreadsheet"
            }

            media = MediaFileUpload(local_file_path,
                                    mimetype="text/csv",
                                    resumable=True)

            self.service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields="id").execute()
        else:
            file = self.service.files()._get(fileId=file_id).execute()
            media_body = MediaFileUpload(local_file_path, mimetype=file["mimeType"], resumable=True)
            self.service.files().update(
                fileId=file_id,
                media_body=media_body).execute()

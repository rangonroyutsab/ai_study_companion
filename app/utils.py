import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# for m in client.models.list():
#     print(m.name)

def upload_to_gemini(path, mime_type="application/pdf"):
    return client.files.upload(
        file=path,
        config=types.UploadFileConfig(mime_type=mime_type),
    )

def wait_for_files_active(files):
    for file in files:
        file = client.files.get(name=file.name)
        while file.state.name == "PROCESSING":
            time.sleep(2)
            file = client.files.get(name=file.name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")

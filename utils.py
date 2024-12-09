import google.generativeai as genai
import time

genai.configure(api_key="AIzaSyAoapsmhtyLjkdEwfgEMNyivtEmSSdsVhA")

def upload_to_gemini(path, mime_type="application/pdf"):
    file = genai.upload_file(path, mime_type=mime_type)
    return file

def wait_for_files_active(files):
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            time.sleep(2)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")
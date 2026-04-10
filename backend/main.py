from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
base_dir = os.path.dirname(__file__)
cpp_path = os.path.join(base_dir, "/Users/vedanshnegi/Desktop/resume-optimizer/cpp_engine/analyzer")
process = subprocess.Popen(
    [cpp_path],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class RequestData(BaseModel):
    education: str
    skills: str
    projects: str
    experience: str
    job: str
@app.get("/")
def home():
    return {"message": "Resume Analyzer API Running"}
@app.post("/analyze")
def analyze(data: RequestData):
    try:
        process = subprocess.Popen(
            [cpp_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        input_data = (
            data.education + "\n###\n" +
            data.skills + "\n###\n" +
            data.projects + "\n###\n" +
            data.experience + "\n###\n" +
            data.job + "\n"
        )

        output, error = process.communicate(input_data)

        return {
            "result": output,
            "error": error
        }

    except Exception as e:
        return {"error": str(e)}

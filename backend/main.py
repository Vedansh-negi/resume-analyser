from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import json
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
    resume: str
    job: str
@app.get("/")
def home():
    return {"message": "Resume Analyzer API Running"}
@app.post("/analyze")
def analyze(data: RequestData):
    process = subprocess.Popen(
        ["../cpp_engine/analyzer"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    input_data = data.resume + "\n" + data.job + "\n"
    output, error = process.communicate(input_data)
    return {
    "output": output,
    "error": error
}

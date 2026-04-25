import pdfplumber
import sys

file_path = sys.argv[1]

text = ""

with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        content = page.extract_text()
        if content:
            text += content + " "

print(text)
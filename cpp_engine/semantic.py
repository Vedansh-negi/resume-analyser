from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import sys
import json

model = SentenceTransformer('all-MiniLM-L6-v2')

with open("input.json", "r") as f:
    data = json.load(f)

resume = data["resume"]
job = data["job"]

emb1 = model.encode(resume)
emb2 = model.encode(job)

score = cosine_similarity([emb1], [emb2])[0][0]

print(score)
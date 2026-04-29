from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import sys
import json

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')

try:
    # ✅ Read from stdin (NOT file)
    data = json.loads(sys.stdin.read())

    resume = data["resume"]
    job = data["job"]

    emb1 = model.encode(resume)
    emb2 = model.encode(job)

    score = cosine_similarity([emb1], [emb2])[0][0]

    print(json.dumps({"semantic_score": float(score)}))

except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
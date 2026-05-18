"""
Build the TF-IDF search index from knowledge_base.txt.
Run once: python build_index.py
"""
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer

DATA_DIR  = Path(__file__).parent / "data"
INDEX_DIR = Path(__file__).parent / "index"

def chunk(text, size=200, overlap=30):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        c = " ".join(words[i:i+size])
        if len(c) > 20:
            chunks.append(c)
        i += size - overlap
    return chunks

def build():
    print("Building index...")
    INDEX_DIR.mkdir(exist_ok=True)
    all_chunks, all_sources = [], []
    for f in sorted(DATA_DIR.glob("*.txt")):
        cs = chunk(f.read_text(encoding="utf-8"))
        for c in cs:
            all_chunks.append(c)
            all_sources.append(f.name)
        print(f"  {f.name} → {len(cs)} chunks")
    vec    = TfidfVectorizer(ngram_range=(1,2), max_features=15000, sublinear_tf=True)
    matrix = vec.fit_transform(all_chunks)
    pickle.dump(vec,         open(INDEX_DIR/"vectorizer.pkl","wb"))
    pickle.dump(matrix,      open(INDEX_DIR/"matrix.pkl","wb"))
    pickle.dump(all_chunks,  open(INDEX_DIR/"chunks.pkl","wb"))
    pickle.dump(all_sources, open(INDEX_DIR/"sources.pkl","wb"))
    print(f"Done — {len(all_chunks)} chunks indexed")

if __name__ == "__main__":
    build()

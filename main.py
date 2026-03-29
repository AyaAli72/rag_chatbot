from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import shutil
import os
import numpy as np

from models.file_loader import FileLoader
from models.chunker import TextChunker
from models.embedding_model import EmbeddingModel
from models.llm_model import LLMModel
from vectorstore.faiss_store import FAISSStore

# --------------------------
# FastAPI app
# --------------------------
app = FastAPI()
vector_store = None
chunks = []

# --------------------------
# HTML UI
# --------------------------
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>🤖 RAG Chatbot</title>
<style>
body {font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f8fafc; display:flex; justify-content:center; align-items:flex-start; min-height:100vh;}
.container {width:600px; background:#1e293b; padding:30px; margin-top:50px; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.5);}
h1 {text-align:center; color:#22c55e; margin-bottom:20px;}
h3 {margin-bottom:10px; color:#38bdf8;}
input[type="text"], input[type="file"], textarea {width:100%; padding:12px; margin-bottom:15px; border-radius:10px; border:none; outline:none;}
button {width:100%; padding:12px; border-radius:10px; border:none; background-color:#22c55e; color:white; font-weight:bold; cursor:pointer; transition:0.3s;}
button:hover {background-color:#16a34a;}
.answer-box {background:#334155; padding:15px; border-radius:10px; min-height:60px; margin-top:15px; white-space:pre-wrap;}
.section {margin-bottom:25px;}
</style>
</head>
<body>
<div class="container">
<h1>🤖 RAG Chatbot</h1>
<div class="section">
<h3>📂 Upload File (PDF / TXT)</h3>
<input type="file" id="fileInput">
<button onclick="uploadFile()">Upload File</button>
</div>
<div class="section">
<h3>🌐 Enter URL</h3>
<input type="text" id="urlInput" placeholder="https://example.com">
<button onclick="uploadURL()">Upload URL</button>
</div>
<div class="section">
<h3>💬 Ask Question</h3>
<input type="text" id="questionInput" placeholder="Type your question here">
<button onclick="askQuestion()">Ask</button>
<div class="answer-box" id="answerBox">Your answer will appear here...</div>
</div>
</div>
<script>
async function uploadFile() {
    let file = document.getElementById("fileInput").files[0];
    if (!file) { alert("Please select a file!"); return; }
    let formData = new FormData(); formData.append("file", file);
    let res = await fetch("/upload", {method:"POST", body:formData});
    let data = await res.json(); if (data.error) alert(data.error); else alert(data.message + ` (Chunks: ${data.chunks})`);
}
async function uploadURL() {
    let url = document.getElementById("urlInput").value;
    if (!url) { alert("Please enter a URL!"); return; }
    let formData = new FormData(); formData.append("url", url);
    let res = await fetch("/upload", {method:"POST", body:formData});
    let data = await res.json(); if (data.error) alert(data.error); else alert(data.message + ` (Chunks: ${data.chunks})`);
}
async function askQuestion() {
    let question = document.getElementById("questionInput").value;
    if (!question) { alert("Please type a question!"); return; }
    let res = await fetch(`/ask?question=${encodeURIComponent(question)}`, {method:"POST"});
    let data = await res.json();
    document.getElementById("answerBox").innerText = data.answer || "No answer generated.";
}
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_UI

# --------------------------
# Upload Endpoint
# --------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(None), url: str = Form(None)):
    global vector_store, chunks
    text = ""

    # 1️⃣ Load text from file or URL
    if file:
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        loader = FileLoader(file_path=file_path)
        if file.filename.lower().endswith(".pdf"):
            text = loader.load("pdf")
        elif file.filename.lower().endswith(".txt"):
            text = loader.load("txt")
        else:
            os.remove(file_path)
            return {"error":"Unsupported file type"}

        os.remove(file_path)  

    elif url:
        loader = FileLoader(url=url)
        text = loader.load("url")
    else:
        return {"error":"No file or URL provided"}

    if not text.strip():
        return {"error":"No text extracted from input"}

    # 2️⃣ Chunking
    chunker = TextChunker(max_len=500)
    chunks = chunker.chunk_text(text)

    # 3️⃣ Embeddings
    embedder = EmbeddingModel()
    embeddings = [embedder.get_embedding(c) for c in chunks if c.strip()]
    if not embeddings:
        return {"error":"Failed to generate embeddings"}

    # 4️⃣ FAISS store
    dim = len(embeddings[0])
    vector_store = FAISSStore(dim)
    vector_store.add_vectors(np.array(embeddings), chunks)

    return {"message":"Input processed successfully","chunks":len(chunks)}

# --------------------------
# Ask Endpoint
# --------------------------
@app.post("/ask")
async def ask_question(question: str):
    global vector_store, chunks
    if vector_store is None:
        return {"error":"No document uploaded yet"}

    embedder = EmbeddingModel()
    query_vector = embedder.get_embedding(question)

    distances, indices, retrieved_chunks = vector_store.search(query_vector, top_k=3)
    retrieved_chunks = [chunks[i] for i in indices[0] if i < len(chunks)]
    context = " ".join(retrieved_chunks)

    llm = LLMModel()
    answer = llm.generate_response(question, context)

    return {"answer": answer}
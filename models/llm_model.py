from transformers import pipeline

class LLMModel:
    def __init__(self):
        self.generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base",
    do_sample=True,       
    max_new_tokens=200,
    truncation=True,
    pad_token_id=0
)

    def generate_response(self, question, context):
        max_context_length = 2000  
        if len(context) > max_context_length:
            context = context[-max_context_length:]

        prompt = f"""
You are an expert AI expert assistant.
understande the context very well and 
Answer the question using ONLY the context below.
If the answer is not found, say "Not found".

Give a clear answer in 2-6 sentences.

Context:
{context}

Question:
{question}

Answer:
"""
        result = self.generator(prompt, max_new_tokens=200)
        text = result[0]["generated_text"]
        text = " ".join(text.split())
        if "Answer:" in text:
            return text.split("Answer:")[-1].strip()

        return text.strip()
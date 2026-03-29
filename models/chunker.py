import re

class TextChunker:
    def __init__(self, max_len=500, overlap=50):
        """
        max_len: أقصى طول لكل chunk
        overlap: عدد الأحرف المشتركة بين chunks متتالية
        """
        self.max_len = max_len
        self.overlap = overlap

    def chunk_text(self, text):
        # تنظيف النص من فراغات زايدة بما فيها \n
        text = " ".join(text.split())
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current = ""

        for s in sentences:
            s = s.strip()
            if not s:
                continue

            if len(current) + len(s) + 1 <= self.max_len:
                current += " " + s if current else s
            else:
                if current:
                    chunks.append(current.strip())
                # overlap: خذ آخر self.overlap chars أو أقل إذا current أقصر
                overlap_text = current[-self.overlap:] if self.overlap > 0 else ""
                current = (overlap_text + " " + s).strip() if overlap_text else s

        if current.strip():
            chunks.append(current.strip())

        return chunks
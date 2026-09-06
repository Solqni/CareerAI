"""简历文件文本提取（txt / pdf / docx）。"""

import io

from fastapi import HTTPException, UploadFile


async def extract_text(file: UploadFile) -> str:
    filename = (file.filename or "").lower()
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空")

    if filename.endswith((".txt", ".md")):
        return content.decode("utf-8", errors="ignore")

    if filename.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            raise HTTPException(status_code=400, detail="无法从 PDF 中提取文本")
        return text

    if filename.endswith(".docx"):
        from docx import Document

        doc = Document(io.BytesIO(content))
        text = "\n".join(p.text for p in doc.paragraphs)
        if not text.strip():
            raise HTTPException(status_code=400, detail="无法从 Word 中提取文本")
        return text

    raise HTTPException(status_code=400, detail="仅支持 .txt / .md / .pdf / .docx 格式")

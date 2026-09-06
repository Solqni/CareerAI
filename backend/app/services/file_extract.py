"""文件文本提取：支持 PDF、Word、Markdown、TXT 格式。"""

from io import BytesIO
from pathlib import Path

import pypdf
from docx import Document


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = pypdf.PdfReader(BytesIO(file_bytes))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(BytesIO(file_bytes))
    paragraphs: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text.strip())
    return "\n".join(paragraphs)


def extract_text_from_markdown(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="replace")


def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="replace")


EXTENSION_MAP = {
    ".pdf": extract_text_from_pdf,
    ".docx": extract_text_from_docx,
    ".doc": extract_text_from_docx,
    ".md": extract_text_from_markdown,
    ".txt": extract_text_from_txt,
}


def extract_text(filename: str, file_bytes: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    extractor = EXTENSION_MAP.get(suffix)
    if not extractor:
        raise ValueError(f"不支持的文件格式: {suffix}")
    return extractor(file_bytes)
from pathlib import Path

from langchain_community.document_loaders import (
    CSVLoader,
    PyPDFLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".csv",
    ".xls",
    ".xlsx",
}


def is_supported_file(file_name):
    return Path(file_name).suffix.lower() in SUPPORTED_EXTENSIONS


def get_allowed_extensions_text():
    return ", ".join(sorted(SUPPORTED_EXTENSIONS))


def get_loader_for_file(file_path):
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return PyPDFLoader(file_path)

    if extension == ".csv":
        return CSVLoader(file_path)

    if extension in {".doc", ".docx"}:
        return UnstructuredWordDocumentLoader(file_path)

    if extension in {".ppt", ".pptx"}:
        return UnstructuredPowerPointLoader(file_path)

    if extension in {".xls", ".xlsx"}:
        return UnstructuredExcelLoader(file_path)

    raise ValueError(f"Unsupported file type: {extension}")


def extract_text_from_file(file_path):
    loader = get_loader_for_file(file_path)
    documents = loader.load()
    extracted_chunks = []

    for document in documents:
        page_content = document.page_content.strip()
        if page_content:
            extracted_chunks.append(page_content)

    return "\n\n".join(extracted_chunks)


def chunk_text(text, chunk_size=500, overlap=50):
    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += step

    return chunks

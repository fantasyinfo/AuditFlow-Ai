from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.parser import ParsedDocument


@dataclass
class DocumentChunkItem:
    chunk_index: int
    page: int
    text: str


class DocumentChunker:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 60):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )

    def chunk_document(self, parsed_doc: ParsedDocument) -> list[DocumentChunkItem]:
        chunks: list[DocumentChunkItem] = []
        overall_index = 0

        for page_num, page_text in parsed_doc.pages:
            clean_text = page_text.strip()
            if not clean_text:
                continue

            splits = self.splitter.split_text(clean_text)
            for split_text in splits:
                if split_text.strip():
                    chunks.append(
                        DocumentChunkItem(
                            chunk_index=overall_index,
                            page=page_num,
                            text=split_text.strip(),
                        )
                    )
                    overall_index += 1

        # Fallback if no page text was split but full_text exists
        if not chunks and parsed_doc.full_text.strip():
            splits = self.splitter.split_text(parsed_doc.full_text.strip())
            for idx, split_text in enumerate(splits):
                chunks.append(
                    DocumentChunkItem(
                        chunk_index=idx,
                        page=1,
                        text=split_text.strip(),
                    )
                )

        return chunks


default_chunker = DocumentChunker()


def chunk_document(parsed_doc: ParsedDocument) -> list[DocumentChunkItem]:
    return default_chunker.chunk_document(parsed_doc)


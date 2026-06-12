import base64
import io
import logging

import anthropic
import fitz  # PyMuPDF
import docx

from core.ai_providers import get_gemini
from core.config import settings

logger = logging.getLogger(__name__)

# Synchronous Anthropic client — extract_text() is called synchronously from
# async route handlers, so the vision fallback must not require an event loop.
_sync_anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

_MIN_TEXT_CHARS = 50
_MAX_VISION_PAGES = 3

_VISION_PROMPT = (
    "Extract ALL text from this resume image, preserving sections and order. "
    "Return plain text only."
)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)

    if len(text.strip()) >= _MIN_TEXT_CHARS:
        return text

    logger.info("PDF has little/no text layer, falling back to vision OCR")
    return extract_text_via_vision(file_bytes)


def extract_text_via_vision(file_bytes: bytes) -> str:
    """OCR an image-based PDF by rendering pages and sending them to a vision model."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_images: list[bytes] = []
    for page in doc[:_MAX_VISION_PAGES]:
        pix = page.get_pixmap(dpi=150)
        page_images.append(pix.tobytes("png"))

    if not page_images:
        return ""

    try:
        return _extract_text_via_gemini_vision(page_images)
    except Exception as e:
        logger.warning("Gemini vision OCR failed, falling back to Claude: %s", e)

    return _extract_text_via_claude_vision(page_images)


def _extract_text_via_gemini_vision(page_images: list[bytes]) -> str:
    gemini = get_gemini()
    if not gemini:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    from google.genai import types

    parts = [types.Part.from_bytes(data=img, mime_type="image/png") for img in page_images]
    response = gemini.models.generate_content(
        model="gemini-2.0-flash",
        contents=[_VISION_PROMPT, *parts],
    )
    return "\n\n".join(filter(None, [response.text]))


def _extract_text_via_claude_vision(page_images: list[bytes]) -> str:
    content = [{"type": "text", "text": _VISION_PROMPT}]
    for img in page_images:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64.b64encode(img).decode("ascii"),
                },
            }
        )

    msg = _sync_anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": content}],
    )
    return msg.content[0].text


def extract_text_from_docx(file_bytes: bytes) -> str:
    document = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def extract_text(file_bytes: bytes, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        try:
            return extract_text_from_pdf(file_bytes)
        except Exception as e:
            logger.error("PDF extraction failed for %s: %s", filename, e)
            raise ValueError("Could not read this PDF. Try uploading a DOCX or a text-based PDF.")
    if lower.endswith((".docx", ".doc")):
        try:
            return extract_text_from_docx(file_bytes)
        except Exception as e:
            logger.error("DOCX extraction failed for %s: %s", filename, e)
            raise ValueError("Could not read this document. Try uploading a different file.")
    raise ValueError(f"Unsupported file type: {filename}")

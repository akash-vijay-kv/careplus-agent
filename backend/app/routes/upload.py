"""File upload endpoint for parsing blood reports.

Uses pdfplumber for text-based PDFs, pytesseract (Tesseract OCR) for
scanned PDFs and images, and GPT-4o-mini (text only) for structuring
the extracted text into JSON.
"""

import asyncio
import io
import json
import logging
import os
import re
import traceback
from functools import partial
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from openai import OpenAI

from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOADS_DIR = Path("/app/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

TEXT_PARSE_MODEL = "gpt-4o-mini"

BLOOD_REPORT_PARSE_PROMPT = """You are a medical document parser. Extract blood test results from the provided text.

Return the results as a JSON array. Each entry must have these fields:
- test_type: name of the test (e.g., "Total Cholesterol", "Fasting Blood Sugar", "Hemoglobin", "HbA1c", "LDL Cholesterol", "HDL Cholesterol", "Triglycerides", "WBC", "RBC", "Platelets", "TSH", "Creatinine", "Urea", "Bilirubin", "SGPT", "SGOT", "Vitamin D", "Vitamin B12", "Iron", "Calcium", "Uric Acid", "ESR", "CRP")
- value: numeric value of the result (number only)
- unit: unit of measurement (e.g., "mg/dL", "g/dL", "%", "cells/mcL", "mIU/L", "ng/mL", "pg/mL", "mmol/L")
- reference_range_low: lower bound of normal range (number or null if not shown)
- reference_range_high: upper bound of normal range (number or null if not shown)
- tested_at: date of the test in YYYY-MM-DD format (use today's date if not visible)

IMPORTANT:
- Return ONLY a valid JSON array, no markdown, no explanation, no other text.
- Extract ALL test results you can identify, even if the text is messy from OCR.
- If you cannot find any blood test results at all, return: []

Example output:
[{"test_type": "Total Cholesterol", "value": 210.0, "unit": "mg/dL", "reference_range_low": 125.0, "reference_range_high": 200.0, "tested_at": "2026-06-20"}]"""

MIN_MEANINGFUL_TEXT_LENGTH = 50


def _has_numeric_content(text: str) -> bool:
    """Check if text contains numeric values typical of blood reports.

    Parameters
    ----------
    text : str
        Extracted text to check.

    Returns
    -------
    bool
        True if the text contains at least 3 numeric values.
    """
    numbers = re.findall(r'\d+\.?\d*', text)
    return len(numbers) >= 3


def _extract_text_with_pdfplumber(file_bytes: bytes) -> str:
    """Extract text from a PDF using pdfplumber (handles tables well).

    Parameters
    ----------
    file_bytes : bytes
        Raw PDF file content.

    Returns
    -------
    str
        Extracted text from all pages.
    """
    try:
        import pdfplumber

        text_parts: list[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            cells = [str(c).strip() if c else "" for c in row]
                            text_parts.append("\t".join(cells))
                    text_parts.append("")

                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return "\n".join(text_parts)
    except Exception as e:
        logger.warning("pdfplumber text extraction failed: %s", e)
        return ""


def _ocr_pdf_pages(file_bytes: bytes) -> str:
    """Convert PDF pages to images and run Tesseract OCR on each.

    Parameters
    ----------
    file_bytes : bytes
        Raw PDF file content.

    Returns
    -------
    str
        OCR text from all pages.
    """
    try:
        from pdf2image import convert_from_bytes
        import pytesseract

        images = convert_from_bytes(file_bytes, dpi=300)
        if not images:
            return ""

        ocr_parts: list[str] = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img)
            if text and text.strip():
                ocr_parts.append(text.strip())
            logger.info("OCR page %d: %d chars", i + 1, len(text))

        return "\n\n".join(ocr_parts)
    except ImportError as e:
        logger.warning("OCR dependencies missing (pdf2image/pytesseract): %s", e)
        return ""
    except Exception as e:
        logger.warning("PDF OCR failed: %s", e)
        return ""


def _ocr_image(file_bytes: bytes) -> str:
    """Run Tesseract OCR on an image file.

    Parameters
    ----------
    file_bytes : bytes
        Raw image file content.

    Returns
    -------
    str
        OCR text extracted from the image.
    """
    try:
        from PIL import Image
        import pytesseract

        img = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(img)
        return text.strip() if text else ""
    except Exception as e:
        logger.warning("Image OCR failed: %s", e)
        return ""


def _parse_text_with_llm(text: str) -> str:
    """Send extracted text to GPT-4o-mini for structured JSON parsing.

    Parameters
    ----------
    text : str
        Raw text extracted from a blood report.

    Returns
    -------
    str
        JSON string with parsed blood results.
    """
    client = OpenAI(api_key=settings.openai_api_key)

    try:
        response = client.chat.completions.create(
            model=TEXT_PARSE_MODEL,
            messages=[
                {"role": "system", "content": BLOOD_REPORT_PARSE_PROMPT},
                {"role": "user", "content": f"Here is the blood report text:\n\n{text}"},
            ],
            max_tokens=4000,
        )

        result = response.choices[0].message.content or "[]"
        logger.info("LLM parse response (first 300 chars): %s", result[:300])
        return result
    except Exception as e:
        logger.error("LLM parse call failed: %s\n%s", e, traceback.format_exc())
        return "[]"


def _clean_json_response(raw: str) -> list:
    """Clean and parse JSON from LLM response.

    Parameters
    ----------
    raw : str
        Raw LLM output that should contain a JSON array.

    Returns
    -------
    list
        Parsed list of blood results, or empty list on failure.
    """
    clean = raw.strip()

    if clean.startswith("```"):
        lines = clean.split("\n")
        start = 1
        end = len(lines)
        for i in range(1, len(lines)):
            if lines[i].strip() == "```":
                end = i
                break
        clean = "\n".join(lines[start:end]).strip()

    bracket_start = clean.find("[")
    bracket_end = clean.rfind("]")
    if bracket_start != -1 and bracket_end != -1:
        clean = clean[bracket_start:bracket_end + 1]

    try:
        parsed = json.loads(clean)
        if isinstance(parsed, list):
            return parsed
        return []
    except json.JSONDecodeError as e:
        logger.warning("JSON parse failed: %s. Raw: %s", e, clean[:200])
        return []


def _process_pdf(file_bytes: bytes) -> list:
    """Process a PDF through text extraction, then OCR fallback.

    Strategy 1: pdfplumber text extraction (works for text-based PDFs).
    Strategy 2: Tesseract OCR via pdf2image (works for scanned PDFs).

    Parameters
    ----------
    file_bytes : bytes
        Raw PDF file content.

    Returns
    -------
    list
        Parsed blood results from the best strategy.
    """
    text = _extract_text_with_pdfplumber(file_bytes)
    logger.info("pdfplumber extraction: %d chars", len(text))

    if len(text) >= MIN_MEANINGFUL_TEXT_LENGTH and _has_numeric_content(text):
        logger.info("Using pdfplumber text for LLM parsing")
        raw_results = _parse_text_with_llm(text)
        parsed = _clean_json_response(raw_results)
        if parsed:
            return parsed

    logger.info("Falling back to OCR on PDF pages")
    ocr_text = _ocr_pdf_pages(file_bytes)
    logger.info("OCR extraction: %d chars", len(ocr_text))

    if len(ocr_text) >= MIN_MEANINGFUL_TEXT_LENGTH and _has_numeric_content(ocr_text):
        logger.info("Using OCR text for LLM parsing")
        combined = f"{text}\n\n--- OCR Text ---\n\n{ocr_text}" if text.strip() else ocr_text
        raw_results = _parse_text_with_llm(combined)
        parsed = _clean_json_response(raw_results)
        if parsed:
            return parsed

    if text.strip():
        logger.info("Last resort: sending all available text to LLM")
        raw_results = _parse_text_with_llm(text)
        return _clean_json_response(raw_results)

    return []


def _process_image(file_bytes: bytes) -> list:
    """Process an image file via Tesseract OCR then LLM parsing.

    Parameters
    ----------
    file_bytes : bytes
        Raw image file content.

    Returns
    -------
    list
        Parsed blood results.
    """
    ocr_text = _ocr_image(file_bytes)
    logger.info("Image OCR extraction: %d chars", len(ocr_text))

    if len(ocr_text) >= MIN_MEANINGFUL_TEXT_LENGTH:
        raw_results = _parse_text_with_llm(ocr_text)
        return _clean_json_response(raw_results)

    logger.warning("OCR produced insufficient text (%d chars)", len(ocr_text))
    return []


@router.post("/upload/blood-report")
async def upload_blood_report(
    file: UploadFile = File(...),
    session_id: str = Form(""),
) -> dict:
    """Upload and parse a blood report file (PDF or image).

    Parameters
    ----------
    file : UploadFile
        The blood report file (PDF, PNG, JPG, JPEG).
    session_id : str
        Session identifier for context.

    Returns
    -------
    dict
        Parsed blood results and a summary message for the agent.
    """
    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error("Failed to read uploaded file: %s", e)
        return {
            "status": "error",
            "message": "Failed to read the uploaded file. Please try again.",
            "parsed_results": [],
        }

    content_type = file.content_type or ""
    filename = file.filename or "unknown"

    save_path = UPLOADS_DIR / filename
    try:
        save_path.write_bytes(file_bytes)
        logger.info("Saved uploaded file to %s", save_path)
    except OSError as e:
        logger.error("Failed to save uploaded file to %s: %s", save_path, e)

    logger.info(
        "Processing upload: %s (content_type=%s, size=%d bytes)",
        filename, content_type, len(file_bytes),
    )

    parsed: list = []
    loop = asyncio.get_running_loop()

    try:
        if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
            parsed = await loop.run_in_executor(
                None, partial(_process_pdf, file_bytes)
            )
        elif content_type.startswith("image/"):
            parsed = await loop.run_in_executor(
                None, partial(_process_image, file_bytes)
            )
        else:
            return {
                "status": "error",
                "message": f"Unsupported file type: {content_type}. Please upload a PDF or image (PNG, JPG).",
                "parsed_results": [],
            }
    except Exception as e:
        logger.error(
            "Unexpected error processing %s: %s\n%s",
            filename, e, traceback.format_exc(),
        )
        return {
            "status": "error",
            "message": "An unexpected error occurred while processing your file. Please try again.",
            "parsed_results": [],
        }

    logger.info("Final parsed results: %d items from %s", len(parsed), filename)

    if not parsed:
        return {
            "status": "error",
            "message": (
                "Could not extract blood test results from the uploaded file. "
                "The document may not contain recognizable lab results, or the "
                "file may be corrupted. Please try uploading a clearer "
                "photo/screenshot of your report."
            ),
            "parsed_results": [],
        }

    summary_lines = [f"Parsed {len(parsed)} result(s) from '{filename}':"]
    for item in parsed:
        range_str = ""
        if item.get("reference_range_low") is not None and item.get("reference_range_high") is not None:
            range_str = f" (ref: {item['reference_range_low']}-{item['reference_range_high']})"
        summary_lines.append(
            f"  - {item['test_type']}: {item['value']} {item['unit']}{range_str}"
        )

    return {
        "status": "success",
        "message": "\n".join(summary_lines),
        "parsed_results": parsed,
        "filename": filename,
    }

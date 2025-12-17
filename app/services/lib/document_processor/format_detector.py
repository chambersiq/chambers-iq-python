"""
Format Detection Utility
Handles file format detection and scanned document identification.
"""

import puremagic
import io
from typing import Dict, Any
from pypdf import PdfReader


class FormatDetector:
    """
    Detects document formats and determines processing capabilities.
    """

    def __init__(self):
        # puremagic is stateless, no initialization needed
        pass

    def detect_format(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Detect document format and processing capabilities.

        Args:
            file_content: Raw file bytes
            filename: Original filename

        Returns:
            dict: Format detection results
        """
        # Determine format using puremagic
        try:
            # Returns a list of matches, e.g. [[mime, name, confidence]]
            matches = puremagic.magic_string(file_content)
            if matches:
                 # Take the most likely match (first one)
                 # matches[0] is typically [mime_type, name, confidence]
                 # But puremagic structure can vary, safely extract mime
                 mime_type = matches[0].mime_type if hasattr(matches[0], 'mime_type') else matches[0][0]
                 file_info = matches[0].name if hasattr(matches[0], 'name') else matches[0][1]
            else:
                 mime_type = "application/octet-stream"
                 file_info = "Unknown Binary"
        except Exception:
             # Fallback
             mime_type = "application/octet-stream"
             file_info = "Unknown"

        result = {
            "mime_type": mime_type,
            "file_info": file_info,
            "filename": filename,
            "format_type": None,
            "is_scanned": False,
            "supported": False,
            "error_message": None
        }

        # Determine format type
        if mime_type == "application/pdf":
            result["format_type"] = "pdf"
            result["is_scanned"] = self._is_scanned_pdf(file_content)
            result["supported"] = not result["is_scanned"]  # Text PDFs supported, scanned not yet
            if result["is_scanned"]:
                result["error_message"] = "Scanned PDF processing not yet supported. Please upload text-based PDFs or DOCX files."

        elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          "application/msword"]:
            result["format_type"] = "docx"
            result["supported"] = True

        elif mime_type.startswith("image/"):
            result["format_type"] = "image"
            result["supported"] = False
            result["error_message"] = "Image processing not yet supported. Please upload PDF or DOCX files."

        else:
            result["format_type"] = "unknown"
            result["supported"] = False
            result["error_message"] = f"Unsupported format: {mime_type}"

        return result

    def _is_scanned_pdf(self, file_content: bytes) -> bool:
        """
        Check if a PDF is scanned (image-based) vs text-based.

        Args:
            file_content: PDF file bytes

        Returns:
            bool: True if PDF appears to be scanned
        """
        try:
            reader = PdfReader(io.BytesIO(file_content))

            # Check first few pages for extractable text
            pages_to_check = min(3, len(reader.pages))

            for page_num in range(pages_to_check):
                page = reader.pages[page_num]
                text = page.extract_text()

                # If we find substantial text, it's likely not scanned
                if text and len(text.strip()) > 50:  # Reasonable text threshold
                    return False

            # If we get here, either no text found or very little text
            return True

        except Exception as e:
            # If we can't read the PDF, assume it's problematic (possibly scanned)
            print(f"Warning: Could not analyze PDF for scanned detection: {e}")
            return True

    def get_supported_formats(self) -> list:
        """
        Get list of currently supported file formats.

        Returns:
            list: Supported MIME types
        """
        return [
            "application/pdf",  # Text-based PDFs only
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
            "application/msword"  # DOC (legacy)
        ]

    def get_unsupported_formats_info(self) -> Dict[str, str]:
        """
        Get information about unsupported formats and why.

        Returns:
            dict: Format -> reason mapping
        """
        return {
            "image/*": "Image processing requires OCR integration (Phase 1B)",
            "application/pdf (scanned)": "Scanned PDFs require OCR integration (Phase 1B)",
            "application/rtf": "RTF format not prioritized for legal documents",
            "text/plain": "Plain text files not typically used for legal documents"
        }

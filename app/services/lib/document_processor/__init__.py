"""
Document Processor Library
Shared utilities for document processing across the application.
"""

from .format_detector import FormatDetector
from .text_extractors import TextExtractor
from .quality_assessor import QualityAssessor


class DocumentProcessor:
    """
    Main document processing class that orchestrates format detection,
    text extraction, and quality assessment.
    """

    def __init__(self):
        self.format_detector = FormatDetector()
        self.text_extractor = TextExtractor()
        self.quality_assessor = QualityAssessor()

    def process_document(self, file_content: bytes, filename: str) -> dict:
        """
        Process a document and return structured results.

        Args:
            file_content: Raw file bytes
            filename: Original filename

        Returns:
            dict: Processing results with format info, text, and quality metrics
        """
        # Detect format and check if supported
        format_result = self.format_detector.detect_format(file_content, filename)

        result = {
            "filename": filename,
            "format": format_result,
            "supported": format_result["supported"],
            "text": "",
            "quality_score": 0.0,
            "error_message": None
        }

        # Extract text if supported
        if format_result["supported"]:
            try:
                text = self.text_extractor.extract_text(file_content, format_result)
                result["text"] = text

                # Assess quality
                quality = self.quality_assessor.assess_quality(text, format_result)
                result["quality_score"] = quality["score"]

            except Exception as e:
                result["supported"] = False
                result["error_message"] = f"Extraction failed: {str(e)}"
        else:
            result["error_message"] = format_result.get("error_message", "Unsupported format")

        return result

    def is_supported_format(self, file_content: bytes, filename: str) -> bool:
        """
        Check if a document format is supported for processing.

        Args:
            file_content: Raw file bytes
            filename: Original filename

        Returns:
            bool: True if format is supported
        """
        format_result = self.format_detector.detect_format(file_content, filename)
        return format_result["supported"]

    def get_format_info(self, file_content: bytes, filename: str) -> dict:
        """
        Get detailed format information without processing.

        Args:
            file_content: Raw file bytes
            filename: Original filename

        Returns:
            dict: Format detection results
        """
        return self.format_detector.detect_format(file_content, filename)

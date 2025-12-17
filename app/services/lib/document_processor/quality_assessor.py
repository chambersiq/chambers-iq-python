"""
Quality Assessment Utility
Evaluates the quality and completeness of extracted text.
"""

from typing import Dict, Any
import re


class QualityAssessor:
    """
    Assesses the quality of extracted document text.
    """

    def assess_quality(self, text: str, format_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the quality of extracted text.

        Args:
            text: Extracted text content
            format_result: Format detection results

        Returns:
            dict: Quality assessment results
        """
        if not text or not text.strip():
            return {
                "score": 0.0,
                "grade": "F",
                "issues": ["No text content extracted"],
                "recommendations": ["Check if document contains text", "Verify file is not corrupted"]
            }

        # Perform various quality checks
        checks = self._perform_quality_checks(text, format_result)

        # Calculate overall score (0.0 to 1.0)
        score = self._calculate_quality_score(checks)

        # Determine grade
        grade = self._score_to_grade(score)

        # Generate recommendations
        recommendations = self._generate_recommendations(checks, format_result)

        return {
            "score": round(score, 2),
            "grade": grade,
            "issues": checks.get("issues", []),
            "recommendations": recommendations,
            "metrics": {
                "text_density": checks.get("text_density", 0),
                "has_structure": checks.get("has_structure", False),
                "language_confidence": checks.get("language_confidence", 0),
                "completeness_score": checks.get("completeness_score", 0)
            }
        }

    def _perform_quality_checks(self, text: str, format_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform various quality checks on the extracted text.

        Args:
            text: Extracted text
            format_result: Format detection results

        Returns:
            dict: Quality check results
        """
        checks = {
            "issues": [],
            "text_density": 0.0,
            "has_structure": False,
            "language_confidence": 0.0,
            "completeness_score": 0.0
        }

        # Text density check (characters per "page" estimate)
        text_length = len(text)
        # Estimate pages (rough heuristic: 2500 chars per page)
        estimated_pages = max(1, text_length / 2500)
        checks["text_density"] = text_length / estimated_pages

        if checks["text_density"] < 500:  # Very low density
            checks["issues"].append("Very low text density - possible scanning issues")

        # Structure detection
        checks["has_structure"] = self._has_document_structure(text)

        # Language detection (basic check for English)
        checks["language_confidence"] = self._detect_language_confidence(text)

        if checks["language_confidence"] < 0.5:
            checks["issues"].append("Low language confidence - possible OCR errors")

        # Completeness check
        checks["completeness_score"] = self._check_completeness(text)

        if checks["completeness_score"] < 0.3:
            checks["issues"].append("Document appears incomplete")

        # Format-specific checks
        format_type = format_result.get("format_type")
        if format_type == "pdf" and format_result.get("is_scanned"):
            checks["issues"].append("Document appears to be scanned - OCR may be needed")

        return checks

    def _has_document_structure(self, text: str) -> bool:
        """
        Check if text has document structure (headings, paragraphs, etc.).

        Args:
            text: Extracted text

        Returns:
            bool: True if structured content detected
        """
        # Look for common document structure indicators
        structure_indicators = [
            r'^[A-Z][A-Z\s]{10,}$',  # ALL CAPS HEADINGS
            r'^\d+\.',  # Numbered lists
            r'^•',  # Bullet points
            r'^[IVX]+\.',  # Roman numerals
            r'^\([a-z]\)',  # Lowercase letter lists
        ]

        lines = text.split('\n')
        structured_lines = 0

        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()
            if not line:
                continue

            for pattern in structure_indicators:
                if re.match(pattern, line, re.IGNORECASE):
                    structured_lines += 1
                    break

        # Consider it structured if > 20% of lines have structure
        return (structured_lines / max(1, len(lines))) > 0.2

    def _detect_language_confidence(self, text: str) -> float:
        """
        Basic language confidence check (focused on English legal text).

        Args:
            text: Extracted text

        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        # Common English words and legal terms
        english_indicators = [
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'agreement', 'contract', 'party', 'parties', 'court', 'case', 'law', 'legal',
            'shall', 'hereby', 'witness', 'whereas', 'therefore'
        ]

        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 0.0

        english_words = sum(1 for word in words if word in english_indicators)
        confidence = english_words / len(words)

        # Penalize very short texts
        if len(words) < 50:
            confidence *= 0.5

        return min(1.0, confidence * 2)  # Scale up for better sensitivity

    def _check_completeness(self, text: str) -> float:
        """
        Check if document appears complete.

        Args:
            text: Extracted text

        Returns:
            float: Completeness score (0.0 to 1.0)
        """
        # Look for document completeness indicators
        completeness_indicators = [
            r'witness', r'signature', r'executed', r'agreement',
            r'contract', r'date', r'party', r'parties'
        ]

        found_indicators = 0
        text_lower = text.lower()

        for indicator in completeness_indicators:
            if re.search(r'\b' + indicator + r'\b', text_lower):
                found_indicators += 1

        return found_indicators / len(completeness_indicators)

    def _calculate_quality_score(self, checks: Dict[str, Any]) -> float:
        """
        Calculate overall quality score from individual checks.

        Args:
            checks: Quality check results

        Returns:
            float: Overall quality score (0.0 to 1.0)
        """
        score = 1.0

        # Penalize for issues
        issue_penalty = len(checks.get("issues", [])) * 0.1
        score -= issue_penalty

        # Factor in text density (normalized)
        density_score = min(1.0, checks.get("text_density", 0) / 2000)
        score = score * 0.7 + density_score * 0.3

        # Factor in structure
        if checks.get("has_structure"):
            score += 0.1

        # Factor in language confidence
        lang_score = checks.get("language_confidence", 0)
        score = score * 0.9 + lang_score * 0.1

        # Factor in completeness
        completeness = checks.get("completeness_score", 0)
        score = score * 0.95 + completeness * 0.05

        return max(0.0, min(1.0, score))

    def _score_to_grade(self, score: float) -> str:
        """
        Convert quality score to letter grade.

        Args:
            score: Quality score (0.0 to 1.0)

        Returns:
            str: Letter grade
        """
        if score >= 0.9: return "A"
        elif score >= 0.8: return "B"
        elif score >= 0.7: return "C"
        elif score >= 0.6: return "D"
        else: return "F"

    def _generate_recommendations(self, checks: Dict[str, Any], format_result: Dict[str, Any]) -> list:
        """
        Generate recommendations based on quality assessment.

        Args:
            checks: Quality check results
            format_result: Format detection results

        Returns:
            list: Recommendations for improvement
        """
        recommendations = []

        if checks.get("text_density", 0) < 1000:
            recommendations.append("Consider using text-based PDFs instead of scanned documents")

        if not checks.get("has_structure"):
            recommendations.append("Document may benefit from better formatting or OCR processing")

        if checks.get("language_confidence", 1) < 0.7:
            recommendations.append("Review extracted text for potential OCR errors")

        if checks.get("completeness_score", 1) < 0.5:
            recommendations.append("Document appears incomplete - check original file")

        format_type = format_result.get("format_type")
        if format_type == "pdf" and format_result.get("is_scanned"):
            recommendations.append("Scanned PDF detected - OCR processing recommended for Phase 1B")

        return recommendations if recommendations else ["Document quality appears good"]

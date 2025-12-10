import os
import sys

# Add app to path
sys.path.append(os.getcwd())
sys.path.append("/Users/ganesh/Library/Python/3.9/lib/python/site-packages")

from app.core.config import settings
from app.agents.document_summarizer import doc_analysis_app

# Mock settings if needed (API Key)
if not settings.ANTHROPIC_API_KEY:
    print("Skipping LLM test: No API Key")
    # We can still verify import works
    print("Import success")
    sys.exit(0)

print("Starting Agent Verification...")

dummy_text = """
LEGAL NOTICE

To,
Mr. John Doe
123, Street Name

Sir,
My client Mr. Smith hereby calls upon you to pay Rs. 1,00,000 within 15 days of this notice, failing which legal action u/s 138 NI Act will be initiated.
Dated: 10th Dec 2024
"""

inputs = {
    "document_text": dummy_text,
    "client_position": "Sender",
    "is_bundle": False
}

try:
    print("Invoking Agent...")
    # Mocking LLM calls would be safer to avoid cost, but for "Verification" user usually means "Use the AI".
    # I'll let it try. If it requires API key and fails, I'll catch it.
    result = doc_analysis_app.invoke(inputs)
    print("Agent Result:")
    print(f"Category: {result.get('category')}")
    print(f"Analysis: {result.get('specialist_analysis')[:50]}...")
    print("Verification Successful!")
except Exception as e:
    print(f"Verification Failed: {e}")

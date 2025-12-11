import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.services.external.indian_kanoon import IndianKanoonClient

# Add project root to path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    token = os.getenv("INDIAN_KANOON_API_TOKEN")
    if not token:
        print("❌ Error: INDIAN_KANOON_API_TOKEN environment variable is not set.")
        print("Please export it: export INDIAN_KANOON_API_TOKEN='your_token'")
        return

    print(f"🔒 Using API Token: {token[:5]}...")
    client = IndianKanoonClient(api_token=token)

    try:
        # Search for a specific Judgment "K.M. Nanavati vs State Of Maharashtra"
        search_query = "K.M. Nanavati vs State Of Maharashtra"
        print(f"\n🔍 Searching for Judgment: '{search_query}'...")
        results = await client.search(search_query)
        if not results.get('docs'):
             print("No docs found for Kesavananda Bharati")
             return
             
        # Pick the first result
        doc_id = results['docs'][0]['tid']
        title = results['docs'][0]['title']
        print(f"📄 Testing with Doc ID: {doc_id} ({title})")

        # 1. Test Court Copy
        print(f"\n🏛️ Fetching Court Copy...")
        try:
            court_copy = await client.get_court_copy(doc_id)
            if 'errmsg' in court_copy:
                 print(f"⚠️ Court Copy Error: {court_copy['errmsg']}")
            else:
                 print(f"✅ Court Copy fetched. Keys: {court_copy.keys()}")
        except Exception as e:
            print(f"❌ Court Copy Exception: {e}")

        # 2. Test Get Fragments
        frag_query = "grave and sudden provocation"
        print(f"\n🧩 Fetching fragments for '{frag_query}'...")
        try:
             fragments = await client.get_document_fragments(doc_id, frag_query)
             if 'errmsg' in fragments:
                  print(f"⚠️ Fragments Error: {fragments['errmsg']}")
             else:
                  print(f"✅ Fragments fetched: {fragments.keys()}")
        except Exception as e:
             print(f"❌ Fragments Exception: {e}")

        # 3. Test Get Meta
        print(f"\nℹ️ Fetching metadata...")
        try:
             meta = await client.get_document_meta(doc_id)
             if 'errmsg' in meta:
                  print(f"⚠️ Metadata Error: {meta['errmsg']}")
             else:
                  print(f"✅ Metadata fetched: {meta.keys()}")
        except Exception as e:
             print(f"❌ Metadata Exception: {e}")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())

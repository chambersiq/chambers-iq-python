from app.api.v1.schemas.case import CaseCreate, Party

try:
    # Test Party Type
    p = Party(name="Test Opposing", type="PT_08")
    print("✅ Party schema accepts 'PT_08'")

    # Test Case Schema with opposingPartyType
    c = CaseCreate(
        caseName="Test Case",
        clientId="client-123", # client-123
        opposingPartyType="PT_08",
        status="active"
    )
    print("✅ CaseCreate schema accepts opposingPartyType='PT_08'")
    
except Exception as e:
    print(f"❌ Verification Failed: {e}")
    exit(1)

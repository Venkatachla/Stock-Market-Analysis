import asyncio
from sqlalchemy.orm import Session
from api.models import SessionLocal, User, Wallet, Holding, Transaction
from api.db_utils import get_user_by_email, create_user
from api.app_fixed import buy_stock, BuyRequest, add_demo_funds

async def test_buy_flow():
    db = SessionLocal()
    try:
        # 1. Setup test user
        email = "test_verify@example.com"
        user = get_user_by_email(db, email)
        if not user:
            user = create_user(db, email, "password123", "Test User")
            db.commit()
        
        user_id = user.id
        print(f"Testing for user ID: {user_id}")

        # 2. Add demo funds
        # Simulating the Header and Depends(get_db)
        print("Adding demo funds...")
        token = "Bearer dummy" # verify_auth_token will be mocked or we can just bypass it for testing logic
        # For simplicity, let's just manually add funds and then test buy
        from api.db_utils import add_to_wallet
        add_to_wallet(db, user_id, 50000.0)
        db.commit()
        
        # 3. Test Buy (Manual call for logic check)
        # We need to mock verify_auth_token for the route call
        # but let's just test if we can call update_holding_after_buy correctly
        from api.db_utils import get_or_create_holding, update_holding_after_buy
        
        holding = get_or_create_holding(db, user_id, "RELIANCE")
        print(f"Holding before: {holding.quantity} @ {holding.avg_price}")
        
        # This was the failing call (5 args vs 4)
        # update_holding_after_buy(db, user_id, "RELIANCE", 10, 2500.0) # This should FAIL
        # update_holding_after_buy(db, holding, 10, 2500.0) # This should SUCCEED
        
        try:
            update_holding_after_buy(db, holding, 10, 2500.0)
            print("Successfully updated holding after buy (Signature check passed)")
        except Exception as e:
            print(f"Failed to update holding: {e}")
            return

        db.commit()
        
        # 4. Verify in DB
        db.refresh(holding)
        print(f"Holding after: {holding.quantity} @ {holding.avg_price}")
        
        if holding.quantity > 0:
            print("✅ TEST PASSED: update_holding_after_buy signature and logic working.")
        else:
            print("❌ TEST FAILED: quantity not updated.")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_buy_flow())

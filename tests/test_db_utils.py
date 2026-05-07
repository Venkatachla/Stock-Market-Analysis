"""
Tests for api/db_utils.py — database CRUD operations.

Uses in-memory SQLite via conftest fixtures. Tests actual SQL operations
through the ORM without hitting production database.

Covers:
- User CRUD (create, get by email/id, duplicate prevention, password verification)
- Wallet operations (create, add, deduct, insufficient balance)
- Holding operations (get/create, buy update with avg price, sell partial/full)
- Transaction operations (create, list, update status)
"""
import pytest
from api.db_utils import (
    create_user, get_user_by_email, get_user_by_id, verify_user_password,
    update_user_token, create_wallet, get_wallet, add_to_wallet, deduct_from_wallet,
    get_or_create_holding, get_holding, get_user_holdings,
    update_holding_after_buy, update_holding_after_sell,
    create_transaction, get_user_transactions,
    get_transaction_by_order_id, update_transaction_status,
)


# ===================== User Functions =====================

class TestCreateUser:
    def test_creates_user_with_wallet(self, db_session):
        user = create_user(db_session, "new@test.com", "password123")
        db_session.commit()
        assert user is not None
        assert user.email == "new@test.com"
        # Wallet should be auto-created
        wallet = get_wallet(db_session, user.id)
        assert wallet is not None
        assert wallet.balance == 0.0

    def test_duplicate_email_returns_none(self, db_session):
        create_user(db_session, "dup@test.com", "pass1")
        db_session.commit()
        result = create_user(db_session, "dup@test.com", "pass2")
        assert result is None


class TestGetUser:
    def test_get_by_email(self, db_session, test_user):
        user = get_user_by_email(db_session, "test@example.com")
        assert user is not None
        assert user.id == test_user.id

    def test_get_by_email_not_found(self, db_session):
        assert get_user_by_email(db_session, "ghost@test.com") is None

    def test_get_by_id(self, db_session, test_user):
        user = get_user_by_id(db_session, test_user.id)
        assert user is not None
        assert user.email == "test@example.com"

    def test_get_by_id_not_found(self, db_session):
        assert get_user_by_id(db_session, 99999) is None


class TestVerifyUserPassword:
    def test_correct_password(self, db_session, test_user):
        user = verify_user_password(db_session, "test@example.com", "TestPassword123!")
        assert user is not None

    def test_wrong_password(self, db_session, test_user):
        assert verify_user_password(db_session, "test@example.com", "wrong") is None

    def test_nonexistent_email(self, db_session):
        assert verify_user_password(db_session, "nobody@test.com", "pass") is None


class TestUpdateUserToken:
    def test_update_token(self, db_session, test_user):
        result = update_user_token(db_session, test_user.id, "new_token_123")
        assert result is True

    def test_update_token_nonexistent_user(self, db_session):
        assert update_user_token(db_session, 99999, "token") is False


# ===================== Wallet Functions =====================

class TestWalletOperations:
    def test_add_to_wallet(self, db_session, test_user):
        assert add_to_wallet(db_session, test_user.id, 5000.0) is True
        wallet = get_wallet(db_session, test_user.id)
        assert wallet.balance == 5000.0

    def test_add_accumulates(self, db_session, test_user):
        add_to_wallet(db_session, test_user.id, 1000)
        add_to_wallet(db_session, test_user.id, 2000)
        wallet = get_wallet(db_session, test_user.id)
        assert wallet.balance == 3000.0

    def test_deduct_from_wallet(self, db_session, funded_user):
        assert deduct_from_wallet(db_session, funded_user.id, 30000) is True
        wallet = get_wallet(db_session, funded_user.id)
        assert wallet.balance == 70000.0

    def test_deduct_insufficient_returns_false(self, db_session, test_user):
        # User has 0 balance
        assert deduct_from_wallet(db_session, test_user.id, 100) is False

    def test_add_to_nonexistent_wallet(self, db_session):
        assert add_to_wallet(db_session, 99999, 100) is False


# ===================== Holding Functions =====================

class TestHoldingOperations:
    def test_get_or_create_creates_new(self, db_session, test_user):
        holding = get_or_create_holding(db_session, test_user.id, "INFY")
        assert holding.symbol == "INFY"
        assert holding.quantity == 0

    def test_get_or_create_returns_existing(self, db_session, test_user):
        h1 = get_or_create_holding(db_session, test_user.id, "INFY")
        h2 = get_or_create_holding(db_session, test_user.id, "INFY")
        assert h1.id == h2.id

    def test_get_holding_not_found(self, db_session, test_user):
        assert get_holding(db_session, test_user.id, "NONEXIST") is None

    def test_update_holding_after_buy_first_purchase(self, db_session, test_user):
        holding = get_or_create_holding(db_session, test_user.id, "TCS")
        update_holding_after_buy(db_session, holding, quantity=10, price=3000)
        assert holding.quantity == 10
        assert holding.avg_price == 3000.0

    def test_update_holding_after_buy_avg_price_recalc(self, db_session, test_user):
        holding = get_or_create_holding(db_session, test_user.id, "TCS")
        update_holding_after_buy(db_session, holding, quantity=10, price=1000)
        update_holding_after_buy(db_session, holding, quantity=10, price=2000)
        # New avg = (10*1000 + 10*2000) / 20 = 1500
        assert holding.quantity == 20
        assert holding.avg_price == 1500.0

    def test_update_holding_after_sell_partial(self, db_session, test_user):
        holding = get_or_create_holding(db_session, test_user.id, "WIPRO")
        update_holding_after_buy(db_session, holding, quantity=10, price=500)
        update_holding_after_sell(db_session, holding, quantity=3, price=600)
        assert holding.quantity == 7

    def test_update_holding_after_sell_all_deletes(self, db_session, test_user):
        holding = get_or_create_holding(db_session, test_user.id, "LT")
        update_holding_after_buy(db_session, holding, quantity=5, price=2000)
        update_holding_after_sell(db_session, holding, quantity=5, price=2100)
        db_session.flush()
        # Holding should be deleted
        assert get_holding(db_session, test_user.id, "LT") is None

    def test_get_user_holdings(self, db_session, test_user):
        h1 = get_or_create_holding(db_session, test_user.id, "INFY")
        update_holding_after_buy(db_session, h1, 5, 1500)
        h2 = get_or_create_holding(db_session, test_user.id, "TCS")
        update_holding_after_buy(db_session, h2, 3, 3000)
        holdings = get_user_holdings(db_session, test_user.id)
        assert len(holdings) == 2


# ===================== Transaction Functions =====================

class TestTransactionOperations:
    def test_create_transaction(self, db_session, test_user):
        tx = create_transaction(
            db_session, test_user.id, "BUY", 1500.0,
            symbol="INFY", quantity=1, price=1500, status="completed",
        )
        assert tx.id is not None
        assert tx.type == "BUY"
        assert tx.total_amount == 1500.0

    def test_get_user_transactions_ordered(self, db_session, test_user):
        create_transaction(db_session, test_user.id, "BUY", 1000)
        create_transaction(db_session, test_user.id, "SELL", 2000)
        db_session.commit()
        txs = get_user_transactions(db_session, test_user.id)
        assert len(txs) == 2

    def test_get_transaction_by_order_id(self, db_session, test_user):
        create_transaction(
            db_session, test_user.id, "DEPOSIT", 5000,
            order_id="order_test123", status="PENDING",
        )
        db_session.commit()
        tx = get_transaction_by_order_id(db_session, "order_test123")
        assert tx is not None
        assert tx.total_amount == 5000

    def test_update_transaction_status(self, db_session, test_user):
        tx = create_transaction(db_session, test_user.id, "DEPOSIT", 5000, status="PENDING")
        db_session.commit()
        result = update_transaction_status(db_session, tx.id, "SUCCESS", "pay_123", "sig_456")
        assert result is True

    def test_update_nonexistent_transaction(self, db_session):
        assert update_transaction_status(db_session, 99999, "FAILED") is False

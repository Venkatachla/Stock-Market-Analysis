"""
Razorpay payment gateway integration for wallet recharge.
"""
import os
import hashlib
import hmac
from typing import Optional, Dict, Any
import razorpay

# Initialize Razorpay client
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)) if RAZORPAY_KEY_ID else None


def create_order(amount: float, user_id: int, email: str, phone: str = "9999999999") -> Optional[Dict[str, Any]]:
    """
    Create Razorpay order for wallet recharge.
    
    Args:
        amount: Amount in INR
        user_id: User ID
        email: User email
        phone: User phone (optional, default: placeholder)
    
    Returns:
        Order details or None if creation fails
    """
    if not razorpay_client:
        return None
    
    try:
        # Amount in paise (1 INR = 100 paise)
        amount_paise = int(amount * 100)
        
        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"user_{user_id}_{int(time.time())}",
            "payment_capture": 1,  # Auto capture payment
            "notes": {
                "user_id": str(user_id),
                "email": email,
                "type": "wallet_recharge"
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        return {
            "order_id": order["id"],
            "amount": amount,
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID
        }
    except Exception as e:
        print(f"Razorpay order creation failed: {str(e)}")
        return None


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Verify Razorpay payment signature.
    
    Args:
        order_id: Razorpay order ID
        payment_id: Razorpay payment ID
        signature: Razorpay signature from payment response
    
    Returns:
        True if signature is valid, False otherwise
    """
    if not RAZORPAY_KEY_SECRET:
        return False
    
    try:
        # Create the message to verify
        message = f"{order_id}|{payment_id}"
        
        # Generate signature using HMAC-SHA256
        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return generated_signature == signature
    except Exception as e:
        print(f"Signature verification failed: {str(e)}")
        return False


def fetch_payment_details(payment_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch payment details from Razorpay.
    
    Args:
        payment_id: Razorpay payment ID
    
    Returns:
        Payment details or None if fetch fails
    """
    if not razorpay_client:
        return None
    
    try:
        payment = razorpay_client.payment.fetch(payment_id)
        return {
            "payment_id": payment.get("id"),
            "order_id": payment.get("order_id"),
            "amount": payment.get("amount") / 100,  # Convert from paise to INR
            "currency": payment.get("currency"),
            "status": payment.get("status"),
            "method": payment.get("method"),
            "email": payment.get("email"),
            "contact": payment.get("contact"),
            "created_at": payment.get("created_at")
        }
    except Exception as e:
        print(f"Failed to fetch payment details: {str(e)}")
        return None


import time

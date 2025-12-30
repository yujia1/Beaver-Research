import stripe
from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from routers.auth import get_current_user
import os
from datetime import datetime

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
router = APIRouter(prefix="/api/payment", tags=["payment"])

# Price ID should ideally be in env or config, but for now we can fetch or hardcode a placeholder
# In production, you'd likely have multiple prices/products.
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "price_1234567890") 
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

@router.post("/create-checkout-session")
def create_checkout_session(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a Stripe Checkout Session for a subscription.
    """
    if not stripe.api_key:
         raise HTTPException(status_code=500, detail="Stripe API key not configured")

    try:
        # Create session
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[{
                'price': STRIPE_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/payment/cancel",
            client_reference_id=str(current_user.id),
            metadata={
                "user_id": str(current_user.id)
            }
        )
        return {"url": checkout_session.url}
    except Exception as e:
        print(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=f"Error creating checkout session: {str(e)}")

@router.post("/webhook")
async def stripe_webhook(
    request: Request, 
    stripe_signature: str = Header(None), 
    db: Session = Depends(get_db)
):
    """
    Handle Stripe Webhooks to update user status
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    payload = await request.body()
    
    if not webhook_secret:
        # If no secret configured, we can't verify, but for dev we might log
        print("Webhook secret not set")
        raise HTTPException(status_code=500, detail="Webhook secret not set")

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_checkout_session_completed(session, db)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        await handle_subscription_deleted(subscription, db)
        
    return {"status": "success"}

async def handle_checkout_session_completed(session, db: Session):
    user_id = session.get('client_reference_id')
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    
    if user_id:
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        if user:
            user.has_paid = True
            user.stripe_customer_id = customer_id
            user.stripe_subscription_id = subscription_id
            user.payment_date = datetime.utcnow()
            db.commit()
            print(f"User {user_id} upgraded to premium via Stripe.")

async def handle_subscription_deleted(subscription, db: Session):
    # If a subscription is canceled/deleted, we might want to revoke access
    # Need to find user by customer_id or subscription_id
    customer_id = subscription.get('customer')
    if customer_id:
        user = db.query(models.User).filter(models.User.stripe_customer_id == customer_id).first()
        if user:
            user.has_paid = False
            db.commit()
            print(f"User {user.id} subscription canceled.")

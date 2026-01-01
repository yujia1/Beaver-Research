import stripe
from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from routers.admin.auth import get_current_user
import os
from datetime import datetime
from pydantic import BaseModel

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
router = APIRouter(prefix="/api/payment", tags=["payment"])

# Price IDs for monthly and annual subscriptions
STRIPE_PRICE_MONTHLY = os.getenv("STRIPE_PRICE_MONTHLY")
STRIPE_PRICE_ANNUAL = os.getenv("STRIPE_PRICE_ANNUAL")
FRONTEND_URL = os.getenv("FRONTEND_URL")

class CheckoutRequest(BaseModel):
    plan: str  # "monthly" or "annual"

@router.post("/create-checkout-session")
def create_checkout_session(
    request: CheckoutRequest,
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a Stripe Checkout Session for embedded checkout.
    Supports both monthly and annual subscriptions.
    Returns the client_secret for embedding the checkout form.
    """
    if not stripe.api_key:
         raise HTTPException(status_code=500, detail="Stripe API key not configured")

    # Select price based on plan
    if request.plan == "annual":
        price_id = STRIPE_PRICE_ANNUAL
    elif request.plan == "monthly":
        price_id = STRIPE_PRICE_MONTHLY
    else:
        raise HTTPException(status_code=400, detail="Invalid plan. Must be 'monthly' or 'annual'")

    try:
        # Create session with ui_mode='embedded' for embedded checkout
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            ui_mode='embedded',  # Enable embedded checkout
            return_url=f"{FRONTEND_URL}/payment/return?session_id={{CHECKOUT_SESSION_ID}}",
            client_reference_id=str(current_user.id),
            metadata={
                "user_id": str(current_user.id),
                "plan": request.plan
            }
        )
        # Return client_secret for embedded checkout
        return {
            "clientSecret": checkout_session.client_secret,
            "sessionId": checkout_session.id
        }
    except Exception as e:
        print(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=f"Error creating checkout session: {str(e)}")

@router.get("/session-status")
def get_session_status(
    session_id: str,
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve the status of a Checkout Session.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "status": session.status,
            "customer_email": session.customer_details.email if session.customer_details else None,
            "payment_status": session.payment_status
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving session: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(
    request: Request, 
    stripe_signature: str = Header(None), 
    db: Session = Depends(get_db)
):
    """
    Handle Stripe Webhooks to update user status.
    Handles:
    - checkout.session.completed (first payment)
    - invoice.payment_succeeded (recurring payments)
    - invoice.payment_failed (failed renewals)
    - customer.subscription.deleted (cancellations)
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    payload = await request.body()
    
    if not webhook_secret:
        print("WARNING: Webhook secret not set - skipping signature verification")
        # In development, you might want to process anyway, but log the warning
        # In production, this should raise an error
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        print(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    event_type = event['type']
    print(f"Received webhook event: {event_type}")
    
    if event_type == 'checkout.session.completed':
        # First payment succeeded
        session = event['data']['object']
        await handle_checkout_session_completed(session, db)
        
    elif event_type == 'invoice.payment_succeeded':
        # Recurring payment succeeded (monthly/annual renewal)
        invoice = event['data']['object']
        await handle_invoice_payment_succeeded(invoice, db)
        
    elif event_type == 'invoice.payment_failed':
        # Payment failed (e.g., card declined on renewal)
        invoice = event['data']['object']
        await handle_invoice_payment_failed(invoice, db)
        
    elif event_type == 'customer.subscription.deleted':
        # Subscription canceled
        subscription = event['data']['object']
        await handle_subscription_deleted(subscription, db)
    
    return {"status": "success"}


async def handle_checkout_session_completed(session, db: Session):
    """
    Handle successful checkout (first payment).
    Sets user as paid and stores Stripe customer/subscription info.
    """
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
            
            # Get subscription details to set expiry
            if subscription_id:
                try:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    user.stripe_current_period_end = datetime.fromtimestamp(subscription.current_period_end)
                except Exception as e:
                    print(f"Error retrieving subscription: {e}")
            
            db.commit()
            print(f"✅ User {user_id} upgraded to premium (checkout completed)")


async def handle_invoice_payment_succeeded(invoice, db: Session):
    """
    Handle successful recurring payment.
    Updates user's payment status and extends subscription period.
    """
    customer_id = invoice.get('customer')
    subscription_id = invoice.get('subscription')
    
    if customer_id:
        user = db.query(models.User).filter(models.User.stripe_customer_id == customer_id).first()
        if user:
            # Ensure user is marked as paid
            user.has_paid = True
            user.payment_date = datetime.utcnow()
            
            # Update subscription period end
            if subscription_id:
                try:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    user.stripe_current_period_end = datetime.fromtimestamp(subscription.current_period_end)
                except Exception as e:
                    print(f"Error retrieving subscription: {e}")
            
            db.commit()
            print(f"✅ User {user.id} payment renewed (invoice paid)")


async def handle_invoice_payment_failed(invoice, db: Session):
    """
    Handle failed recurring payment.
    Optionally revoke access or send notification.
    """
    customer_id = invoice.get('customer')
    
    if customer_id:
        user = db.query(models.User).filter(models.User.stripe_customer_id == customer_id).first()
        if user:
            # You can choose to:
            # 1. Immediately revoke access: user.has_paid = False
            # 2. Send notification and give grace period
            # 3. Wait for subscription.deleted event
            
            # For now, we'll log it and let Stripe retry
            # Stripe will eventually send subscription.deleted if all retries fail
            print(f"⚠️ Payment failed for user {user.id} - Stripe will retry")
            
            # Optionally, you could send an email notification here
            # send_payment_failed_email(user.email)


async def handle_subscription_deleted(subscription, db: Session):
    """
    Handle subscription cancellation.
    Revokes user's premium access.
    """
    customer_id = subscription.get('customer')
    
    if customer_id:
        user = db.query(models.User).filter(models.User.stripe_customer_id == customer_id).first()
        if user:
            user.has_paid = False
            user.stripe_current_period_end = None
            db.commit()
            print(f"❌ User {user.id} subscription canceled")

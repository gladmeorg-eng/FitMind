# ============================================================
# FILE: services/ai-engine/app/routers/billing.py
# Complete Billing & Stripe Integration
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import stripe
import os

from app.database import get_db
from app.services.sendgrid_service import sendgrid_service
from app.services.twilio_service import twilio_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

router = APIRouter()

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# ============================================================
# INVOICE MANAGEMENT
# ============================================================

class InvoiceCreate(BaseModel):
    member_id: str
    amount: float
    description: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    amount: float
    status: str
    stripe_invoice_id: Optional[str]

@router.get("/invoices")
async def list_invoices(
    gym_id: str,
    member_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List invoices with optional filters."""
    offset = (page - 1) * limit

    query = """
        SELECT i.*, m.first_name, m.last_name, m.email
        FROM invoices i
        JOIN members m ON m.id = i.member_id
        WHERE i.gym_id = :gym_id
    """
    params = {"gym_id": gym_id}

    if member_id:
        query += " AND i.member_id = :member_id"
        params["member_id"] = member_id
    if status:
        query += " AND i.status = :status"
        params["status"] = status

    query += " ORDER BY i.created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    result = await db.execute(text(query), params)
    invoices = result.mappings().all()

    # Get totals
    totals = await db.execute(text("""
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'paid' THEN total_amount END), 0) as total_revenue,
            COALESCE(SUM(CASE WHEN status = 'pending' THEN total_amount END), 0) as total_outstanding
        FROM invoices WHERE gym_id = :gym_id
    """), {"gym_id": gym_id})
    totals_data = totals.mappings().first()

    return {
        "data": invoices,
        "pagination": {"page": page, "limit": limit},
        "totals": totals_data
    }

@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(
    gym_id: str,
    invoice: InvoiceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new invoice and optionally charge immediately."""

    # Get member details
    member = await db.execute(text("""
        SELECT * FROM members WHERE id = :member_id AND gym_id = :gym_id
    """), {"member_id": invoice.member_id, "gym_id": gym_id})
    member_data = member.mappings().first()

    if not member_data:
        raise HTTPException(status_code=404, detail="Member not found")

    # Generate invoice number
    invoice_number = f"INV-{gym_id[:4].upper()}-{datetime.now().strftime('%Y%m%d')}-{os.urandom(2).hex().upper()}"

    # Create Stripe invoice
    stripe_invoice = None
    if member_data.get("stripe_customer_id"):
        stripe_invoice = stripe.InvoiceItem.create(
            customer=member_data["stripe_customer_id"],
            amount=int(invoice.amount * 100),  # cents
            currency="usd",
            description=invoice.description or "Gym membership",
        )
        stripe_invoice = stripe.Invoice.create(
            customer=member_data["stripe_customer_id"],
            auto_advance=True,  # Auto-finalize and charge
        )

    # Save to database
    result = await db.execute(text("""
        INSERT INTO invoices 
        (gym_id, member_id, invoice_number, amount, tax_amount, total_amount, 
         description, period_start, period_end, status, stripe_invoice_id, created_at)
        VALUES (:gym_id, :member_id, :invoice_number, :amount, 0, :amount,
                :description, :period_start, :period_end, 'pending', :stripe_id, NOW())
        RETURNING id
    """), {
        "gym_id": gym_id,
        "member_id": invoice.member_id,
        "invoice_number": invoice_number,
        "amount": invoice.amount,
        "description": invoice.description,
        "period_start": invoice.period_start,
        "period_end": invoice.period_end,
        "stripe_id": stripe_invoice.id if stripe_invoice else None
    })

    invoice_id = result.scalar()
    await db.commit()

    return {
        "id": str(invoice_id),
        "invoice_number": invoice_number,
        "amount": invoice.amount,
        "status": "pending",
        "stripe_invoice_id": stripe_invoice.id if stripe_invoice else None
    }

# ============================================================
# FAILED PAYMENT RECOVERY (The Money Machine)
# ============================================================

@router.post("/invoices/{invoice_id}/retry")
async def retry_payment(
    gym_id: str,
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Manually retry a failed payment."""

    invoice = await db.execute(text("""
        SELECT i.*, m.stripe_customer_id, m.payment_method_id, m.email, m.phone,
               m.first_name, m.last_name
        FROM invoices i
        JOIN members m ON m.id = i.member_id
        WHERE i.id = :invoice_id AND i.gym_id = :gym_id
    """), {"invoice_id": invoice_id, "gym_id": gym_id})
    invoice_data = invoice.mappings().first()

    if not invoice_data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice_data["status"] == "paid":
        return {"status": "already_paid", "message": "This invoice is already paid"}

    # Attempt Stripe payment
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(invoice_data["total_amount"] * 100),
            currency="usd",
            customer=invoice_data["stripe_customer_id"],
            payment_method=invoice_data["payment_method_id"],
            off_session=True,
            confirm=True,
            metadata={
                "invoice_id": invoice_id,
                "gym_id": gym_id,
                "member_id": invoice_data["member_id"]
            }
        )

        # Update invoice
        await db.execute(text("""
            UPDATE invoices 
            SET status = 'paid', paid_at = NOW(), 
                stripe_payment_intent_id = :payment_intent_id,
                retry_count = retry_count + 1, last_retry_at = NOW()
            WHERE id = :invoice_id
        """), {
            "invoice_id": invoice_id,
            "payment_intent_id": payment_intent.id
        })

        # Log payment
        await db.execute(text("""
            INSERT INTO payments (gym_id, member_id, invoice_id, amount, currency, 
                                  status, payment_method, stripe_payment_intent_id, created_at)
            VALUES (:gym_id, :member_id, :invoice_id, :amount, 'usd', 'succeeded', 
                    'card', :payment_intent_id, NOW())
        """), {
            "gym_id": gym_id,
            "member_id": invoice_data["member_id"],
            "invoice_id": invoice_id,
            "amount": invoice_data["total_amount"],
            "payment_intent_id": payment_intent.id
        })

        await db.commit()

        # Send success notification
        await sendgrid_service.send_email(
            to=invoice_data["email"],
            subject="Payment Successful - FitMind AI",
            body=f"""Hi {invoice_data["first_name"]},

Your payment of ${invoice_data["total_amount"]} has been successfully processed.

Thank you for your continued membership!

FitMind AI Team"""
        )

        return {
            "status": "succeeded",
            "payment_intent_id": payment_intent.id,
            "amount": invoice_data["total_amount"]
        }

    except stripe.error.CardError as e:
        # Card declined - update retry count and schedule next attempt
        error_code = e.code
        decline_code = e.decline_code if hasattr(e, 'decline_code') else None

        new_retry_count = invoice_data["retry_count"] + 1
        next_retry = datetime.now() + timedelta(hours=48)

        # After 3 retries, mark as failed and alert
        if new_retry_count >= 3:
            await db.execute(text("""
                UPDATE invoices 
                SET status = 'failed', retry_count = :retry_count,
                    failure_reason = :failure_reason, last_retry_at = NOW()
                WHERE id = :invoice_id
            """), {
                "invoice_id": invoice_id,
                "retry_count": new_retry_count,
                "failure_reason": f"{error_code}: {decline_code}"
            })

            # Create retention alert for failed payment
            await db.execute(text("""
                INSERT INTO retention_alerts 
                (gym_id, member_id, alert_type, severity, description, 
                 ai_recommendation, status, created_at)
                VALUES (:gym_id, :member_id, 'payment_failed', 'high',
                        'Payment failed after 3 attempts: ' || :failure_reason,
                        'Contact member to update payment method or offer freeze option',
                        'open', NOW())
            """), {
                "gym_id": gym_id,
                "member_id": invoice_data["member_id"],
                "failure_reason": f"{error_code}: {decline_code}"
            })

            # Send dunning email
            await sendgrid_service.send_email(
                to=invoice_data["email"],
                subject="Action Required: Update Your Payment Method",
                body=f"""Hi {invoice_data["first_name"]},

We were unable to process your recent payment of ${invoice_data["total_amount"]}.

Please update your payment method to avoid any interruption to your membership.

Update Payment: [Link]
Or reply to this email and we'll help you out.

FitMind AI Team"""
            )
        else:
            await db.execute(text("""
                UPDATE invoices 
                SET retry_count = :retry_count, next_retry_at = :next_retry,
                    last_retry_at = NOW(), failure_reason = :failure_reason
                WHERE id = :invoice_id
            """), {
                "invoice_id": invoice_id,
                "retry_count": new_retry_count,
                "next_retry": next_retry,
                "failure_reason": f"{error_code}: {decline_code}"
            })

        await db.commit()

        return {
            "status": "failed",
            "error": str(e),
            "retry_count": new_retry_count,
            "next_retry": next_retry.isoformat() if new_retry_count < 3 else None
        }

# ============================================================
# STRIPE WEBHOOK HANDLER (The Magic)
# ============================================================

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhooks for payment events."""

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    # Handle different event types
    handlers = {
        "invoice.payment_succeeded": handle_payment_succeeded,
        "invoice.payment_failed": handle_payment_failed,
        "customer.subscription.created": handle_subscription_created,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_cancelled,
        "payment_intent.payment_failed": handle_payment_intent_failed,
        "payment_intent.succeeded": handle_payment_intent_succeeded,
    }

    handler = handlers.get(event_type)
    if handler:
        background_tasks.add_task(handler, data, db)

    return {"status": "success", "event": event_type}

async def handle_payment_succeeded(data: dict, db: AsyncSession):
    """Handle successful payment - update invoice, notify member."""
    invoice_id = data.get("metadata", {}).get("invoice_id")
    if not invoice_id:
        return

    # Update invoice status
    await db.execute(text("""
        UPDATE invoices 
        SET status = 'paid', paid_at = NOW(), 
            stripe_payment_intent_id = :payment_intent_id
        WHERE id = :invoice_id
    """), {
        "invoice_id": invoice_id,
        "payment_intent_id": data.get("payment_intent")
    })

    # Get member info for notification
    member = await db.execute(text("""
        SELECT m.email, m.first_name, m.phone
        FROM invoices i
        JOIN members m ON m.id = i.member_id
        WHERE i.id = :invoice_id
    """), {"invoice_id": invoice_id})
    member_data = member.mappings().first()

    if member_data:
        # Send receipt email
        await sendgrid_service.send_email(
            to=member_data["email"],
            subject="Payment Receipt - FitMind AI",
            body=f"""Hi {member_data["first_name"]},

Your payment has been successfully processed.

Amount: ${data.get("amount_due", 0) / 100:.2f}
Date: {datetime.now().strftime('%B %d, %Y')}
Invoice: {invoice_id}

Thank you!

FitMind AI Team"""
        )

    await db.commit()

async def handle_payment_failed(data: dict, db: AsyncSession):
    """Handle failed payment - trigger retry logic, alert retention system."""
    invoice_id = data.get("metadata", {}).get("invoice_id")
    if not invoice_id:
        return

    # Get invoice and member details
    invoice = await db.execute(text("""
        SELECT i.*, m.id as member_id, m.email, m.first_name, m.phone,
               m.churn_risk, m.retention_score
        FROM invoices i
        JOIN members m ON m.id = i.member_id
        WHERE i.id = :invoice_id
    """), {"invoice_id": invoice_id})
    invoice_data = invoice.mappings().first()

    if not invoice_data:
        return

    # Update invoice
    await db.execute(text("""
        UPDATE invoices 
        SET status = 'failed', 
            failure_reason = :failure_reason,
            retry_count = retry_count + 1,
            last_retry_at = NOW()
        WHERE id = :invoice_id
    """), {
        "invoice_id": invoice_id,
        "failure_reason": data.get("last_payment_error", {}).get("decline_code", "unknown")
    })

    # Create retention alert
    await db.execute(text("""
        INSERT INTO retention_alerts 
        (gym_id, member_id, alert_type, severity, description, 
         ai_recommendation, status, created_at)
        VALUES (:gym_id, :member_id, 'payment_failed', 'high',
                'Payment failed: ' || :failure_reason,
                'Immediate outreach required - risk of churn',
                'open', NOW())
    """), {
        "gym_id": invoice_data["gym_id"],
        "member_id": invoice_data["member_id"],
        "failure_reason": data.get("last_payment_error", {}).get("decline_code", "unknown")
    })

    # Send immediate SMS + Email
    await sendgrid_service.send_email(
        to=invoice_data["email"],
        subject="⚠️ Payment Issue - Please Update Your Card",
        body=f"""Hi {invoice_data["first_name"]},

We couldn't process your recent payment.

This usually happens when:
• Your card expired
• Insufficient funds
• Bank security block

Please update your payment method to keep your membership active:
[Update Payment Link]

Need help? Reply to this email or call us.

FitMind AI Team"""
    )

    if invoice_data.get("phone"):
        await twilio_service.send_sms(
            to=invoice_data["phone"],
            body=f"Hi {invoice_data["first_name"]}, we couldn't process your gym payment. Please update your card: [link] -FitMind AI"
        )

    await db.commit()

async def handle_subscription_created(data: dict, db: AsyncSession):
    """Handle new subscription - welcome sequence."""
    customer_id = data.get("customer")

    # Find member by Stripe customer ID
    member = await db.execute(text("""
        SELECT * FROM members WHERE stripe_customer_id = :customer_id
    """), {"customer_id": customer_id})
    member_data = member.mappings().first()

    if member_data:
        # Update membership status
        await db.execute(text("""
            UPDATE members 
            SET membership_status = 'active',
                membership_start_date = CURRENT_DATE,
                membership_end_date = CURRENT_DATE + INTERVAL '1 month'
            WHERE id = :member_id
        """), {"member_id": member_data["id"]})

        # Send welcome email
        await sendgrid_service.send_email(
            to=member_data["email"],
            subject="Welcome to FitMind AI! 🎉",
            body=f"""Hi {member_data["first_name"]},

Welcome! Your membership is now active.

Here's what you can do:
📱 Download our app to book classes
🏋️ Check out this week's schedule
👥 Refer a friend and get $25 credit

Let's crush your fitness goals together!

FitMind AI Team"""
        )

        await db.commit()

async def handle_subscription_cancelled(data: dict, db: AsyncSession):
    """Handle cancellation - exit survey, win-back attempt."""
    customer_id = data.get("customer")

    member = await db.execute(text("""
        SELECT * FROM members WHERE stripe_customer_id = :customer_id
    """), {"customer_id": customer_id})
    member_data = member.mappings().first()

    if member_data:
        # Update status
        await db.execute(text("""
            UPDATE members 
            SET membership_status = 'cancelled'
            WHERE id = :member_id
        """), {"member_id": member_data["id"]})

        # Create exit survey campaign
        await db.execute(text("""
            INSERT INTO retention_campaigns 
            (gym_id, name, campaign_type, target_segment, subject, body_text, status, created_at)
            VALUES (:gym_id, 'Exit Survey', 'survey', 'cancelled_members',
                    'Help us improve - Quick 2-min survey',
                    'We''re sorry to see you go! Help us improve by sharing your feedback.',
                    'draft', NOW())
        """), {"gym_id": member_data["gym_id"]})

        # Send win-back offer after 7 days (scheduled via Celery)
        # This would be queued as a delayed task

        await db.commit()

async def handle_payment_intent_succeeded(data: dict, db: AsyncSession):
    """Track successful payment for analytics."""
    # Log to activity for AI training
    metadata = data.get("metadata", {})
    member_id = metadata.get("member_id")

    if member_id:
        await db.execute(text("""
            INSERT INTO activity_logs 
            (gym_id, member_id, activity_type, details, created_at)
            VALUES (:gym_id, :member_id, 'payment_made', 
                    jsonb_build_object('amount', :amount, 'payment_method', :method),
                    NOW())
        """), {
            "gym_id": metadata.get("gym_id"),
            "member_id": member_id,
            "amount": data.get("amount", 0) / 100,
            "method": data.get("charges", {}).get("data", [{}])[0].get("payment_method_details", {}).get("type", "card")
        })
        await db.commit()

async def handle_payment_intent_failed(data: dict, db: AsyncSession):
    """Log failed payment for retry optimization."""
    metadata = data.get("metadata", {})

    await db.execute(text("""
        INSERT INTO activity_logs 
        (gym_id, member_id, activity_type, details, created_at)
        VALUES (:gym_id, :member_id, 'payment_failed',
                jsonb_build_object('error', :error, 'code', :code),
                NOW())
    """), {
        "gym_id": metadata.get("gym_id"),
        "member_id": metadata.get("member_id"),
        "error": data.get("last_payment_error", {}).get("message", "unknown"),
        "code": data.get("last_payment_error", {}).get("decline_code", "unknown")
    })
    await db.commit()

async def handle_subscription_updated(data: dict, db: AsyncSession):
    """Handle subscription changes - plan upgrades/downgrades."""
    customer_id = data.get("customer")

    # Update member's plan details
    await db.execute(text("""
        UPDATE members 
        SET monthly_fee = :amount / 100.0,
            membership_end_date = :current_period_end::date
        WHERE stripe_customer_id = :customer_id
    """), {
        "customer_id": customer_id,
        "amount": data.get("plan", {}).get("amount", 0),
        "current_period_end": datetime.fromtimestamp(data.get("current_period_end", 0)).strftime('%Y-%m-%d')
    })
    await db.commit()

# ============================================================
# BILLING STATS & ANALYTICS
# ============================================================

@router.get("/stats")
async def get_billing_stats(
    gym_id: str,
    period: str = "month",
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive billing statistics."""

    # Date range based on period
    if period == "today":
        date_filter = "CURRENT_DATE"
    elif period == "week":
        date_filter = "CURRENT_DATE - INTERVAL '7 days'"
    elif period == "month":
        date_filter = "CURRENT_DATE - INTERVAL '30 days'"
    else:
        date_filter = "CURRENT_DATE - INTERVAL '30 days'"

    stats = await db.execute(text("""
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'paid' THEN total_amount END), 0) as total_revenue,
            COALESCE(SUM(CASE WHEN status = 'pending' THEN total_amount END), 0) as outstanding,
            COUNT(CASE WHEN status = 'paid' THEN 1 END) as successful_payments,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_payments,
            COUNT(CASE WHEN status = 'pending' AND retry_count > 0 THEN 1 END) as retrying_payments,
            AVG(CASE WHEN status = 'paid' THEN total_amount END) as avg_payment,
            (SELECT COUNT(*) FROM members WHERE gym_id = :gym_id AND membership_status = 'active') as active_members,
            (SELECT COALESCE(SUM(monthly_fee), 0) FROM members WHERE gym_id = :gym_id AND membership_status = 'active') as mrr
        FROM invoices
        WHERE gym_id = :gym_id AND created_at >= """ + date_filter + """
    """), {"gym_id": gym_id})

    stats_data = stats.mappings().first()

    # Calculate recovery rate
    total_attempted = stats_data["successful_payments"] + stats_data["failed_payments"]
    recovery_rate = (stats_data["successful_payments"] / total_attempted * 100) if total_attempted > 0 else 100

    # Upcoming renewals (next 7 days)
    renewals = await db.execute(text("""
        SELECT COUNT(*) as count
        FROM members
        WHERE gym_id = :gym_id 
        AND membership_status = 'active'
        AND membership_end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
    """), {"gym_id": gym_id})
    renewals_data = renewals.mappings().first()

    return {
        "period": period,
        "total_revenue": round(stats_data["total_revenue"] or 0, 2),
        "mrr": round(stats_data["mrr"] or 0, 2),
        "outstanding": round(stats_data["outstanding"] or 0, 2),
        "successful_payments": stats_data["successful_payments"],
        "failed_payments": stats_data["failed_payments"],
        "retrying_payments": stats_data["retrying_payments"],
        "recovery_rate": round(recovery_rate, 1),
        "avg_payment": round(stats_data["avg_payment"] or 0, 2),
        "active_members": stats_data["active_members"],
        "upcoming_renewals": renewals_data["count"],
        "projected_mrr": round((stats_data["mrr"] or 0) * 1.08, 2)  # 8% growth assumption
    }

# ============================================================
# AUTOMATED BILLING SETUP
# ============================================================

@router.post("/setup-recurring")
async def setup_recurring_billing(
    gym_id: str,
    member_id: str,
    payment_method_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Set up automatic recurring billing for a member."""

    member = await db.execute(text("""
        SELECT * FROM members WHERE id = :member_id AND gym_id = :gym_id
    """), {"member_id": member_id, "gym_id": gym_id})
    member_data = member.mappings().first()

    if not member_data:
        raise HTTPException(status_code=404, detail="Member not found")

    # Create or get Stripe customer
    if not member_data.get("stripe_customer_id"):
        customer = stripe.Customer.create(
            email=member_data["email"],
            name=f"{member_data["first_name"]} {member_data["last_name"]}",
            metadata={"member_id": member_id, "gym_id": gym_id}
        )

        await db.execute(text("""
            UPDATE members 
            SET stripe_customer_id = :customer_id,
                payment_method_id = :payment_method_id
            WHERE id = :member_id
        """), {
            "member_id": member_id,
            "customer_id": customer.id,
            "payment_method_id": payment_method_id
        })
    else:
        # Attach payment method to existing customer
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=member_data["stripe_customer_id"]
        )

        # Set as default
        stripe.Customer.modify(
            member_data["stripe_customer_id"],
            invoice_settings={"default_payment_method": payment_method_id}
        )

        await db.execute(text("""
            UPDATE members SET payment_method_id = :payment_method_id
            WHERE id = :member_id
        """), {
            "member_id": member_id,
            "payment_method_id": payment_method_id
        })

    await db.commit()

    return {
        "status": "success",
        "message": "Recurring billing set up successfully",
        "member_id": member_id
    }

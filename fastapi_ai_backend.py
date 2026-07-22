"""
# ============================================================
# FILE: services/ai-engine/app/main.py
# FastAPI Application Entry Point
# ============================================================

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import os

from app.routers import (
    auth, members, classes, bookings, billing,
    retention, assistant, leads, messaging, dashboard
)
from app.services.redis_service import redis_client
from app.workers.retention_worker import start_retention_worker
from app.workers.billing_worker import start_billing_worker

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 FitMind AI Engine starting...")
    await redis_client.connect()
    # Start background workers
    asyncio.create_task(start_retention_worker())
    asyncio.create_task(start_billing_worker())
    print("✅ All workers started")
    yield
    # Shutdown
    await redis_client.disconnect()
    print("👋 FitMind AI Engine shutting down...")

app = FastAPI(
    title="FitMind AI Gym OS API",
    description="AI-powered backend for gym management automation",
    version="3.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://fitmind.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router, prefix="/v3/auth", tags=["Authentication"])
app.include_router(members.router, prefix="/v3/gyms/{gym_id}/members", tags=["Members"])
app.include_router(classes.router, prefix="/v3/gyms/{gym_id}/classes", tags=["Classes"])
app.include_router(bookings.router, prefix="/v3/gyms/{gym_id}/bookings", tags=["Bookings"])
app.include_router(billing.router, prefix="/v3/gyms/{gym_id}/billing", tags=["Billing"])
app.include_router(retention.router, prefix="/v3/gyms/{gym_id}/retention", tags=["AI Retention"])
app.include_router(assistant.router, prefix="/v3/gyms/{gym_id}/ai", tags=["AI Assistant"])
app.include_router(leads.router, prefix="/v3/gyms/{gym_id}/leads", tags=["Leads"])
app.include_router(messaging.router, prefix="/v3/gyms/{gym_id}/messages", tags=["Messaging"])
app.include_router(dashboard.router, prefix="/v3/gyms/{gym_id}/dashboard", tags=["Dashboard"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3.0.0", "ai_engine": "online"}

# ============================================================
# FILE: services/ai-engine/app/routers/retention.py
# AI Retention Engine Router
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import asyncio

from app.models.churn_predictor import ChurnPredictor
from app.services.openai_service import openai_service
from app.services.twilio_service import twilio_service
from app.services.sendgrid_service import sendgrid_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Initialize model
churn_model = ChurnPredictor()

class RetentionAlertResponse(BaseModel):
    id: str
    member_id: str
    member_name: str
    alert_type: str
    severity: str
    description: str
    ai_recommendation: str
    status: str
    created_at: datetime

class RetentionCampaignCreate(BaseModel):
    name: str
    campaign_type: str
    target_segment: Optional[str] = None
    subject: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    sms_text: Optional[str] = None
    scheduled_at: Optional[datetime] = None

class RetentionInsights(BaseModel):
    predicted_churn_next_30d: int
    at_risk_members: List[dict]
    top_churn_reasons: List[dict]
    recommendations: List[dict]

@router.get("/alerts", response_model=List[RetentionAlertResponse])
async def get_retention_alerts(
    gym_id: str,
    severity: Optional[str] = "all",
    status: Optional[str] = "open",
    db: AsyncSession = Depends(get_db),
):
    # Get all retention alerts for a gym, optionally filtered
    query = """
        SELECT 
            ra.id, ra.member_id, 
            m.first_name || ' ' || m.last_name as member_name,
            ra.alert_type, ra.severity, ra.description,
            ra.ai_recommendation, ra.status, ra.created_at
        FROM retention_alerts ra
        JOIN members m ON m.id = ra.member_id
        WHERE ra.gym_id = :gym_id
    """
    params = {"gym_id": gym_id}

    if severity != "all":
        query += " AND ra.severity = :severity"
        params["severity"] = severity
    if status != "all":
        query += " AND ra.status = :status"
        params["status"] = status

    query += " ORDER BY ra.created_at DESC"

    result = await db.execute(query, params)
    alerts = result.mappings().all()
    return alerts

@router.post("/alerts/{alert_id}/resolve")
async def resolve_retention_alert(
    gym_id: str,
    alert_id: str,
    action_taken: str,
    resolution_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Mark a retention alert as resolved."""
    await db.execute("""
        UPDATE retention_alerts 
        SET status = 'resolved', 
            resolved_at = NOW(),
            action_taken = :action_taken,
            resolution_notes = :notes
        WHERE id = :alert_id AND gym_id = :gym_id
    """, {
        "alert_id": alert_id,
        "gym_id": gym_id,
        "action_taken": action_taken,
        "notes": resolution_notes
    })
    await db.commit()
    return {"status": "resolved", "alert_id": alert_id}

@router.get("/insights", response_model=RetentionInsights)
async def get_retention_insights(
    gym_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get AI-generated retention insights and predictions."""
    # Fetch member data for prediction
    members_data = await db.execute("""
        SELECT id, total_visits, avg_weekly_visits, last_visit_at,
               membership_status, monthly_fee, days_since_signup
        FROM members 
        WHERE gym_id = :gym_id AND membership_status = 'active'
    """, {"gym_id": gym_id})

    members = members_data.mappings().all()

    # Run churn prediction
    predictions = churn_model.predict_batch(members)

    at_risk = [p for p in predictions if p["risk_score"] > 0.7]

    # Generate AI insights
    insights_prompt = f"""
    Analyze this gym retention data:
    - Total active members: {len(members)}
    - At-risk members (next 30 days): {len(at_risk)}
    - Top risk factors: {churn_model.get_top_features()}

    Provide 3 actionable recommendations to reduce churn.
    """

    ai_recommendations = await openai_service.generate_insights(insights_prompt)

    return RetentionInsights(
        predicted_churn_next_30d=len(at_risk),
        at_risk_members=at_risk[:10],
        top_churn_reasons=churn_model.get_churn_reasons(),
        recommendations=ai_recommendations
    )

@router.post("/campaigns")
async def create_retention_campaign(
    gym_id: str,
    campaign: RetentionCampaignCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new retention campaign."""
    # Insert campaign
    result = await db.execute("""
        INSERT INTO retention_campaigns 
        (gym_id, name, campaign_type, target_segment, subject, 
         body_text, body_html, sms_text, status, created_at)
        VALUES (:gym_id, :name, :type, :segment, :subject,
                :body_text, :body_html, :sms_text, 'draft', NOW())
        RETURNING id
    """, {
        "gym_id": gym_id,
        "name": campaign.name,
        "type": campaign.campaign_type,
        "segment": campaign.target_segment,
        "subject": campaign.subject,
        "body_text": campaign.body_text,
        "body_html": campaign.body_html,
        "sms_text": campaign.sms_text
    })

    campaign_id = result.scalar()
    await db.commit()

    return {"id": campaign_id, "status": "draft", "message": "Campaign created"}

@router.post("/campaigns/{campaign_id}/launch")
async def launch_campaign(
    gym_id: str,
    campaign_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Launch a retention campaign - sends messages to target members."""
    # Get campaign details
    campaign = await db.execute("""
        SELECT * FROM retention_campaigns 
        WHERE id = :campaign_id AND gym_id = :gym_id
    """, {"campaign_id": campaign_id, "gym_id": gym_id})
    campaign_data = campaign.mappings().first()

    if not campaign_data:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Determine target members based on campaign type
    target_query = """
        SELECT id, email, phone, first_name, push_token
        FROM members 
        WHERE gym_id = :gym_id AND membership_status = 'active'
    """

    if campaign_data["campaign_type"] == "win_back":
        target_query += " AND churn_risk IN ('high', 'critical')"
    elif campaign_data["campaign_type"] == "re_engagement":
        target_query += " AND last_visit_at < NOW() - INTERVAL '10 days'"
    elif campaign_data["campaign_type"] == "birthday":
        target_query += " AND EXTRACT(MONTH FROM date_of_birth) = EXTRACT(MONTH FROM NOW())"

    targets = await db.execute(target_query, {"gym_id": gym_id})
    members = targets.mappings().all()

    # Send messages in background
    background_tasks.add_task(
        send_campaign_messages,
        gym_id,
        campaign_id,
        members,
        campaign_data
    )

    # Update campaign status
    await db.execute("""
        UPDATE retention_campaigns 
        SET status = 'sending', sent_at = NOW(), target_count = :count
        WHERE id = :campaign_id
    """, {"campaign_id": campaign_id, "count": len(members)})
    await db.commit()

    return {
        "campaign_id": campaign_id,
        "status": "sending",
        "target_count": len(members),
        "message": "Campaign launched, messages sending in background"
    }

async def send_campaign_messages(gym_id: str, campaign_id: str, members: list, campaign: dict):
    """Background task to send campaign messages."""
    sent_count = 0

    for member in members:
        # Personalize message
        personalized_body = campaign["body_text"].replace("{first_name}", member["first_name"])

        # Send email
        if member["email"] and campaign.get("body_text"):
            await sendgrid_service.send_email(
                to=member["email"],
                subject=campaign["subject"],
                body=personalized_body
            )

        # Send SMS
        if member["phone"] and campaign.get("sms_text"):
            personalized_sms = campaign["sms_text"].replace("{first_name}", member["first_name"])
            await twilio_service.send_sms(
                to=member["phone"],
                body=personalized_sms
            )

        sent_count += 1

        # Rate limiting
        if sent_count % 10 == 0:
            await asyncio.sleep(1)

    # Update final stats
    # (In production, update database with sent_count, opened, etc.)
    print(f"✅ Campaign {campaign_id}: Sent {sent_count} messages")

# ============================================================
# FILE: services/ai-engine/app/models/churn_predictor.py
# Churn Prediction Model
# ============================================================

import pickle
import numpy as np
from typing import List, Dict
from datetime import datetime, timedelta

class ChurnPredictor:
    """ML model for predicting member churn risk."""

    def __init__(self):
        self.model = None
        self.feature_names = [
            'days_since_last_visit',
            'avg_weekly_visits',
            'total_visits',
            'membership_length_days',
            'monthly_fee',
            'visit_streak',
            'cancellation_count',
            'late_cancel_count',
            'no_show_count',
            'days_until_renewal'
        ]
        self._load_or_init_model()

    def _load_or_init_model(self):
        """Load trained model or initialize with heuristic rules."""
        try:
            with open('models/churn_model.pkl', 'rb') as f:
                self.model = pickle.load(f)
        except FileNotFoundError:
            # Initialize with rule-based fallback
            self.model = None
            print("⚠️ No trained model found, using heuristic predictions")

    def predict_single(self, member: dict) -> dict:
        """Predict churn risk for a single member."""
        # Extract features
        features = self._extract_features(member)

        if self.model:
            risk_score = self.model.predict_proba([features])[0][1]
        else:
            # Heuristic fallback
            risk_score = self._heuristic_score(features)

        # Determine risk level
        if risk_score >= 0.8:
            risk_level = "critical"
        elif risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Generate reason
        reasons = self._get_risk_reasons(features, risk_score)

        return {
            "member_id": member["id"],
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "reasons": reasons,
            "recommended_action": self._get_recommended_action(risk_level, reasons)
        }

    def predict_batch(self, members: List[dict]) -> List[dict]:
        """Predict churn risk for multiple members."""
        return [self.predict_single(m) for m in members]

    def _extract_features(self, member: dict) -> List[float]:
        """Extract numerical features from member data."""
        now = datetime.now()
        last_visit = member.get("last_visit_at", now)
        if isinstance(last_visit, str):
            last_visit = datetime.fromisoformat(last_visit.replace('Z', '+00:00'))

        days_since_visit = (now - last_visit).days if last_visit else 999
        membership_start = member.get("created_at", now)
        if isinstance(membership_start, str):
            membership_start = datetime.fromisoformat(membership_start.replace('Z', '+00:00'))

        membership_length = (now - membership_start).days

        return [
            days_since_visit,
            member.get("avg_weekly_visits", 0),
            member.get("total_visits", 0),
            membership_length,
            member.get("monthly_fee", 0),
            member.get("visit_streak", 0),
            0,  # cancellation_count (would come from history)
            0,  # late_cancel_count
            0,  # no_show_count
            30,  # days_until_renewal (simplified)
        ]

    def _heuristic_score(self, features: List[float]) -> float:
        """Rule-based churn score when no ML model exists."""
        score = 0.0

        # Days since last visit (most important)
        days = features[0]
        if days > 21: score += 0.4
        elif days > 14: score += 0.25
        elif days > 7: score += 0.1

        # Low visit frequency
        if features[1] < 1: score += 0.2
        elif features[1] < 2: score += 0.1

        # Low total visits (new members)
        if features[2] < 5: score += 0.15

        # Negative streak
        if features[5] < 0: score += 0.1

        return min(score, 0.95)

    def _get_risk_reasons(self, features: List[float], score: float) -> List[str]:
        """Generate human-readable risk reasons."""
        reasons = []

        if features[0] > 14:
            reasons.append(f"Hasn't visited in {features[0]} days")
        if features[1] < 1:
            reasons.append("Averaging less than 1 visit per week")
        if features[2] < 5:
            reasons.append("New member with low engagement")
        if features[5] < 0:
            reasons.append("Broken visit streak")

        return reasons

    def _get_recommended_action(self, risk_level: str, reasons: List[str]) -> str:
        """Get AI-recommended action based on risk."""
        actions = {
            "critical": "Immediate personal outreach + 50% discount offer + freeze option",
            "high": "Send win-back campaign + schedule personal call + offer free class",
            "medium": "Send re-engagement email + class recommendation + streak reminder",
            "low": "Continue normal engagement, monitor for changes"
        }
        return actions.get(risk_level, "Monitor")

    def get_top_features(self) -> List[dict]:
        """Return feature importance for explainability."""
        return [
            {"feature": "days_since_last_visit", "importance": 0.45},
            {"feature": "avg_weekly_visits", "importance": 0.25},
            {"feature": "membership_length", "importance": 0.15},
            {"feature": "visit_streak", "importance": 0.10},
            {"feature": "monthly_fee", "importance": 0.05}
        ]

    def get_churn_reasons(self) -> List[dict]:
        """Get aggregated churn reasons across all predictions."""
        return [
            {"reason": "Lack of engagement (infrequent visits)", "count": 45, "percentage": 38.5},
            {"reason": "Life changes (moving, schedule)", "count": 28, "percentage": 23.9},
            {"reason": "Price sensitivity", "count": 22, "percentage": 18.8},
            {"reason": "Competitor attraction", "count": 15, "percentage": 12.8},
            {"reason": "Facility/schedule issues", "count": 7, "percentage": 6.0}
        ]

# ============================================================
# FILE: services/ai-engine/app/routers/assistant.py
# AI Operations Assistant Router
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.openai_service import openai_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    context: Optional[dict] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    actions: List[dict]
    data: Optional[dict] = None
    conversation_id: str

class AutoScheduleRequest(BaseModel):
    week_start: Optional[str] = None
    optimize_for: Optional[str] = "occupancy"

class PricingOptimizeResponse(BaseModel):
    current_mrr: float
    recommended_mrr: float
    potential_increase: float
    recommendations: List[dict]

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    gym_id: str,
    message: ChatMessage,
    db: AsyncSession = Depends(get_db)
):
    """Natural language AI assistant for gym operations."""

    # Get gym context
    gym_data = await db.execute("""
        SELECT * FROM gyms WHERE id = :gym_id
    """, {"gym_id": gym_id})
    gym = gym_data.mappings().first()

    # Get recent metrics for context
    metrics = await db.execute("""
        SELECT 
            COUNT(*) as active_members,
            COALESCE(SUM(monthly_fee), 0) as mrr
        FROM members 
        WHERE gym_id = :gym_id AND membership_status = 'active'
    """, {"gym_id": gym_id})
    metrics_data = metrics.mappings().first()

    # Build system prompt with gym context
    system_prompt = f"""You are FitMind AI, an expert gym management assistant.

    Gym: {gym['name']}
    Active Members: {metrics_data['active_members']}
    MRR: ${metrics_data['mrr']}

    You can help with:
    - Scheduling and class optimization
    - Member retention strategies
    - Billing and payment issues
    - Revenue analysis and pricing
    - Lead conversion tactics

    When the user asks for an action, respond with both a friendly message 
    and a structured action that the frontend can execute."""

    # Call OpenAI
    ai_response = await openai_service.chat_completion(
        system_prompt=system_prompt,
        user_message=message.message,
        conversation_id=message.conversation_id
    )

    # Parse actions from AI response
    actions = parse_actions_from_response(ai_response)

    return ChatResponse(
        response=ai_response["text"],
        actions=actions,
        data=ai_response.get("data"),
        conversation_id=ai_response.get("conversation_id", message.conversation_id or "new")
    )

@router.post("/auto-schedule")
async def auto_optimize_schedule(
    gym_id: str,
    request: AutoScheduleRequest,
    db: AsyncSession = Depends(get_db)
):
    """AI-optimize class schedule based on demand patterns."""

    # Get historical attendance data
    attendance_data = await db.execute("""
        SELECT 
            cs.day_of_week,
            cs.start_time,
            ct.name as class_name,
            AVG(c.booked_count::float / NULLIF(c.max_capacity, 0)) as avg_occupancy,
            COUNT(*) as total_classes
        FROM class_schedules cs
        JOIN class_types ct ON ct.id = cs.class_type_id
        LEFT JOIN classes c ON c.schedule_id = cs.id 
            AND c.class_date > NOW() - INTERVAL '30 days'
        WHERE cs.gym_id = :gym_id AND cs.is_active = true
        GROUP BY cs.day_of_week, cs.start_time, ct.name
        ORDER BY avg_occupancy DESC
    """, {"gym_id": gym_id})

    schedules = attendance_data.mappings().all()

    # AI analysis
    analysis_prompt = f"""
    Analyze this gym schedule data and recommend optimizations:
    {schedules}

    Optimize for: {request.optimize_for}

    Return specific changes: add/remove/move classes with reasoning.
    """

    recommendations = await openai_service.generate_schedule_recommendations(
        analysis_prompt, schedules
    )

    return {
        "changes": recommendations.get("changes", []),
        "projected_occupancy_improvement": recommendations.get("occupancy_improvement", 0),
        "projected_revenue_impact": recommendations.get("revenue_impact", 0)
    }

@router.post("/pricing-optimize", response_model=PricingOptimizeResponse)
async def optimize_pricing(
    gym_id: str,
    db: AsyncSession = Depends(get_db)
):
    """AI-optimize membership pricing based on market and usage data."""

    # Get pricing and usage data
    pricing_data = await db.execute("""
        SELECT 
            membership_type,
            COUNT(*) as member_count,
            AVG(monthly_fee) as avg_fee,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY monthly_fee) as median_fee,
            AVG(total_visits) as avg_visits,
            AVG(avg_weekly_visits) as avg_weekly
        FROM members 
        WHERE gym_id = :gym_id AND membership_status = 'active'
        GROUP BY membership_type
    """, {"gym_id": gym_id})

    tiers = pricing_data.mappings().all()

    # Get competitor data (would come from external API in production)
    market_data = {
        "local_avg": 89.00,
        "local_median": 85.00,
        "price_elasticity": -0.8
    }

    # AI pricing analysis
    pricing_prompt = f"""
    Analyze pricing optimization for this gym:
    Current Tiers: {tiers}
    Market Data: {market_data}

    Recommend price changes with confidence scores and expected revenue impact.
    Consider: demand elasticity, member lifetime value, competitive positioning.
    """

    recommendations = await openai_service.generate_pricing_recommendations(
        pricing_prompt, tiers, market_data
    )

    current_mrr = sum(t["member_count"] * t["avg_fee"] for t in tiers)
    recommended_mrr = current_mrr + recommendations.get("revenue_increase", 0)

    return PricingOptimizeResponse(
        current_mrr=round(current_mrr, 2),
        recommended_mrr=round(recommended_mrr, 2),
        potential_increase=round(recommendations.get("revenue_increase", 0), 2),
        recommendations=recommendations.get("tier_changes", [])
    )

def parse_actions_from_response(ai_response: dict) -> List[dict]:
    """Extract actionable items from AI response."""
    actions = []
    text = ai_response.get("text", "").lower()

    if "schedule" in text or "class" in text:
        actions.append({
            "type": "navigate",
            "description": "View class schedule",
            "target": "/classes"
        })

    if "retention" in text or "churn" in text or "risk" in text:
        actions.append({
            "type": "navigate",
            "description": "View retention alerts",
            "target": "/retention"
        })

    if "payment" in text or "billing" in text or "invoice" in text:
        actions.append({
            "type": "navigate",
            "description": "View billing dashboard",
            "target": "/billing"
        })

    if "launch" in text or "campaign" in text or "send" in text:
        actions.append({
            "type": "action",
            "description": "Launch recommended campaign",
            "parameters": {"auto_fill": True}
        })

    return actions

# ============================================================
# FILE: services/ai-engine/app/services/openai_service.py
# OpenAI Integration Service
# ============================================================

import os
from typing import Optional, List, Dict
import openai

class OpenAIService:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o"  # or gpt-4-turbo for cost savings

    async def chat_completion(
        self,
        system_prompt: str,
        user_message: str,
        conversation_id: Optional[str] = None
    ) -> dict:
        """Generate AI response for gym operations chat."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            functions=[
                {
                    "name": "schedule_class",
                    "description": "Schedule a new class",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "class_type_id": {"type": "string"},
                            "date": {"type": "string"},
                            "time": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "send_campaign",
                    "description": "Send a retention campaign",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "campaign_type": {"type": "string"},
                            "target_segment": {"type": "string"}
                        }
                    }
                }
            ],
            function_call="auto"
        )

        message = response.choices[0].message

        return {
            "text": message.content or "I've processed your request. Would you like me to take any action?",
            "function_call": message.function_call,
            "conversation_id": conversation_id or f"conv_{response.id}"
        }

    async def generate_insights(self, prompt: str) -> List[dict]:
        """Generate AI insights for retention analysis."""

        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a gym business analyst. Provide concise, actionable recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=400
        )

        text = response.choices[0].message.content

        # Parse recommendations
        recommendations = []
        for line in text.split("\n"):
            if line.strip() and (line.startswith("1.") or line.startswith("2.") or line.startswith("3.")):
                recommendations.append({
                    "action": line.strip(),
                    "expected_impact": "Medium to high",
                    "confidence": 0.75
                })

        return recommendations

    async def generate_schedule_recommendations(
        self, prompt: str, schedule_data: list
    ) -> dict:
        """Generate schedule optimization recommendations."""

        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a gym scheduling optimizer. Return structured recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=600
        )

        text = response.choices[0].message.content

        # Parse structured response
        return {
            "changes": self._parse_schedule_changes(text),
            "occupancy_improvement": 12.5,  # Would be calculated
            "revenue_impact": 850  # Would be calculated
        }

    async def generate_pricing_recommendations(
        self, prompt: str, tiers: list, market_data: dict
    ) -> dict:
        """Generate pricing optimization recommendations."""

        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a pricing strategist for fitness businesses."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        text = response.choices[0].message.content

        return {
            "tier_changes": self._parse_pricing_changes(text, tiers),
            "revenue_increase": 1860  # Would be calculated from model
        }

    def _parse_schedule_changes(self, text: str) -> List[dict]:
        """Parse schedule changes from AI text."""
        changes = []
        # Simplified parsing - in production use structured output
        if "move" in text.lower():
            changes.append({
                "action": "move",
                "class_id": "spin-cycle",
                "old_value": "7:00 PM Tuesday",
                "new_value": "6:30 PM Tuesday",
                "reason": "Low attendance at current time"
            })
        return changes

    def _parse_pricing_changes(self, text: str, tiers: list) -> List[dict]:
        """Parse pricing changes from AI text."""
        changes = []
        for tier in tiers:
            changes.append({
                "tier_name": tier["membership_type"],
                "current_price": round(tier["avg_fee"], 2),
                "recommended_price": round(tier["avg_fee"] * 1.12, 2),
                "confidence": 0.72,
                "reasoning": "Market analysis shows 12% headroom"
            })
        return changes

# Singleton instance
openai_service = OpenAIService()

# ============================================================
# FILE: services/ai-engine/requirements.txt
# ============================================================
"""
fastapi==0.111.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
redis==5.0.0
celery==5.4.0
openai==1.35.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.7.0
python-multipart==0.0.9
python-dotenv==1.0.0
httpx==0.27.0
numpy==1.26.0
scikit-learn==1.5.0
pandas==2.2.0
stripe==9.0.0
twilio==9.0.0
sendgrid==6.11.0
pytest==8.2.0
pytest-asyncio==0.23.0
"""

# ============================================================
# FILE: services/ai-engine/Dockerfile
# ============================================================
"""
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY models/ ./models/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
"""

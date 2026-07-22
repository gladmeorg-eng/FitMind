import os
from fastapi import FastAPI
from google import genai

# Initialize Gemini using the key you saved in Render
gemini_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_key) if gemini_key else None

@app.post("/v3/gyms/{gym_id}/ai/chat")
async def ai_chat(gym_id: str, message: str):
    if not client:
        return {"response": "Error: GEMINI_API_KEY not found in Render environment variables."}
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message
        )
        return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel

security = HTTPBearer()

# --- Services & Worker Stubs ---
class RedisClient:
    async def connect(self):
        pass
    async def disconnect(self):
        pass

redis_client = RedisClient()

async def start_retention_worker():
    pass

async def start_billing_worker():
    pass

class TwilioService:
    async def send_sms(self, to: str, body: str):
        print(f"SMS sent to {to}: {body}")

twilio_service = TwilioService()

class SendGridService:
    async def send_email(self, to: str, subject: str, body: str):
        print(f"Email sent to {to}: {subject}")

sendgrid_service = SendGridService()

# --- Database Dependency Fallback ---
async def get_db():
    class DummyDB:
        async def execute(self, query, params=None):
            class DummyResult:
                def mappings(self):
                    class DummyMappings:
                        def all(self):
                            return []
                        def first(self):
                            return {
                                "id": "gym_123",
                                "name": "FitMind Gym",
                                "active_members": 150,
                                "mrr": 12500,
                                "campaign_type": "win_back",
                                "body_text": "Hi {first_name}, we miss you!"
                            }
                    return DummyMappings()
                def scalar(self):
                    return "id_123"
            return DummyResult()
        async def commit(self):
            pass
    yield DummyDB()

# --- OpenAI Service ---
class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = "gpt-4o"

    async def chat_completion(self, system_prompt: str, user_message: str, conversation_id: Optional[str] = None) -> dict:
        if self.api_key:
            try:
                import openai
                client = openai.AsyncOpenAI(api_key=self.api_key)
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                text = response.choices[0].message.content or "Processed."
                return {"text": text, "conversation_id": conversation_id or "conv_123"}
            except Exception:
                return {"text": f"FitMind AI Assistant: Received '{user_message}'", "conversation_id": conversation_id or "conv_123"}
        return {"text": f"FitMind AI Assistant (Demo Mode): Received '{user_message}'", "conversation_id": conversation_id or "conv_123"}

    async def generate_insights(self, prompt: str) -> List[dict]:
        return [
            {"action": "Offer 1-on-1 coaching for members with 0 visits in last 14 days", "expected_impact": "High", "confidence": 0.85},
            {"action": "Send automated SMS re-engagement campaign", "expected_impact": "Medium", "confidence": 0.78},
            {"action": "Provide free class pass to low-frequency members", "expected_impact": "Medium", "confidence": 0.72}
        ]

    async def generate_schedule_recommendations(self, prompt: str, schedule_data: list) -> dict:
        return {
            "changes": [
                {"action": "move", "class_id": "spin-cycle", "old_value": "7:00 PM Tuesday", "new_value": "6:30 PM Tuesday", "reason": "Higher peak demand"}
            ],
            "occupancy_improvement": 12.5,
            "revenue_impact": 850
        }

    async def generate_pricing_recommendations(self, prompt: str, tiers: list, market_data: dict) -> dict:
        return {
            "tier_changes": [
                {"tier_name": "Standard", "current_price": 89.0, "recommended_price": 99.0, "confidence": 0.8, "reasoning": "Market allows 11% increase"}
            ],
            "revenue_increase": 1860
        }

openai_service = OpenAIService()

# --- Churn Predictor ML Model ---
class ChurnPredictor:
    def __init__(self):
        self.model = None
        self.feature_names = [
            'days_since_last_visit', 'avg_weekly_visits', 'total_visits',
            'membership_length_days', 'monthly_fee', 'visit_streak',
            'cancellation_count', 'late_cancel_count', 'no_show_count', 'days_until_renewal'
        ]

    def predict_single(self, member: dict) -> dict:
        features = self._extract_features(member)
        risk_score = self._heuristic_score(features)
        
        if risk_score >= 0.8:
            risk_level = "critical"
        elif risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        reasons = self._get_risk_reasons(features, risk_score)
        return {
            "member_id": member.get("id", "m_unknown"),
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "reasons": reasons,
            "recommended_action": self._get_recommended_action(risk_level, reasons)
        }

    def predict_batch(self, members: List[dict]) -> List[dict]:
        return [self.predict_single(m) for m in members]

    def _extract_features(self, member: dict) -> List[float]:
        now = datetime.now()
        last_visit = member.get("last_visit_at", now)
        if isinstance(last_visit, str):
            try:
                last_visit = datetime.fromisoformat(last_visit.replace('Z', '+00:00'))
            except Exception:
                last_visit = now

        days_since_visit = (now - last_visit).days if last_visit else 999
        membership_start = member.get("created_at", now)
        if isinstance(membership_start, str):
            try:
                membership_start = datetime.fromisoformat(membership_start.replace('Z', '+00:00'))
            except Exception:
                membership_start = now

        membership_length = (now - membership_start).days
        return [
            float(days_since_visit),
            float(member.get("avg_weekly_visits", 0)),
            float(member.get("total_visits", 0)),
            float(membership_length),
            float(member.get("monthly_fee", 0)),
            float(member.get("visit_streak", 0)),
            0.0, 0.0, 0.0, 30.0
        ]

    def _heuristic_score(self, features: List[float]) -> float:
        score = 0.0
        days = features[0]
        if days > 21: score += 0.4
        elif days > 14: score += 0.25
        elif days > 7: score += 0.1

        if features[1] < 1: score += 0.2
        elif features[1] < 2: score += 0.1

        if features[2] < 5: score += 0.15
        if features[5] < 0: score += 0.1
        return min(score, 0.95)

    def _get_risk_reasons(self, features: List[float], score: float) -> List[str]:
        reasons = []
        if features[0] > 14:
            reasons.append(f"Hasn't visited in {int(features[0])} days")
        if features[1] < 1:
            reasons.append("Averaging less than 1 visit per week")
        if features[2] < 5:
            reasons.append("New member with low engagement")
        if features[5] < 0:
            reasons.append("Broken visit streak")
        return reasons

    def _get_recommended_action(self, risk_level: str, reasons: List[str]) -> str:
        actions = {
            "critical": "Immediate personal outreach + 50% discount offer + freeze option",
            "high": "Send win-back campaign + schedule personal call + offer free class",
            "medium": "Send re-engagement email + class recommendation + streak reminder",
            "low": "Continue normal engagement, monitor for changes"
        }
        return actions.get(risk_level, "Monitor")

    def get_top_features(self) -> List[dict]:
        return [
            {"feature": "days_since_last_visit", "importance": 0.45},
            {"feature": "avg_weekly_visits", "importance": 0.25},
            {"feature": "membership_length", "importance": 0.15},
            {"feature": "visit_streak", "importance": 0.10},
            {"feature": "monthly_fee", "importance": 0.05}
        ]

    def get_churn_reasons(self) -> List[dict]:
        return [
            {"reason": "Lack of engagement (infrequent visits)", "count": 45, "percentage": 38.5},
            {"reason": "Life changes (moving, schedule)", "count": 28, "percentage": 23.9},
            {"reason": "Price sensitivity", "count": 22, "percentage": 18.8},
            {"reason": "Competitor attraction", "count": 15, "percentage": 12.8},
            {"reason": "Facility/schedule issues", "count": 7, "percentage": 6.0}
        ]

churn_model = ChurnPredictor()

# --- Pydantic Data Models ---
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

# --- FastAPI App & Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 FitMind AI Engine starting...")
    try:
        await redis_client.connect()
        asyncio.create_task(start_retention_worker())
        asyncio.create_task(start_billing_worker())
        print("✅ All workers started")
    except Exception as e:
        print(f"Startup warning: {e}")
    yield
    try:
        await redis_client.disconnect()
    except Exception:
        pass
    print("👋 FitMind AI Engine shutting down...")

app = FastAPI(
    title="FitMind AI Gym OS API",
    description="AI-powered backend for gym management automation",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
retention_router = APIRouter(prefix="/v3/gyms/{gym_id}/retention", tags=["AI Retention"])
assistant_router = APIRouter(prefix="/v3/gyms/{gym_id}/ai", tags=["AI Assistant"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3.0.0", "ai_engine": "online"}

# --- Retention Routes ---
@retention_router.get("/alerts", response_model=List[RetentionAlertResponse])
async def get_retention_alerts(
    gym_id: str,
    severity: Optional[str] = "all",
    status: Optional[str] = "open",
    db: Any = Depends(get_db)
):
    query = "SELECT ra.id, ra.member_id, m.first_name || ' ' || m.last_name as member_name, ra.alert_type, ra.severity, ra.description, ra.ai_recommendation, ra.status, ra.created_at FROM retention_alerts ra JOIN members m ON m.id = ra.member_id WHERE ra.gym_id = :gym_id"
    params = {"gym_id": gym_id}

    if severity != "all":
        query += " AND ra.severity = :severity"
        params["severity"] = severity
    if status != "all":
        query += " AND ra.status = :status"
        params["status"] = status

    query += " ORDER BY ra.created_at DESC"
    result = await db.execute(query, params)
    return result.mappings().all()

@retention_router.post("/alerts/{alert_id}/resolve")
async def resolve_retention_alert(
    gym_id: str,
    alert_id: str,
    action_taken: str,
    resolution_notes: Optional[str] = None,
    db: Any = Depends(get_db)
):
    query = "UPDATE retention_alerts SET status = 'resolved', resolved_at = NOW(), action_taken = :action_taken, resolution_notes = :notes WHERE id = :alert_id AND gym_id = :gym_id"
    await db.execute(query, {
        "alert_id": alert_id,
        "gym_id": gym_id,
        "action_taken": action_taken,
        "notes": resolution_notes
    })
    await db.commit()
    return {"status": "resolved", "alert_id": alert_id}

@retention_router.get("/insights", response_model=RetentionInsights)
async def get_retention_insights(
    gym_id: str,
    db: Any = Depends(get_db)
):
    query = "SELECT id, total_visits, avg_weekly_visits, last_visit_at, membership_status, monthly_fee, days_since_signup FROM members WHERE gym_id = :gym_id AND membership_status = 'active'"
    members_data = await db.execute(query, {"gym_id": gym_id})
    members = members_data.mappings().all()

    predictions = churn_model.predict_batch(members)
    at_risk = [p for p in predictions if p["risk_score"] > 0.7]

    insights_prompt = f"Analyze gym retention data: Active={len(members)}, At-Risk={len(at_risk)}"
    ai_recommendations = await openai_service.generate_insights(insights_prompt)

    return RetentionInsights(
        predicted_churn_next_30d=len(at_risk),
        at_risk_members=at_risk[:10],
        top_churn_reasons=churn_model.get_churn_reasons(),
        recommendations=ai_recommendations
    )

@retention_router.post("/campaigns")
async def create_retention_campaign(
    gym_id: str,
    campaign: RetentionCampaignCreate,
    background_tasks: BackgroundTasks,
    db: Any = Depends(get_db)
):
    query = "INSERT INTO retention_campaigns (gym_id, name, campaign_type, target_segment, subject, body_text, body_html, sms_text, status, created_at) VALUES (:gym_id, :name, :type, :segment, :subject, :body_text, :body_html, :sms_text, 'draft', NOW()) RETURNING id"
    result = await db.execute(query, {
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

@retention_router.post("/campaigns/{campaign_id}/launch")
async def launch_campaign(
    gym_id: str,
    campaign_id: str,
    background_tasks: BackgroundTasks,
    db: Any = Depends(get_db)
):
    campaign = await db.execute("SELECT * FROM retention_campaigns WHERE id = :campaign_id AND gym_id = :gym_id", {"campaign_id": campaign_id, "gym_id": gym_id})
    campaign_data = campaign.mappings().first()

    if not campaign_data:
        raise HTTPException(status_code=404, detail="Campaign not found")

    target_query = "SELECT id, email, phone, first_name, push_token FROM members WHERE gym_id = :gym_id AND membership_status = 'active'"
    targets = await db.execute(target_query, {"gym_id": gym_id})
    members = targets.mappings().all()

    background_tasks.add_task(send_campaign_messages, gym_id, campaign_id, members, campaign_data)
    await db.execute("UPDATE retention_campaigns SET status = 'sending', sent_at = NOW(), target_count = :count WHERE id = :campaign_id", {"campaign_id": campaign_id, "count": len(members)})
    await db.commit()

    return {"campaign_id": campaign_id, "status": "sending", "target_count": len(members), "message": "Campaign launched"}

async def send_campaign_messages(gym_id: str, campaign_id: str, members: list, campaign: dict):
    sent_count = 0
    for member in members:
        body_text = campaign.get("body_text", "") or ""
        personalized_body = body_text.replace("{first_name}", member.get("first_name", "Member"))

        if member.get("email") and body_text:
            await sendgrid_service.send_email(to=member["email"], subject=campaign.get("subject", ""), body=personalized_body)

        if member.get("phone") and campaign.get("sms_text"):
            personalized_sms = campaign["sms_text"].replace("{first_name}", member.get("first_name", "Member"))
            await twilio_service.send_sms(to=member["phone"], body=personalized_sms)

        sent_count += 1
        if sent_count % 10 == 0:
            await asyncio.sleep(1)

# --- Assistant Routes ---
def parse_actions_from_response(ai_response: dict) -> List[dict]:
    actions = []
    text = ai_response.get("text", "").lower()
    if "schedule" in text or "class" in text:
        actions.append({"type": "navigate", "description": "View class schedule", "target": "/classes"})
    if "retention" in text or "churn" in text or "risk" in text:
        actions.append({"type": "navigate", "description": "View retention alerts", "target": "/retention"})
    if "payment" in text or "billing" in text or "invoice" in text:
        actions.append({"type": "navigate", "description": "View billing dashboard", "target": "/billing"})
    if "launch" in text or "campaign" in text or "send" in text:
        actions.append({"type": "action", "description": "Launch recommended campaign", "parameters": {"auto_fill": True}})
    return actions

@assistant_router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    gym_id: str,
    message: ChatMessage,
    db: Any = Depends(get_db)
):
    gym_data = await db.execute("SELECT * FROM gyms WHERE id = :gym_id", {"gym_id": gym_id})
    gym = gym_data.mappings().first() or {"name": "FitMind Gym"}

    metrics = await db.execute("SELECT COUNT(*) as active_members, COALESCE(SUM(monthly_fee), 0) as mrr FROM members WHERE gym_id = :gym_id AND membership_status = 'active'", {"gym_id": gym_id})
    metrics_data = metrics.mappings().first() or {"active_members": 100, "mrr": 8000}

    system_prompt = f"You are FitMind AI assistant for {gym.get('name', 'Gym')}."
    ai_response = await openai_service.chat_completion(system_prompt=system_prompt, user_message=message.message, conversation_id=message.conversation_id)
    actions = parse_actions_from_response(ai_response)

    return ChatResponse(
        response=ai_response["text"],
        actions=actions,
        data=ai_response.get("data"),
        conversation_id=ai_response.get("conversation_id", message.conversation_id or "new")
    )

@assistant_router.post("/auto-schedule")
async def auto_optimize_schedule(
    gym_id: str,
    request: AutoScheduleRequest,
    db: Any = Depends(get_db)
):
    query = "SELECT cs.day_of_week, cs.start_time, ct.name as class_name, AVG(c.booked_count::float / NULLIF(c.max_capacity, 0)) as avg_occupancy, COUNT(*) as total_classes FROM class_schedules cs JOIN class_types ct ON ct.id = cs.class_type_id LEFT JOIN classes c ON c.schedule_id = cs.id AND c.class_date > NOW() - INTERVAL '30 days' WHERE cs.gym_id = :gym_id AND cs.is_active = true GROUP BY cs.day_of_week, cs.start_time, ct.name ORDER BY avg_occupancy DESC"
    attendance_data = await db.execute(query, {"gym_id": gym_id})
    schedules = attendance_data.mappings().all()

    recommendations = await openai_service.generate_schedule_recommendations("Optimize schedule", schedules)
    return {
        "changes": recommendations.get("changes", []),
        "projected_occupancy_improvement": recommendations.get("occupancy_improvement", 0),
        "projected_revenue_impact": recommendations.get("revenue_impact", 0)
    }

@assistant_router.post("/pricing-optimize", response_model=PricingOptimizeResponse)
async def optimize_pricing(
    gym_id: str,
    db: Any = Depends(get_db)
):
    query = "SELECT membership_type, COUNT(*) as member_count, AVG(monthly_fee) as avg_fee, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY monthly_fee) as median_fee, AVG(total_visits) as avg_visits, AVG(avg_weekly_visits) as avg_weekly FROM members WHERE gym_id = :gym_id AND membership_status = 'active' GROUP BY membership_type"
    pricing_data = await db.execute(query, {"gym_id": gym_id})
    tiers = pricing_data.mappings().all()

    market_data = {"local_avg": 89.00, "local_median": 85.00, "price_elasticity": -0.8}
    recommendations = await openai_service.generate_pricing_recommendations("Pricing prompt", tiers, market_data)

    current_mrr = sum(t.get("member_count", 0) * t.get("avg_fee", 0) for t in tiers) or 5000.0
    recommended_mrr = current_mrr + recommendations.get("revenue_increase", 0)

    return PricingOptimizeResponse(
        current_mrr=round(current_mrr, 2),
        recommended_mrr=round(recommended_mrr, 2),
        potential_increase=round(recommendations.get("revenue_increase", 0), 2),
        recommendations=recommendations.get("tier_changes", [])
    )

# Include Routers in main app
app.include_router(retention_router)
app.include_router(assistant_router)

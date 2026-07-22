
-- ============================================================
-- FITMIND AI GYM OS - COMPLETE DATABASE SCHEMA
-- PostgreSQL 15+ | Production-Ready
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- CORE: GYMS & ORGANIZATIONS
-- ============================================================
CREATE TABLE gyms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan_type VARCHAR(20) DEFAULT 'starter' CHECK (plan_type IN ('starter', 'growth', 'enterprise')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled')),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'US',
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    branding JSONB DEFAULT '{"primary_color": "#6366f1", "logo_url": null, "app_name": null}',
    stripe_account_id VARCHAR(255),
    twilio_phone VARCHAR(20),
    sendgrid_api_key_encrypted TEXT,
    openai_api_key_encrypted TEXT,
    settings JSONB DEFAULT '{
        "auto_retry_payments": true,
        "retry_interval_hours": 48,
        "max_retry_attempts": 3,
        "auto_waitlist": true,
        "cancellation_policy_hours": 12,
        "late_cancel_fee": 0,
        "check_in_window_minutes": 15,
        "retention_alert_days": 10,
        "win_back_discount_percent": 50,
        "referral_reward_amount": 25
    }',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- ============================================================
-- CORE: USERS (Owners, Staff, Coaches)
-- ============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    role VARCHAR(20) DEFAULT 'staff' CHECK (role IN ('owner', 'admin', 'manager', 'coach', 'staff')),
    permissions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(gym_id, email)
);

-- ============================================================
-- CORE: MEMBERS
-- ============================================================
CREATE TABLE members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,

    -- Personal Info
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(20),
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),

    -- Membership
    membership_type VARCHAR(50) DEFAULT 'standard',
    membership_status VARCHAR(20) DEFAULT 'active' CHECK (membership_status IN ('active', 'frozen', 'expired', 'cancelled', 'pending')),
    membership_start_date DATE,
    membership_end_date DATE,
    billing_cycle VARCHAR(20) DEFAULT 'monthly' CHECK (billing_cycle IN ('weekly', 'monthly', 'quarterly', 'yearly')),
    monthly_fee DECIMAL(10,2) DEFAULT 0,

    -- AI Retention Scoring
    retention_score INTEGER DEFAULT 100 CHECK (retention_score BETWEEN 0 AND 100),
    churn_risk VARCHAR(20) DEFAULT 'low' CHECK (churn_risk IN ('low', 'medium', 'high', 'critical')),
    churn_risk_reason TEXT,
    last_visit_at TIMESTAMPTZ,
    visit_streak INTEGER DEFAULT 0,
    total_visits INTEGER DEFAULT 0,
    total_classes INTEGER DEFAULT 0,
    avg_weekly_visits DECIMAL(3,1) DEFAULT 0,

    -- Engagement
    last_engagement_at TIMESTAMPTZ,
    preferred_class_types JSONB DEFAULT '[]',
    preferred_times JSONB DEFAULT '[]',
    fitness_goals JSONB DEFAULT '[]',

    -- Referral
    referral_code VARCHAR(20) UNIQUE,
    referred_by UUID REFERENCES members(id),
    referral_count INTEGER DEFAULT 0,
    referral_earnings DECIMAL(10,2) DEFAULT 0,

    -- App
    app_installed BOOLEAN DEFAULT false,
    push_token VARCHAR(500),
    device_type VARCHAR(20),

    -- Stripe
    stripe_customer_id VARCHAR(255),
    payment_method_id VARCHAR(255),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    UNIQUE(gym_id, email)
);

CREATE INDEX idx_members_gym ON members(gym_id);
CREATE INDEX idx_members_churn_risk ON members(gym_id, churn_risk);
CREATE INDEX idx_members_retention ON members(gym_id, retention_score);
CREATE INDEX idx_members_last_visit ON members(gym_id, last_visit_at);

-- ============================================================
-- CLASSES & SCHEDULING
-- ============================================================
CREATE TABLE class_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    duration_minutes INTEGER NOT NULL DEFAULT 45,
    max_capacity INTEGER NOT NULL DEFAULT 20,
    min_capacity INTEGER DEFAULT 5,
    color VARCHAR(7) DEFAULT '#6366f1',
    icon VARCHAR(50),
    difficulty VARCHAR(20) DEFAULT 'all' CHECK (difficulty IN ('beginner', 'intermediate', 'advanced', 'all')),
    calories_burned_estimate INTEGER,
    equipment_needed JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE class_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    class_type_id UUID NOT NULL REFERENCES class_types(id),
    coach_id UUID REFERENCES users(id),

    -- Schedule
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room VARCHAR(100),
    max_capacity INTEGER,
    waitlist_capacity INTEGER DEFAULT 10,

    -- AI Optimization
    predicted_demand INTEGER DEFAULT 0,
    avg_attendance_last_30d DECIMAL(5,2) DEFAULT 0,
    is_recommended BOOLEAN DEFAULT false,
    optimization_notes TEXT,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    schedule_id UUID REFERENCES class_schedules(id),
    class_type_id UUID NOT NULL REFERENCES class_types(id),
    coach_id UUID REFERENCES users(id),

    -- Instance Details
    class_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room VARCHAR(100),
    max_capacity INTEGER NOT NULL,
    booked_count INTEGER DEFAULT 0,
    waitlist_count INTEGER DEFAULT 0,
    attended_count INTEGER DEFAULT 0,
    no_show_count INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'cancelled', 'completed', 'in_progress')),
    cancellation_reason TEXT,

    -- AI
    ai_optimized BOOLEAN DEFAULT false,
    ai_notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_classes_gym_date ON classes(gym_id, class_date);
CREATE INDEX idx_classes_status ON classes(status);

-- ============================================================
-- BOOKINGS & WAITLIST
-- ============================================================
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,

    status VARCHAR(20) DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'cancelled', 'no_show', 'attended', 'waitlisted', 'promoted')),
    booked_at TIMESTAMPTZ DEFAULT NOW(),
    cancelled_at TIMESTAMPTZ,
    cancellation_reason VARCHAR(50),
    checked_in_at TIMESTAMPTZ,

    -- Waitlist
    waitlist_position INTEGER,
    promoted_at TIMESTAMPTZ,

    -- AI
    booking_source VARCHAR(20) DEFAULT 'app' CHECK (booking_source IN ('app', 'web', 'staff', 'auto')),
    ai_recommended BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(member_id, class_id)
);

CREATE INDEX idx_bookings_member ON bookings(member_id);
CREATE INDEX idx_bookings_class ON bookings(class_id);
CREATE INDEX idx_bookings_status ON bookings(status);

-- ============================================================
-- BILLING & PAYMENTS
-- ============================================================
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,

    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(10,2) NOT NULL,

    description TEXT,
    period_start DATE,
    period_end DATE,

    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'failed', 'refunded', 'disputed')),
    paid_at TIMESTAMPTZ,

    stripe_invoice_id VARCHAR(255),
    stripe_payment_intent_id VARCHAR(255),

    -- Retry Logic
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMPTZ,
    last_retry_at TIMESTAMPTZ,
    failure_reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id),

    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded')),

    payment_method VARCHAR(20) DEFAULT 'card' CHECK (payment_method IN ('card', 'ach', 'wallet', 'cash')),
    stripe_payment_intent_id VARCHAR(255),
    stripe_charge_id VARCHAR(255),

    failure_code VARCHAR(50),
    failure_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_invoices_member ON invoices(member_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_payments_member ON payments(member_id);

-- ============================================================
-- AI RETENTION ENGINE
-- ============================================================
CREATE TABLE retention_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,

    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN (
        'missed_visits', 'membership_expiring', 'payment_failed', 
        'low_attendance', 'cancellation_risk', 'birthday', 'milestone'
    )),
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),

    description TEXT,
    ai_recommendation TEXT,
    suggested_action VARCHAR(50),

    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'ignored')),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id),
    resolution_notes TEXT,

    -- Effectiveness Tracking
    action_taken VARCHAR(50),
    member_responded BOOLEAN DEFAULT false,
    member_returned BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE retention_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(50) NOT NULL CHECK (campaign_type IN (
        'win_back', 're_engagement', 'birthday', 'milestone', 
        'referral', 'upgrade', 'survey', 'custom'
    )),

    -- Targeting
    target_segment VARCHAR(50),
    target_count INTEGER DEFAULT 0,

    -- Content
    subject VARCHAR(255),
    body_text TEXT,
    body_html TEXT,
    sms_text TEXT,
    push_title VARCHAR(100),
    push_body TEXT,

    -- Schedule
    scheduled_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,

    -- Results
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    sms_sent INTEGER DEFAULT 0,
    sms_delivered INTEGER DEFAULT 0,
    push_sent INTEGER DEFAULT 0,
    push_opened INTEGER DEFAULT 0,

    conversions INTEGER DEFAULT 0,
    revenue_generated DECIMAL(10,2) DEFAULT 0,

    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'sending', 'sent', 'paused')),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_retention_alerts_gym ON retention_alerts(gym_id, status);
CREATE INDEX idx_retention_alerts_member ON retention_alerts(member_id);

-- ============================================================
-- MESSAGING & COMMUNICATIONS
-- ============================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,

    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'sms', 'push', 'in_app')),
    message_type VARCHAR(50) NOT NULL,

    subject VARCHAR(255),
    body TEXT NOT NULL,

    status VARCHAR(20) DEFAULT 'queued' CHECK (status IN ('queued', 'sent', 'delivered', 'opened', 'clicked', 'failed', 'bounced')),

    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,

    external_id VARCHAR(255), -- Twilio msg_sid, SendGrid message_id, etc.
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_member ON messages(member_id);
CREATE INDEX idx_messages_status ON messages(status);

-- ============================================================
-- LEADS & SALES PIPELINE
-- ============================================================
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,

    -- Contact
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),

    -- Source
    source VARCHAR(50) NOT NULL CHECK (source IN (
        'website', 'walk_in', 'referral', 'social_media', 
        'google_ads', 'facebook_ads', 'instagram', 'tiktok', 'partner'
    )),
    source_detail TEXT,
    landing_page VARCHAR(255),
    utm_campaign VARCHAR(100),

    -- Referral
    referred_by_member_id UUID REFERENCES members(id),

    -- AI Scoring
    lead_score INTEGER DEFAULT 50 CHECK (lead_score BETWEEN 0 AND 100),
    ai_insights TEXT,

    -- Pipeline
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN (
        'new', 'contacted', 'tour_scheduled', 'tour_completed', 
        'trial_offered', 'trial_active', 'converted', 'lost', 'nurture'
    )),

    -- Timeline
    first_contact_at TIMESTAMPTZ DEFAULT NOW(),
    last_contact_at TIMESTAMPTZ,
    tour_scheduled_at TIMESTAMPTZ,
    tour_completed_at TIMESTAMPTZ,
    trial_started_at TIMESTAMPTZ,
    trial_ends_at TIMESTAMPTZ,
    converted_at TIMESTAMPTZ,
    converted_to_member_id UUID REFERENCES members(id),
    lost_at TIMESTAMPTZ,
    lost_reason VARCHAR(100),

    -- Assignment
    assigned_to UUID REFERENCES users(id),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_leads_gym ON leads(gym_id);
CREATE INDEX idx_leads_status ON leads(gym_id, status);
CREATE INDEX idx_leads_score ON leads(gym_id, lead_score);

-- ============================================================
-- ACTIVITY LOG (For AI Training & Analytics)
-- ============================================================
CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id),
    user_id UUID REFERENCES users(id),

    activity_type VARCHAR(50) NOT NULL CHECK (activity_type IN (
        'check_in', 'class_booked', 'class_cancelled', 'class_attended', 
        'class_no_show', 'payment_made', 'payment_failed', 'membership_started',
        'membership_renewed', 'membership_cancelled', 'membership_frozen',
        'profile_updated', 'app_opened', 'message_opened', 'message_clicked',
        'referral_sent', 'referral_converted', 'review_submitted'
    )),

    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activity_logs_member ON activity_logs(member_id);
CREATE INDEX idx_activity_logs_gym ON activity_logs(gym_id, created_at);

-- ============================================================
-- AI MODEL VERSIONS & PREDICTIONS
-- ============================================================
CREATE TABLE ai_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID REFERENCES gyms(id),

    model_type VARCHAR(50) NOT NULL CHECK (model_type IN (
        'churn_prediction', 'demand_forecasting', 'lead_scoring', 
        'pricing_optimization', 'class_recommendation'
    )),
    version VARCHAR(20) NOT NULL,

    -- Metrics
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),

    model_path VARCHAR(500),
    feature_importance JSONB,
    training_data_size INTEGER,

    is_active BOOLEAN DEFAULT false,
    deployed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ai_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id),
    model_id UUID REFERENCES ai_models(id),

    prediction_type VARCHAR(50) NOT NULL,
    prediction_value DECIMAL(10,6),
    confidence DECIMAL(5,4),
    features_used JSONB,

    was_correct BOOLEAN,
    actual_outcome VARCHAR(50),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- DIGITAL WAIVERS
-- ============================================================
CREATE TABLE waivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,

    template_id VARCHAR(50) NOT NULL,
    template_version INTEGER DEFAULT 1,

    signed_content TEXT NOT NULL,
    signature_data TEXT, -- base64 encoded signature image

    signed_at TIMESTAMPTZ NOT NULL,
    ip_address INET,
    user_agent TEXT,

    document_url VARCHAR(500),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TRIGGER FUNCTIONS
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all tables with updated_at
CREATE TRIGGER update_gyms_updated_at BEFORE UPDATE ON gyms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_members_updated_at BEFORE UPDATE ON members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_class_schedules_updated_at BEFORE UPDATE ON class_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_classes_updated_at BEFORE UPDATE ON classes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bookings_updated_at BEFORE UPDATE ON bookings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_invoices_updated_at BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_retention_alerts_updated_at BEFORE UPDATE ON retention_alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- VIEWS FOR ANALYTICS
-- ============================================================
CREATE VIEW v_gym_dashboard AS
SELECT 
    g.id as gym_id,
    g.name as gym_name,
    COUNT(DISTINCT m.id) as total_members,
    COUNT(DISTINCT CASE WHEN m.membership_status = 'active' THEN m.id END) as active_members,
    COUNT(DISTINCT CASE WHEN m.churn_risk IN ('high', 'critical') THEN m.id END) as at_risk_members,
    COUNT(DISTINCT CASE WHEN m.last_visit_at > NOW() - INTERVAL '7 days' THEN m.id END) as active_this_week,
    COALESCE(SUM(i.total_amount), 0) as mrr_revenue,
    COUNT(DISTINCT c.id) as classes_this_month,
    AVG(c.booked_count::FLOAT / NULLIF(c.max_capacity, 0) * 100) as avg_occupancy
FROM gyms g
LEFT JOIN members m ON m.gym_id = g.id AND m.deleted_at IS NULL
LEFT JOIN invoices i ON i.gym_id = g.id AND i.status = 'paid' AND i.created_at > NOW() - INTERVAL '30 days'
LEFT JOIN classes c ON c.gym_id = g.id AND c.class_date > NOW() - INTERVAL '30 days'
WHERE g.deleted_at IS NULL
GROUP BY g.id, g.name;

CREATE VIEW v_member_360 AS
SELECT 
    m.*,
    COUNT(DISTINCT b.id) as total_bookings,
    COUNT(DISTINCT CASE WHEN b.status = 'attended' THEN b.id END) as attended_classes,
    COUNT(DISTINCT CASE WHEN b.status = 'no_show' THEN b.id END) as no_shows,
    COUNT(DISTINCT CASE WHEN b.status = 'cancelled' THEN b.id END) as cancellations,
    MAX(b.checked_in_at) as last_check_in,
    COALESCE(SUM(p.amount), 0) as lifetime_value
FROM members m
LEFT JOIN bookings b ON b.member_id = m.id
LEFT JOIN payments p ON p.member_id = m.id AND p.status = 'succeeded'
WHERE m.deleted_at IS NULL
GROUP BY m.id;

-- ============================================================
-- SEED DATA FOR DEMO
-- ============================================================
INSERT INTO gyms (name, slug, plan_type, city, state, settings) VALUES
('FitLife Downtown', 'fitlife-downtown', 'growth', 'New York', 'NY', 
 '{"auto_retry_payments": true, "retention_alert_days": 10, "win_back_discount_percent": 50}');

INSERT INTO users (gym_id, email, password_hash, first_name, last_name, role) VALUES
((SELECT id FROM gyms WHERE slug = 'fitlife-downtown'), 'sarah@fitlife.com', 'hashed_pw', 'Sarah', 'Johnson', 'owner');

INSERT INTO class_types (gym_id, name, description, duration_minutes, max_capacity, color, icon) VALUES
((SELECT id FROM gyms WHERE slug = 'fitlife-downtown'), 'HIIT Blast', 'High intensity interval training', 45, 20, '#ef4444', 'fire'),
((SELECT id FROM gyms WHERE slug = 'fitlife-downtown'), 'Yoga Flow', 'Vinyasa yoga for all levels', 60, 15, '#8b5cf6', 'yoga'),
((SELECT id FROM gyms WHERE slug = 'fitlife-downtown'), 'Spin Cycle', 'Indoor cycling class', 45, 25, '#06b6d4', 'bike'),
((SELECT id FROM gyms WHERE slug = 'fitlife-downtown'), 'Powerlifting', 'Strength training focus', 60, 22, '#6366f1', 'dumbbell');

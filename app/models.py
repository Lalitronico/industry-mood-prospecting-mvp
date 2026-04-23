from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class LeadStatus(str, enum.Enum):
    NEW = "new"
    ENRICHED = "enriched"
    SCORED = "scored"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    INTERESTED = "interested"
    DEMO_SCHEDULED = "demo_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"


class EmailStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"


class LeadSource(str, enum.Enum):
    APOLLO = "apollo"
    LINKEDIN = "linkedin"
    MANUAL = "manual"
    REFERRAL = "referral"
    IMPORT = "import"


class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    website = Column(String(255))
    industry = Column(String(100))
    sub_industry = Column(String(100))
    size_range = Column(String(50))  # "50-100", "100-300", etc.
    employee_count = Column(Integer)
    location = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100), default="Mexico")
    linkedin_url = Column(String(255))
    technologies = Column(Text)  # JSON string
    description = Column(Text)
    
    # Signals
    hiring_for = Column(Text)
    recent_news = Column(Text)
    funding_stage = Column(String(50))
    
    # Scoring
    fit_score = Column(Integer, default=0)  # 0-100
    pain_signals = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    
    # Contact info
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255), index=True)
    email_verified = Column(Boolean, default=False)
    phone = Column(String(50))
    linkedin_url = Column(String(255))
    job_title = Column(String(255))
    seniority = Column(String(50))  # C-level, VP, Director, Manager
    department = Column(String(100))  # HR, Operations, etc.
    
    # Status
    status = Column(String(50), default=LeadStatus.NEW)
    source = Column(String(50), default=LeadSource.APOLLO)
    
    # Scoring
    score = Column(Integer, default=0)  # 0-100
    score_reasons = Column(Text)  # JSON string
    priority = Column(String(20), default="warm")  # hot, warm, cool
    
    # Campaign tracking
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    sequence_step = Column(Integer, default=0)
    last_contact_at = Column(DateTime(timezone=True))
    next_contact_at = Column(DateTime(timezone=True))
    
    # Engagement
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    replies_received = Column(Integer, default=0)
    
    # Notes
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Targeting
    target_industry = Column(String(100))
    target_location = Column(String(255))
    target_size = Column(String(50))
    
    # Status
    status = Column(String(50), default="draft")  # draft, active, paused, completed
    
    # Sequence config
    sequence_template = Column(Text)  # JSON string with sequence steps
    
    # Stats
    leads_total = Column(Integer, default=0)
    leads_contacted = Column(Integer, default=0)
    leads_responded = Column(Integer, default=0)
    demos_booked = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text)
    body_text = Column(Text, nullable=False)
    
    # Template metadata
    step_number = Column(Integer)  # 1, 2, 3... in sequence
    purpose = Column(String(100))  # initial, followup, breakup
    
    # AI generation prompt
    ai_prompt = Column(Text)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    
    # Content
    subject = Column(String(500))
    body_text = Column(Text)
    body_html = Column(Text)
    
    # Personalization data used
    personalization_data = Column(Text)  # JSON string
    
    # Review workflow
    status = Column(String(50), default=EmailStatus.PENDING_REVIEW)
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    
    # Sending
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    message_id = Column(String(255))  # From ESP
    
    # Tracking
    opened_at = Column(DateTime(timezone=True))
    open_count = Column(Integer, default=0)
    clicked_at = Column(DateTime(timezone=True))
    click_count = Column(Integer, default=0)
    replied_at = Column(DateTime(timezone=True))
    reply_content = Column(Text)
    
    # Bounce handling
    bounced_at = Column(DateTime(timezone=True))
    bounce_reason = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    activity_type = Column(String(50))  # email_sent, email_opened, reply_received, etc.
    description = Column(Text)
    metadata_json = Column("metadata", Text)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())

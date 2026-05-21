from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, SecretStr, NameEmail
from datetime import date
from enum import Enum
import uuid
import json
from sqlalchemy import create_engine, Column, Integer, String, Text, Date
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
import os

#Database Configuration
# Hardcoded connection string
DB_PASSWORD = os.getenv("DB_PASSWORD")
SQLALCHEMY_DATABASE_URL = f"postgresql://admin:{DB_PASSWORD}@db:5432/idea_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#Database Models
class DBLead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String, unique=True, index=True)
    status = Column(String, default="Submitted")
    assigned_verifier = Column(String, nullable=True)
    verifier_comments = Column(Text, nullable=True)
    title = Column(String)
    organization = Column(String)
    background = Column(Text)
    challenge = Column(Text)
    scope = Column(Text)
    requirements = Column(Text)
    risks = Column(Text, nullable=True)
    time_plan = Column(Date)
    active_wbs = Column(String, nullable=True)
    spoc_email = Column(String)
    business_owner_email = Column(String)
    stakeholders = Column(String, default="[]")

# Automatically generate tables if they don't exist
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Application Setup
app = FastAPI(
    title="IDEA API",
    description="API for registering and initial management of initiative leads.",
    version="0.3.0",
)

# Enable Cross-Origin Resource Sharing (CORS) for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")

#***Temporary*** hardcoded credentials for the prototype
VERIFIER_PASSWORD=os.getenv("VERIFIER_PASSWORD")

VERIFIERS = {
    "admin": VERIFIER_PASSWORD
}


def get_current_verifier(token: str = Depends(oauth2_scheme)):
    if token not in VERIFIERS:
        raise HTTPException(
            status_code=404,
            detail="Unauthorized. Please log in as a verifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# Mail server configuration (SMTP)
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

mail_config = ConnectionConfig(
    MAIL_USERNAME="volvoenjoyerideavolvo@gmail.com",
    MAIL_PASSWORD=SecretStr(EMAIL_APP_PASSWORD),
    MAIL_FROM="volvoenjoyerideavolvo@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="IDEA Platform",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fast_mail = FastMail(mail_config)

# Helper function to send emails in the background
async def send_email_notification(subject: str, recipients: list[str], body: str):
    name_email_recipients = [NameEmail(name="", email=r) for r in recipients]

    message = MessageSchema(
        subject=subject,
        recipients=name_email_recipients,
        body=body,
        subtype=MessageType.plain
    )
    await fast_mail.send_message(message)

#Pydantic Schemas (Data Validation)
class Status(str, Enum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    ASSIGNED = "Assigned"
    APPROVED = "Approved - Discovery Phase"
    ONGOING = "Ongoing - Implementation Phase"
    REJECTED = "Rejected / Needs Clarification"


class LeadCreate(BaseModel):
    title: str = Field(..., description="Initiative title")
    organization: str = Field(..., description="Organization name")
    background: str = Field(..., description="Initiative background")
    challenge: str = Field(..., description="Business challenge")
    scope: str = Field(..., description="High-level scope")
    requirements: str = Field(..., description="Basic requirements")
    risks: str | None = Field(default=None, description="Assumptions, constraints, risks")
    time_plan: date = Field(..., description="High-level time-plan / target dates")
    active_wbs: str | None = Field(default=None, description="Active WBS for Discovery Phase")
    spoc_email: EmailStr = Field(..., description="SPOC")
    business_owner_email: EmailStr = Field(..., description="Business Owner")
    stakeholders: list[str] = Field(default=[], description="Involved Stakeholders")


class LeadData(LeadCreate):
    id: int | None = None
    tracking_id: str | None = None
    status: Status = Status.SUBMITTED
    assigned_verifier: str | None = None
    verifier_comments: str | None = None


class LeadUpdate(BaseModel):
    status: Status
    verifier_comments: str | None = Field(default=None)

#Endpoints

@app.get("/", summary="Redirect to Docs", tags=["Redirects"])
def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.post("/auth", summary="Login for Verifiers", tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username in VERIFIERS and VERIFIERS[form_data.username] == form_data.password:
        return {"access_token": form_data.username, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")


@app.post("/leads", summary="Submit Lead Form", tags=["Leads"])
async def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    new_tracking_id = str(uuid.uuid4()).split('-')[0]
    db_lead = DBLead(
        tracking_id=new_tracking_id,
        title=lead.title,
        organization=lead.organization,
        background=lead.background,
        challenge=lead.challenge,
        scope=lead.scope,
        requirements=lead.requirements,
        risks=lead.risks,
        time_plan=lead.time_plan,
        active_wbs=lead.active_wbs,
        spoc_email=lead.spoc_email,
        business_owner_email=lead.business_owner_email,
        stakeholders=json.dumps(lead.stakeholders)
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)

    tracking_url = f"http://localhost:5500/track.html"

    email_body = (
        f"Thank you for submitting your lead!\n\n"
        f"You can check its status clicking the link below and entering your tracking ID: {db_lead.tracking_id}\n"
        f"{tracking_url}\n\n"
        "Best regards,\n"
        "Volvo"
    )

    await send_email_notification(
        subject="IDEA Platform - Lead Submission",
        recipients=[str(lead.spoc_email), str(lead.business_owner_email)],
        body=email_body,
    )

    return {
        "message": "Lead submitted successfully",
        "tracking_id": db_lead.tracking_id,
        "check_status_url": f"/track/{db_lead.tracking_id}"
    }


@app.get("/track/{tracking_id}", summary="Check Your Lead Status", tags=["Leads"])
def track_lead(tracking_id: str, db: Session = Depends(get_db)):
    lead = db.query(DBLead).filter(DBLead.tracking_id == tracking_id).first()
    if lead:
        return {
            "title": lead.title,
            "status": lead.status,
            "assigned_verifier": lead.assigned_verifier,
            "verifier_comments": lead.verifier_comments
        }
    raise HTTPException(status_code=404, detail="Invalid tracking code")


@app.get("/leads/{lead_id}", response_model=LeadData, summary="Get Lead Details", tags=["Leads"])
def get_lead(lead_id: int, current_verifier: str = Depends(get_current_verifier), db: Session = Depends(get_db)):
    lead = db.query(DBLead).filter(DBLead.id == lead_id).first()
    if lead:
        lead_dict = lead.__dict__
        lead_dict['stakeholders'] = json.loads(str(lead.stakeholders))
        return lead_dict
    raise HTTPException(status_code=404, detail="Lead not found")


@app.get("/leads", response_model=list[LeadData], summary="List Leads", tags=["Leads"])
def list_leads(limit: int = 10, current_verifier: str = Depends(get_current_verifier), db: Session = Depends(get_db)):
    leads = db.query(DBLead).limit(limit).all()
    result = []
    for lead in leads:
        lead_dict = lead.__dict__
        lead_dict['stakeholders'] = json.loads(str(lead.stakeholders))
        result.append(lead_dict)
    return result


@app.patch("/leads/{lead_id}/status", summary="Update Lead Status", tags=["Leads"])
async def update_lead_status(lead_id: int, update_data: LeadUpdate, current_verifier: str = Depends(get_current_verifier),
                       db: Session = Depends(get_db)):
    lead = db.query(DBLead).filter(DBLead.id == lead_id).first()
    if lead:
        lead.status = update_data.status
        if update_data.verifier_comments is not None:
            lead.verifier_comments = update_data.verifier_comments
        lead.assigned_verifier = current_verifier

        db.commit()
        db.refresh(lead)

        tracking_url = f"http://localhost:5500/track.html"

        email_body = (
            f"The status of your lead '{lead.title}' has been updated to: {lead.status}.\n\n"
            f"To see more information, click the link below and enter your tracking ID: {lead.tracking_id}\n"
            f"{tracking_url}\n\n"
            "Best regards,\n"
            "Volvo"
        )

        await send_email_notification(
            subject=f"IDEA Platform - Lead Status Update: {lead.title}",
            recipients=[str(lead.spoc_email), str(lead.business_owner_email)],
            body=email_body
        )

        lead_dict = lead.__dict__
        lead_dict['stakeholders'] = json.loads(str(lead.stakeholders))
        return {"message": "Lead updated successfully", "lead": lead_dict}

    raise HTTPException(status_code=404, detail="Lead not found")

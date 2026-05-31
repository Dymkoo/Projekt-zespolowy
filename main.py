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
import time
from sqlalchemy.exc import OperationalError
import bcrypt

VERIFIER_EMAIL = os.getenv("VERIFIER_EMAIL")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
VERIFIER_USERNAME = os.getenv("VERIFIER_USERNAME")
VERIFIER_PASSWORD = os.getenv("VERIFIER_PASSWORD")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

SQLALCHEMY_DATABASE_URL = f"postgresql://admin:{DB_PASSWORD}@db:5432/idea_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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
    contact_email = Column(String)
    owner_email = Column(String)
    stakeholders = Column(String, default="[]")

class DBUser(Base):
    __tablename__ = "verifiers"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)
    lead_id = Column(Integer, nullable=True)

def wait_for_db(engine, max_retries=10, delay=3):
    retries = 0
    while retries < max_retries:
        try:
            with engine.connect() as conn:
                return True
        except OperationalError:
            retries += 1
            time.sleep(delay)
    raise Exception("Database connection failed")

wait_for_db(engine)

Base.metadata.create_all(bind=engine)

def initialize_admin_user():
    db = SessionLocal()
    try:
        existing_admin = db.query(DBUser).filter(DBUser.username == VERIFIER_USERNAME).first()
        if not existing_admin:
            admin_user = DBUser(username=VERIFIER_USERNAME, password=hash_password(VERIFIER_PASSWORD), role="verifier")
            db.add(admin_user)
            db.commit()
    finally:
        db.close()

initialize_admin_user()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="IDEA API",
    description="API for registering and initial management of initiative leads."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == token).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Invalid user.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"username": user.username, "role": user.role, "lead_id": user.lead_id}

mail_config = ConnectionConfig(
    MAIL_USERNAME="volvoenjoyerideavolvo@gmail.com",
    MAIL_PASSWORD=SecretStr(EMAIL_APP_PASSWORD),
    MAIL_FROM="volvoenjoyerideavolvo@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="IDEA Team",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fast_mail = FastMail(mail_config)

async def send_email_notification(subject: str, recipients: list[str], body: str):
    name_email_recipients = [NameEmail(name="", email=r) for r in recipients]

    message = MessageSchema(
        subject=subject,
        recipients=name_email_recipients,
        body=body,
        subtype=MessageType.plain
    )
    await fast_mail.send_message(message)

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
    contact_email: EmailStr = Field(..., description="Contact Email")
    owner_email: EmailStr = Field(..., description="Owner Email")
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
    project_leader_email: EmailStr | None = Field(default=None)

class LeaderResponse(BaseModel):
    id: int
    username: str
    lead_id: int | None
    lead_title: str | None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

@app.get("/", summary="Redirect to Docs", tags=["Redirects"])
def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.post("/auth", summary="Login for Verifiers", tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == form_data.username).first()

    if user and verify_password(form_data.password, str(user.password)):
        return {"access_token": user.username, "token_type": "bearer"}

    raise HTTPException(status_code=400, detail="Incorrect username or password")

@app.post("/leads", summary="Submit Lead Form", tags=["Leads"])
async def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    new_tracking_id = "IDEA_"+str(uuid.uuid4())[:4]
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
        contact_email=lead.contact_email,
        owner_email=lead.owner_email,
        stakeholders=json.dumps(lead.stakeholders)
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)

    email_body = (
        "Hello,\n\n"
        "Your request in the IDEA tool has been successfully submitted.\n\n"
        f"Request ID: {db_lead.tracking_id}\n\n"
        "It is now being forwarded to the Initiative Coordinator for verification. DPO will contact you directly if any additional information is required.\n\n"
        "Best regards,\n"
        "IDEA Team"
    )

    await send_email_notification(
        subject=f"{db_lead.tracking_id} - IDEA Tool Request Confirmation",
        recipients=[str(lead.contact_email), str(lead.owner_email)],
        body=email_body
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
def get_lead(lead_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] == "leader":
        if current_user.get("lead_id")  != lead_id:
            raise HTTPException(status_code=403, detail="No permissions. You can only view your lead")

    lead = db.query(DBLead).filter(DBLead.id == lead_id).first()
    if lead:
        lead_dict = lead.__dict__
        lead_dict['stakeholders'] = json.loads(str(lead.stakeholders))
        return lead_dict
    raise HTTPException(status_code=404, detail="Lead not found")

@app.get("/leads", response_model=list[LeadData], summary="List Leads", tags=["Leads"])
def list_leads(limit: int = 10, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] == "leader":
        leads = db.query(DBLead).filter(DBLead.id == current_user["lead_id"]).limit(limit).all()
    else:
        leads = db.query(DBLead).limit(limit).all()

    result = []
    for lead in leads:
        lead_dict = lead.__dict__
        lead_dict['stakeholders'] = json.loads(str(lead.stakeholders))
        result.append(lead_dict)
    return result

@app.patch("/leads/{lead_id}/status", summary="Update Lead Status", tags=["Leads"])
async def update_lead_status(lead_id: int, update_data: LeadUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "verifier":
        raise HTTPException(status_code=403, detail="Access only for verifiers")

    lead = db.query(DBLead).filter(DBLead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.status = update_data.status
    if update_data.verifier_comments is not None:
        lead.verifier_comments = update_data.verifier_comments
    lead.assigned_verifier = current_user["username"]

    if update_data.project_leader_email:
        existing_leader = db.query(DBUser).filter(DBUser.username == update_data.project_leader_email).first()
        if not existing_leader:
            temp_password = str(uuid.uuid4())[:8]
            new_leader = DBUser(username=update_data.project_leader_email, password=hash_password(temp_password), role="leader", lead_id=lead_id)
            db.add(new_leader)

            leader_email_body = (
                "Hello,\n\n"
                f"You have been assigned as the project leader for lead: {lead.tracking_id}.\n\n"
                f"Username: {update_data.project_leader_email}\n"
                f"Temporary password: {temp_password}\n\n"
                "Best regards,\n"
                "IDEA Team"
            )

            await send_email_notification(
                subject=f"{lead.tracking_id} - Project Leader Assignment",
                recipients=[update_data.project_leader_email],
                body=leader_email_body
            )

    email_body = (
        "Hello,\n\n"
        "Your request in the IDEA tool has been successfully updated.\n\n"
        "Best regards,\n"
        "IDEA Team"
    )

    await send_email_notification(
        subject=f"{lead.tracking_id} - IDEA Tool Request Update - STATUS",
        recipients=[str(lead.contact_email), str(lead.owner_email)],
        body=email_body
    )

    db.commit()
    db.refresh(lead)

    lead_dict = lead.__dict__
    lead_dict["stakeholders"] = json.loads(str(lead.stakeholders))
    return {"message": "Lead updated successfully", "lead": lead_dict}

@app.get("/leaders", response_model=list[LeaderResponse], summary="List of Leaders", tags=["Leaders Management"])
def list_leaders(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "verifier":
        raise HTTPException(status_code=403, detail="Access only for verifiers")

    leaders = db.query(DBUser).filter(DBUser.role == "leader").all()

    result = []
    for leader in leaders:
        lead_title = None
        if leader.lead_id:
            lead = db.query(DBLead).filter(DBLead.id == leader.lead_id).first()
            if lead:
                lead_title = lead.title

        result.append({"id": leader.id, "username": leader.username, "lead_id": leader.lead_id, "lead_title": lead_title})
        return result

@app.delete("/leaders/{leader_id}", summary="Delete Leader", tags=["Leaders Management"])
def delete_leader(username: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "verifier":
        raise HTTPException(status_code=403, detail="Access only for verifiers")

    leader = db.query(DBUser).filter(DBUser.username == username, DBUser.role == "leader").first()

    if not leader:
        raise HTTPException(status_code=404, detail="Leader not found")

    db.delete(leader)
    db.commit()

    return {"message": f"Leader {username} deleted successfully"}

@app.post("/auth/change-password", summary="Change Your Password", tags=["Authentication"])
def change_password(data: PasswordChange, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == current_user["username"]).first()

    if not user or not verify_password(data.old_password, str(user.password)):
        raise HTTPException(status_code=400, detail="Invalid Password")

    user.password = hash_password(data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}

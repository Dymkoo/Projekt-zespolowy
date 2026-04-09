from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from enum import Enum
import uuid

app = FastAPI(
    title="IDEA API",
    description="API for registering and initial management of initiative leads.",
    version="0.3.0",
)

# --- CONFIG & AUTH ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")

VERIFIERS = {
    "admin": "cisco123"
}

def get_current_verifier(token: str = Depends(oauth2_scheme)):
    if token not in VERIFIERS:
        raise HTTPException(
            status_code=404,
            detail="Unauthorized. Please log in as a verifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# --- DATA MODELS ---
class Status(str, Enum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    ASSIGNED = "Assigned"
    APPROVED = "Approved - Discovery Phase"
    ONGOING = "Ongoing - Implementation Phase"
    REJECTED = "Rejected / Needs Clarification"

class LeadCreate(BaseModel):
    #Core Identification
    title: str = Field(..., description="Initiative title")
    organization: str = Field(..., description="Organization name")

    #Business Context
    background: str = Field(..., description="Initiative background")
    challenge: str = Field(..., description="Business challenge")

    #Scope & Requirements
    scope: str = Field(..., description="High-level scope")
    requirements: str = Field(..., description="Basic requirements (functional / non-functional)")
    risks: str | None = Field(default=None, description="Assumptions, constraints, risks")

    #Planning Inputs
    time_plan: date = Field(..., description="High-level time-plan / target dates")
    active_wbs: str | None = Field(default=None, description="Active WBS for Discovery Phase")

    #Governance & Contacts
    spoc_email: EmailStr = Field(..., description="SPOC")
    business_owner_email: EmailStr = Field(..., description="Business Owner")
    stakeholders: list[str] = Field(default=[], description="Involved Stakeholders / Key Users / SMEs")

class LeadData(LeadCreate):
    id: int | None = None
    tracking_id: str | None = None
    status: Status = Status.SUBMITTED
    assigned_verifier: str | None = None
    verifier_comments: str | None = None

class LeadUpdate(BaseModel):
    status: Status
    verifier_comments: str | None = Field(default=None, description="")

leads_data = []
current_id = 1

# --- PUBLIC ENDPOINTS ---
@app.get("/", summary="Redirect to Docs", tags=["Redirects"])
def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.post("/auth", summary="Login for Verifiers", tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username in VERIFIERS and VERIFIERS[form_data.username] == form_data.password:
        return {"access_token": form_data.username, "token_type": "bearer"}

    raise HTTPException(status_code=400, detail="Incorrect username or password")

@app.post("/leads", summary="Submit Lead Form", tags=["Leads"])
async def create_lead(lead: LeadCreate):
    global current_id

    new_lead = LeadData(
        **lead.model_dump(),
        id=current_id,
        tracking_id=str(uuid.uuid4())
    )

    leads_data.append(new_lead)
    current_id += 1

    return {
        "message": "Lead submitted successfully",
        "tracking_id": new_lead.tracking_id,
        "check_status_url": f"/track/{new_lead.tracking_id}"
    }

@app.get("/track/{tracking_id}", summary="Check Your Lead Status", tags=["Leads"])
def track_lead(tracking_id: str):
    for lead in leads_data:
        if lead.tracking_id == tracking_id:
            return {
                "title": lead.title,
                "status": lead.status,
                "assigned_verifier": lead.assigned_verifier,
                "verifier_comments": lead.verifier_comments
            }

    raise HTTPException(status_code=404, detail="Invalid tracking code")

# --- PRIVATE ENDPOINTS ---
@app.get("/leads/{lead_id}", response_model=LeadData, summary="Get Lead Details", tags=["Leads"])
def get_lead(lead_id: int, current_verifier: str = Depends(get_current_verifier)):
    for lead in leads_data:
        if lead.id == lead_id:
            return lead

    raise HTTPException(status_code=404, detail="Lead not found")

@app.get("/leads", response_model=list[LeadData], summary="List Leads", tags=["Leads"])
def list_leads(limit: int = 10, current_verifier: str = Depends(get_current_verifier)):
    return leads_data[:limit]

@app.patch("/leads/{lead_id}/status", summary="Update Lead Status", tags=["Leads"])
def update_lead_status(lead_id: int, update_data: LeadUpdate, current_verifier: str = Depends(get_current_verifier)):
    for lead in leads_data:
        if lead.id == lead_id:
            lead.status = update_data.status

            if update_data.verifier_comments is not None:
                lead.verifier_comments = update_data.verifier_comments

            lead.assigned_verifier = current_verifier

            return {"message": "Lead updated successfully", "lead": lead}

    raise HTTPException(status_code=404, detail="Lead not found")
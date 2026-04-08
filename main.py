from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from enum import Enum

app = FastAPI(
    title="IDEA API",
    description="API for registering and initial management of initiative leads.",
    version="0.2.0",
)

# --- CONFIG & AUTH ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")

VERIFIERS = {
    "admin": "cisco!12345"
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


class LeadData(BaseModel):
    id: int | None = None

    #Core Identification
    title: str = Field(..., description="Initiative title")
    organization: str = Field(..., description="Organization name")

    #Business Context
    background: str = Field(..., description="Initiative background")
    challenge: str = Field(..., description="Business challenge")

    #Scope & Requirements
    scope: str = Field(..., description="High-level scope")
    requirements: str = Field(..., description="Basic requirements (functional / non-functional)")
    risks: str = Field(default=None, description="Assumptions, constraints, risks")

    #Planning Inputs
    time_plan: date = Field(..., description="High-level time-plan / target dates")
    active_wbs: str = Field(default=None, description="Active WBS for Discovery Phase")

    #Governance & Contacts
    spoc_email: EmailStr = Field(..., description="SPOC")
    business_owner_email: EmailStr = Field(..., description="Business Owner")
    stakeholders: list[str] = Field(default=[], description="Involved Stakeholders / Key Users / SMEs")

    status: Status = Status.SUBMITTED

leads_data = []
current_id = 1

# --- PUBLIC ENDPOINTS ---
@app.get("/", summary="Redirect To Docs", tags=["Redirects"])
def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.post("/auth", summary="Login for Verifiers", tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username in VERIFIERS and VERIFIERS[form_data.username] == form_data.password:
        return {"access_token": form_data.username, "token_type": "bearer"}

    raise HTTPException(status_code=400, detail="Incorrect username or password")

@app.post("/leads", summary="Submit Lead Form (No authentication required)", tags=["Leads"])
async def create_lead(lead: LeadData):
    global current_id
    lead.id = current_id
    leads_data.append(lead)
    current_id += 1

    return {"message": "Lead submitted successfully!", "lead_data": lead}

# --- PRIVATE ENDPOINTS ---
@app.get("/leads", response_model=list[LeadData], summary="List Leads (Requires Authentication)", tags=["Leads"])
def list_leads(limit: int = 10, current_verifier: str = Depends(get_current_verifier)):
    return leads_data[:limit]

@app.get("/leads/{lead_id}", response_model=LeadData, summary="Lead Details (Requires Authentication)", tags=["Leads"])
def get_lead(lead_id: int, current_verifier: str = Depends(get_current_verifier)):
    for lead in leads_data:
        if lead.id == lead_id:
            return lead

    raise HTTPException(status_code=404, detail="Lead not found")
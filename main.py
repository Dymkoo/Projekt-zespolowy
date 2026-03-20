from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from enum import Enum

app = FastAPI()

class Status(str, Enum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    ASSIGNED = "Assigned"
    APPROVED = "Approved - Discovery Phase"
    ONGOING = "Ongoing - Implementation Phase"
    REJECTED = "Rejected / Needs Clarification"


class LeadData(BaseModel):
    #Core Identification
    title: str = Field(..., description="Initiative title")
    organization: str = Field(..., description="Organization name")

    #Business Context
    background: str = Field(..., description="Initiative background")
    challenge: str = Field(..., description="Business challenge")

    #Scope & Requirements
    scope: str = Field(..., description="High-level scope")
    requirements: str = Field(..., description="Basic requirements (functional / non-functional)")
    risks: str = Field(..., description="Assumptions, constraints, risks")

    #Planning Inputs
    time_plan: date = Field(..., description="High-level time-plan / target dates")
    active_wbs: str = Field(..., description="Active WBS for Discovery Phase")

    #Governance & Contacts
    spoc_email: EmailStr = Field(..., description="SPOC")
    business_owner_email: EmailStr = Field(..., description="Business Owner")
    stakeholders: list[str] = Field(default=[], description="Involved Stakeholders / Key Users / SMEs")

    status: Status = Status.SUBMITTED

leads_data = []

@app.get("/")
def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.post("/leads")
async def create_lead(lead: LeadData):
    leads_data.append(lead)
    return {
        "message": "Lead submitted successfully!",
        "lead_data": lead
    }

@app.get("/leads", response_model=list[LeadData])
def list_leads(limit: int = 10):
    return leads_data[:limit]

@app.get("/leads/{lead_id}", response_model=LeadData)
def get_lead(lead_id: int) -> LeadData:
    if lead_id < len(leads_data):
        return leads_data[lead_id]
    else:
        raise HTTPException(status_code=404, detail="Lead not found")
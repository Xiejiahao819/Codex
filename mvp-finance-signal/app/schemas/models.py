from pydantic import BaseModel, Field


class EventSummary(BaseModel):
    id: int
    title: str
    sentiment: int = Field(ge=-1, le=1)
    confidence: float = Field(ge=0.0, le=1.0)


class IndustryImpact(BaseModel):
    industry: str
    direction: int = Field(description="1 for positive, -1 for negative")
    strength: float = Field(ge=0.0, le=100.0)


class CompanyImpact(BaseModel):
    ticker: str
    direction: int = Field(description="1 for positive, -1 for negative")
    strength: float = Field(ge=0.0, le=100.0)


class EventDetailResponse(BaseModel):
    event: EventSummary
    industry_impacts: list[IndustryImpact]
    company_impacts: list[CompanyImpact]


class RelatedIndustry(BaseModel):
    industry: str
    relation: str
    weight: float = Field(ge=0.0, le=1.0)


class CompanyDecomposeResponse(BaseModel):
    ticker: str
    direct_industry: str
    related_industries: list[RelatedIndustry]
    recent_events: list[int]

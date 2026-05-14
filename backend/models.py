from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

class EntityMetadata(BaseModel):
    legal_name: str
    ticker: str
    exchange: str
    report_date: str
    version: str
    last_updated: datetime
    schema_version: str

class VersionLogEntry(BaseModel):
    version: str
    date: str
    trigger: str
    agent: str
    sections_updated: List[str]

class SourceMetadata(BaseModel):
    type: str
    filing_type: Optional[str] = None
    filed_date: Optional[str] = None
    entity: Optional[str] = None
    cik: Optional[str] = None
    url: Optional[str] = None

class TemporalValidity(BaseModel):
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    is_historical: bool
    is_current: bool

class InvestmentRelevance(BaseModel):
    relevant: bool
    relevance_tags: List[str] = Field(default_factory=list)
    report_section: Optional[str] = None

class DataPoint(BaseModel):
    id: str
    claim: str
    section: str
    sub_section: Optional[str] = None
    confidence_tier: Literal["primary_confirmed", "secondary_reported", "agent_inferred", "unverified"]
    source: SourceMetadata
    temporal_validity: TemporalValidity
    investment_relevance: InvestmentRelevance
    flags: List[str] = Field(default_factory=list)
    created_at: datetime
    last_verified: datetime

class Section(BaseModel):
    status: str = "pending"
    last_agent_run: Optional[str] = None
    data_points: List[DataPoint] = Field(default_factory=list)

class Sections(BaseModel):
    corporate_identity: Section = Field(default_factory=Section)
    business_segments: Section = Field(default_factory=Section)
    market_growth: Section = Field(default_factory=Section)
    competition_risks: Section = Field(default_factory=Section)
    management: Section = Field(default_factory=Section)
    ma_ledger: Section = Field(default_factory=Section)
    financials_valuation: Section = Field(default_factory=Section)
    synthesis: Section = Field(default_factory=Section)

class Compendium(BaseModel):
    entity: EntityMetadata
    version_log: List[VersionLogEntry] = Field(default_factory=list)
    sections: Sections
    conflict_log: List[Dict[str, Any]] = Field(default_factory=list)
    missing_data_ledger: List[Dict[str, Any]] = Field(default_factory=list)
    refresh_triggers: List[Dict[str, Any]] = Field(default_factory=list)

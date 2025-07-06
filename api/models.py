
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator


#schema for a single RegInsight 
class RegInsight(BaseModel):
    RegInsightDocumentId: UUID
    CUBEJurisdiction: str
    CUBEIssuingBody: str
    CUBEPublishedDate: datetime
    RegOntologyId: str
    RegInsightTextNative: str
    # Optional fields
    CUBEIssuingDepartment: str | None = None
    IssuanceType: str | None = None
    Status: str | None = None
    RegInsightTitleNative: str | None = None
    RegInsightSourceLink: str | None = None

    # Basic sanity check: title length
    _title_len = validator("RegInsightTitleNative", allow_reuse=True)(
        lambda v: v if v is None or len(v) <= 300 else v[:297] + "..."
    )

    class Config:
        anystr_strip_whitespace = True
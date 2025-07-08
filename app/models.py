from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator

class RegInsight(BaseModel):
    doc_id: str = Field(alias="RegInsightDocumentId")
    jurisdiction: str = Field(alias="CUBEJurisdiction")
    published_date: datetime = Field(alias="CUBEPublishedDate")
    ontology_id: str = Field(alias="RegOntologyId")
    concept_names: str | None = None  # New field for human-readable concepts
    text_native: str = Field(alias="RegInsightTextNative")
    title: str = Field(alias="RegInsightTitleNative")
    # Optionals 
    department: str | None = Field(default=None, alias="CUBEIssuingDepartment")
    issuing_body: str | None = Field(default=None, alias="CUBEIssuingBody")
    issuance_type: str | None = Field(default=None, alias="IssuanceType")
    status: str | None = Field(default=None, alias="Status")
    source_url: str | None = Field(default=None, alias="RegInsightSourceLink")
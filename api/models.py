
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator


#schema for a single RegInsight. Created by ChatGPT as it was fairly boilerplate - just copy the data schema provided in task.
class RegInsight(BaseModel):
    doc_id: UUID = Field(alias="RegInsightDocumentId") #the alias is the source field on input - but a little long at times
    jurisdiction: str = Field(alias="CUBEJurisdiction")
    issuing_body: str = Field(alias="CUBEIssuingBody")
    published_date: datetime = Field(alias="CUBEPublishedDate")
    ontology_id: str = Field(alias="RegOntologyId")
    text_native: str = Field(alias="RegInsightTextNative")

    # Optional fields
    department: str | None = Field(default=None, alias="CUBEIssuingDepartment")
    issuance_type: str | None = Field(default=None, alias="IssuanceType")
    status: str | None = Field(default=None, alias="Status")
    title: str | None = Field(default=None, alias="RegInsightTitleNative")
    source_url: str | None = Field(default=None, alias="RegInsightSourceLink")

    class Config:
        # Auto-strip whitespace from all string fields
        anystr_strip_whitespace = True
        # Allow instantiating from source fields (aliases)
        allow_population_by_field_name = False
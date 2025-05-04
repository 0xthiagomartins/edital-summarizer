from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field


class BidMetadata(BaseModel):
    object: str = Field(description="Object description of the bid")
    dates: str = Field(
        description="Opening date and time in format 'Abertura: DD/MM/YYYY HH:MM'"
    )
    public_notice: str = Field(description="Public notice identifier")
    status: str = Field(description="Current status of the bid")
    agency: str = Field(description="Agency responsible for the bid")
    city: str = Field(description="City where the bid is taking place")
    bid_number: str = Field(description="Bid identification number")
    notes: str = Field(description="Additional notes about the bid")
    process_id: str = Field(description="Process identification number")
    phone: Optional[str] = Field(None, description="Contact phone number")
    website: Optional[str] = Field(None, description="Website for more information")

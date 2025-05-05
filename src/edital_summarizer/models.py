from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field


class BidMetadata(BaseModel):
    object: str = Field(description="Object description of the bid")
    dates: str = Field(
        description="Raw date information as scraped from the source. Can contain multiple dates with different labels.\n"
        "Examples:\n"
        "- 'Abertura: 01/04/2025 08:00'\n"
        "- 'Abertura: 01/04/2025 08:00, Prazo de Impugnação: 29/03/2025'\n"
        "- 'Data Limite Proposta: 15/05/2025, Início Disputa: 16/05/2025 10:00'\n"
        "- 'Opening: 04/01/2025 08:00 AM, Deadline: 03/29/2025'\n"
        "- 'Documento disponível até: 30/04/2025, Sessão: 02/05/2025 14:00'\n"
        "Note: Format and labels may vary depending on the source"
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

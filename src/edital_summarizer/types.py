from enum import Enum, auto


class SummaryType(Enum):
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    LEGAL = "legal"

    @classmethod
    def from_str(cls, label: str) -> "SummaryType":
        """Convert string to SummaryType, handling both English and Portuguese inputs."""
        normalized = label.lower().strip()
        mapping = {
            # English
            "executive": cls.EXECUTIVE,
            "technical": cls.TECHNICAL,
            "legal": cls.LEGAL,
            # Portuguese
            "executivo": cls.EXECUTIVE,
            "técnico": cls.TECHNICAL,
            "legal": cls.LEGAL,
        }
        if normalized not in mapping:
            raise ValueError(
                f"Invalid summary type: {label}. Valid types are: executive, technical, legal"
            )
        return mapping[normalized]

    def to_pt(self) -> str:
        """Get Portuguese translation of the summary type."""
        mapping = {
            self.EXECUTIVE: "executivo",
            self.TECHNICAL: "técnico",
            self.LEGAL: "legal",
        }
        return mapping[self]

    def __str__(self) -> str:
        return self.value

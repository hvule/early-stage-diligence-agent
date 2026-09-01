from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ProbabilityRange:
    lower: float
    best: float
    upper: float

    def validate(self) -> None:
        for value in (self.lower, self.best, self.upper):
            if not 0 <= value <= 100:
                raise ValueError("Probabilities must be between 0 and 100.")
        if not self.lower <= self.best <= self.upper:
            raise ValueError("Require lower <= best <= upper.")

    @property
    def ambiguity_width(self) -> float:
        return self.upper - self.lower


@dataclass
class BeliefSnapshot:
    survival_3y: ProbabilityRange
    sustainable_given_survival: ProbabilityRange
    notes: str = ""

    def validate(self) -> None:
        self.survival_3y.validate()
        self.sustainable_given_survival.validate()

    def implied_sustainable_business_best(self) -> float:
        """Best-estimate P(sustainable business) = P(S3) * P(B|S3)."""
        return (self.survival_3y.best / 100.0) * (
            self.sustainable_given_survival.best / 100.0
        ) * 100.0

    def to_dict(self):
        return asdict(self)


@dataclass
class CompanyContext:
    name: str
    url: Optional[str]
    mode: str  # "live" or "historical"
    cutoff_date: Optional[str] = None

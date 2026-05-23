from __future__ import annotations

from decimal import Decimal
from typing import NewType

from pydantic import BaseModel, ConfigDict

FieldKey = NewType("FieldKey", str)


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)

    amount: Decimal
    currency: str  # ISO 4217, e.g. "EUR", "USD"


class BoundingBox(BaseModel):
    model_config = ConfigDict(frozen=True)

    x: float
    y: float
    w: float
    h: float

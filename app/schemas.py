"""
Schemas Pydantic para validação dos webhooks.

Responsabilidades:
- Validar estrutura do payload
- Garantir campos obrigatórios
- Servir como contrato interno da aplicação
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime


class Customer(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str
    phone: str
    country: str


class Product(BaseModel):
    id: str
    name: str
    niche: str
    quantity: int

class Payment(BaseModel):
    amount_usd: float
    method: str
    status: str


class WebhookPayload(BaseModel):
    transaction_id: str
    transaction_time: datetime
    event: str

    customer: Customer
    product: Product
    payment: Payment
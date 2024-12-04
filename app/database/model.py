from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional


@dataclass
class Patient:
    id: str
    name: str
    phone: str
    email: Optional[str]
    address: Optional[str]
    created_at: datetime
    medical_history: str = ""
    notes: str = ""
    birth_date: Optional[datetime] = None
    gender: Optional[str] = None
    emergency_contact: Optional[str] = None


@dataclass
class Service:
    id: str
    name: str
    price: Decimal
    description: str
    category: str
    duration: int  # in minutes
    active: bool = True
    created_at: datetime = datetime.now()
    modified_at: datetime = datetime.now()


@dataclass
class Transaction:
    id: str
    patient_id: str
    total_amount: Decimal
    payment_method: str
    transaction_date: datetime
    status: str  # pending, completed, cancelled
    items: List['TransactionItem']
    notes: str = ""
    discount_amount: Decimal = Decimal('0')
    tax_amount: Decimal = Decimal('0')
    created_by: str = ""


@dataclass
class TransactionItem:
    id: str
    transaction_id: str
    service_id: str
    quantity: int
    price: Decimal
    discount: Decimal = Decimal('0')
    notes: str = ""


@dataclass
class Appointment:
    id: str
    patient_id: str
    service_id: str
    start_time: datetime
    end_time: datetime
    status: str  # scheduled, completed, cancelled, no-show
    notes: str = ""
    created_at: datetime = datetime.now()
    modified_at: datetime = datetime.now()


@dataclass
class Staff:
    id: str
    name: str
    email: str
    phone: str
    role: str  # admin, doctor, therapist, receptionist
    active: bool = True
    created_at: datetime = datetime.now()
    modified_at: datetime = datetime.now()
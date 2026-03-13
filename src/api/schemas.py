import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AccountBase(BaseModel):
    mask: str = Field(..., max_length=4)
    institution_name: str

class AccountCreate(AccountBase):
    pass

class AccountResponse(AccountBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
class TransactionBase(BaseModel):
    external_id: str
    date: date
    amount: float
    merchant_name: str
    description: str

class TransactionCreate(TransactionBase):
    account_id: uuid.UUID

class TransactionResponse(TransactionBase):
    id: uuid.UUID
    account_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class IngestTransactionsRequest(BaseModel):
    account_id: uuid.UUID
    transactions: List[TransactionBase]

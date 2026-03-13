import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api import deps, schemas
from src.core.repository import BaseRepository
from src.models.core import BankAccount, User

router = APIRouter()
account_repo = BaseRepository(BankAccount)
user_repo = BaseRepository(User)

@router.post("/", response_model=schemas.AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    *,
    db: AsyncSession = Depends(deps.get_db),
    account_in: schemas.AccountCreate,
    user_id: uuid.UUID
) -> Any:
    """
    Create new bank account for a user.
    """
    user = await user_repo.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    obj_in = account_in.model_dump()
    obj_in["user_id"] = user_id
    account = await account_repo.create(db=db, obj_in=obj_in)
    return account

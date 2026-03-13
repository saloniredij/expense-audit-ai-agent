import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api import deps, schemas
from src.core.repository import BaseRepository
from src.models.core import User

router = APIRouter()
user_repo = BaseRepository(User)

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = await user_repo.create(db=db, obj_in=user_in.model_dump())
    return user

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def read_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get user by ID.
    """
    user = await user_repo.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

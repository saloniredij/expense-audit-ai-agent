import uuid
import json
import asyncio
from typing import Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.api import deps, schemas
from src.core.repository import BaseRepository
from src.models.core import User, Transaction
from src.models.audit import AuditReport, AuditStatus
from src.agent.graph import audit_graph

router = APIRouter()
user_repo = BaseRepository(User)
audit_repo = BaseRepository(AuditReport)

async def run_audit_background_task(audit_id: uuid.UUID, user_id: uuid.UUID, db_url: str):
    """
    Background worker function that runs the LangGraph AI Audit.
    In a real system this would be Celery or Temporal. For this, we use FastAPI BackgroundTasks 
    but must instantiate a fresh DB session string since the HTTP request session is closed.
    """
    from src.core.database import db_manager
    from src.agent.state import AgentState

    # We use a new session explicitly for the background task
    async for session in db_manager.get_session():
        try:
            # 1. Update status to PROCESSING
            audit = await audit_repo.get(db=session, id=audit_id)
            if not audit:
                return
            audit.status = AuditStatus.PROCESSING
            session.add(audit)
            await session.commit()

            # 2. Fetch all transactions for the user
            # Joining transactions via accounts
            result = await session.execute(
                select(Transaction).join(Transaction.account).where(Transaction.account.has(user_id=user_id))
            )
            transactions_db = result.scalars().all()
            
            # Serialize for agent state
            transactions_dicts = []
            for t in transactions_db:
                transactions_dicts.append({
                    "id": str(t.id),
                    "amount": t.amount,
                    "merchant_name": t.merchant_name,
                    "date": t.date,
                    "description": t.description
                })

            # 3. Invoke LangGraph Agent
            initial_state: AgentState = {
                "user_id": str(user_id),
                "transactions": transactions_dicts,
                "merchant_frequencies": {},
                "identified_subscriptions": [],
                "final_output": None,
                "error": None
            }
            
            final_state = await audit_graph.ainvoke(initial_state)

            # 4. Save results back
            audit_refreshed = await audit_repo.get(db=session, id=audit_id)
            if final_state.get("error"):
                audit_refreshed.status = AuditStatus.FAILED
                audit_refreshed.error_message = final_state["error"]
            else:
                audit_refreshed.status = AuditStatus.COMPLETED
                final_out = final_state.get("final_output")
                if final_out:
                    audit_refreshed.raw_result = final_out.model_dump()
                else:
                    audit_refreshed.raw_result = {}
            
            session.add(audit_refreshed)
            await session.commit()
            return
            
        except Exception as e:
            await session.rollback()
            audit_refreshed = await audit_repo.get(db=session, id=audit_id)
            if audit_refreshed:
                audit_refreshed.status = AuditStatus.FAILED
                audit_refreshed.error_message = str(e)
                session.add(audit_refreshed)
                await session.commit()
            raise e

class AuditCreateRequest(schemas.BaseModel):
    user_id: uuid.UUID

class AuditResponse(schemas.BaseModel):
    id: uuid.UUID
    status: AuditStatus
    raw_result: Any = None
    error_message: str | None = None

@router.post("/", status_code=status.HTTP_202_ACCEPTED, response_model=AuditResponse)
async def trigger_audit(
    *,
    db: AsyncSession = Depends(deps.get_db),
    payload: AuditCreateRequest,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Trigger an asynchronous expense audit for a user.
    """
    user = await user_repo.get(db=db, id=payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create Pending Audit Record
    audit = await audit_repo.create(db=db, obj_in={"user_id": payload.user_id, "status": AuditStatus.PENDING})
    
    # Offload execution
    from src.core.config import settings
    background_tasks.add_task(run_audit_background_task, audit.id, payload.user_id, settings.DATABASE_URL)
    
    return audit

@router.get("/{audit_id}", response_model=AuditResponse)
async def get_audit_status(
    audit_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Retrieve the status and results of a generated audit.
    """
    audit = await audit_repo.get(db=db, id=audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit

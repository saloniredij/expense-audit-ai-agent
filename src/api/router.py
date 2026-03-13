from fastapi import APIRouter
from .routes import users, accounts, transactions, audits

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(audits.router, prefix="/audits", tags=["audits"])

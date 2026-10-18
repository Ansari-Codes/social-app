"""
Routes/AnalyticsRts.py — authenticated dashboard analytics endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.sqliteback.Database.db import DB, User
from backend.sqliteback.Functions.AnalyticsFns import AnalyticsFns
from backend.sqliteback.Helpers.AuthHelp import get_current_user
from backend.sqliteback.Models.AnalyticsModels import DashboardAnalytics
from backend.sqliteback.Models.core import BaseResponse

analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])
analytics_fns = AnalyticsFns(DB)


@analytics_router.get("/me", response_model=BaseResponse[DashboardAnalytics])
def get_my_analytics(
    days: int = Query(default=30, ge=7, le=365),
    me: User = Depends(get_current_user),
):
    try:
        data = analytics_fns.dashboard(me.id, days)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    return BaseResponse[DashboardAnalytics](data=DashboardAnalytics.model_validate(data))

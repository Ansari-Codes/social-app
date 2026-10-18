"""
Routes/NotificationRts.py — authenticated in-app notification APIs.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.sqliteback.Database.db import DB, User
from backend.sqliteback.Functions.NotificationFns import NotificationFns
from backend.sqliteback.Helpers.AuthHelp import get_current_user
from backend.sqliteback.Models.core import BaseResponse
from backend.sqliteback.Models.NotificationModels import DataNotifications, DataOk, NotificationPublic

notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])
notification_fns = NotificationFns(DB)


@notifications_router.get("/", response_model=BaseResponse[DataNotifications])
def get_notifications(me: User = Depends(get_current_user)):
    notifications = notification_fns.list_for_user(me.id)
    data = DataNotifications(
        notifications=[NotificationPublic.model_validate(item) for item in notifications],
        unread_count=notification_fns.unread_count(me.id),
    )
    return BaseResponse[DataNotifications](data=data)


@notifications_router.post("/read-all", response_model=BaseResponse[DataOk])
def mark_all_notifications_read(me: User = Depends(get_current_user)):
    notification_fns.mark_all_read(me.id)
    return BaseResponse[DataOk](data=DataOk(ok=True))


@notifications_router.patch("/{notification_id}/read", response_model=BaseResponse[DataOk])
def mark_notification_read(
    notification_id: int,
    me: User = Depends(get_current_user),
):
    if not notification_fns.mark_read(me.id, notification_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
    return BaseResponse[DataOk](data=DataOk(ok=True))

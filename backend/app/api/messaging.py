from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.schemas import MessageCreate, MessageListResponse, MessageResponse
from app.core.database import get_db
from app.models.user import Message, User, UserRole

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/send", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to another user. Athletes can message their coaches, coaches can message their athletes."""
    # Verify recipient exists
    result = await db.execute(select(User).where(User.id == data.recipient_id))
    recipient = result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    # Authorization: athletes can message their coach, coaches can message their athletes, admins can message anyone
    if current_user.role == UserRole.ATHLETE:
        if recipient.role != UserRole.COACH or current_user.coach_id != recipient.id:
            raise HTTPException(
                status_code=403,
                detail="You can only send messages to your assigned coach",
            )
    elif current_user.role == UserRole.COACH:
        if recipient.role != UserRole.ATHLETE or recipient.coach_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only send messages to your linked athletes",
            )
    # Admins can message anyone

    message = Message(
        sender_id=current_user.id,
        recipient_id=data.recipient_id,
        subject=data.subject,
        body=data.body,
    )
    db.add(message)
    await db.flush()

    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        sender_name=current_user.full_name,
        recipient_id=message.recipient_id,
        recipient_name=recipient.full_name,
        subject=message.subject,
        body=message.body,
        is_read=message.is_read,
        created_at=message.created_at,
    )


@router.get("/inbox", response_model=MessageListResponse)
async def get_inbox(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages received by the current user."""
    query = select(Message).where(Message.recipient_id == current_user.id)
    count_query = select(func.count(Message.id)).where(Message.recipient_id == current_user.id)

    if unread_only:
        query = query.where(Message.is_read == False)
        count_query = count_query.where(Message.is_read == False)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(Message.created_at.desc()).offset(skip).limit(limit)
    )
    messages = result.scalars().all()

    # Fetch sender/recipient names
    response_messages = []
    for m in messages:
        sender = await db.execute(select(User.full_name).where(User.id == m.sender_id))
        recipient = await db.execute(select(User.full_name).where(User.id == m.recipient_id))
        response_messages.append(
            MessageResponse(
                id=m.id,
                sender_id=m.sender_id,
                sender_name=sender.scalar() or "Unknown",
                recipient_id=m.recipient_id,
                recipient_name=recipient.scalar() or "Unknown",
                subject=m.subject,
                body=m.body,
                is_read=m.is_read,
                created_at=m.created_at,
            )
        )

    return MessageListResponse(messages=response_messages, total=total)


@router.get("/sent", response_model=MessageListResponse)
async def get_sent_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages sent by the current user."""
    count_query = select(func.count(Message.id)).where(Message.sender_id == current_user.id)
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(
        select(Message)
        .where(Message.sender_id == current_user.id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()

    response_messages = []
    for m in messages:
        sender = await db.execute(select(User.full_name).where(User.id == m.sender_id))
        recipient = await db.execute(select(User.full_name).where(User.id == m.recipient_id))
        response_messages.append(
            MessageResponse(
                id=m.id,
                sender_id=m.sender_id,
                sender_name=sender.scalar() or "Unknown",
                recipient_id=m.recipient_id,
                recipient_name=recipient.scalar() or "Unknown",
                subject=m.subject,
                body=m.body,
                is_read=m.is_read,
                created_at=m.created_at,
            )
        )

    return MessageListResponse(messages=response_messages, total=total)


@router.put("/{message_id}/read")
async def mark_message_read(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a message as read."""
    result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.recipient_id == current_user.id,
        )
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.is_read = True
    await db.flush()
    return {"status": "ok"}


@router.get("/coaches", response_model=list)
async def list_messageable_coaches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List coaches the current athlete can message (their assigned coach)."""
    if current_user.role == UserRole.ATHLETE and current_user.coach_id:
        result = await db.execute(
            select(User).where(User.id == current_user.coach_id, User.is_active == True)
        )
        coach = result.scalar_one_or_none()
        if coach:
            return [{"id": coach.id, "full_name": coach.full_name, "email": coach.email}]
    elif current_user.role == UserRole.COACH:
        result = await db.execute(
            select(User).where(
                User.coach_id == current_user.id,
                User.role == UserRole.ATHLETE,
                User.is_active == True,
            ).order_by(User.full_name)
        )
        athletes = result.scalars().all()
        return [{"id": a.id, "full_name": a.full_name, "email": a.email} for a in athletes]
    elif current_user.role == UserRole.ADMIN:
        result = await db.execute(
            select(User).where(User.is_active == True, User.id != current_user.id).order_by(User.full_name)
        )
        users = result.scalars().all()
        return [{"id": u.id, "full_name": u.full_name, "email": u.email} for u in users]
    return []

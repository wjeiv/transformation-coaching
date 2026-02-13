from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ContactRequestInput
from app.core.database import get_db
from app.models.user import ContactRequest

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/contact", status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    data: ContactRequestInput,
    db: AsyncSession = Depends(get_db),
):
    """Submit a contact/inquiry form (no authentication required)."""
    contact = ContactRequest(
        name=data.name,
        email=data.email,
        phone=data.phone,
        message=data.message,
    )
    db.add(contact)
    await db.flush()
    return {
        "status": "ok",
        "message": "Thank you for reaching out! We will get back to you soon.",
    }

"""
Shared Conversations Endpoints
Handles sharing and viewing shared conversations
"""

import secrets
from datetime import datetime, timedelta
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.infrastructure.database.models import SharedConversation, User

router = APIRouter(prefix="/shared", tags=["Shared Conversations"])


# Pydantic Models
class ShareConversationRequest(BaseModel):
    """Request to share a conversation"""
    session_id: str
    messages: list[dict]
    title: str | None = None
    expires_in_days: int | None = 30  # Default 30 days


class ShareConversationResponse(BaseModel):
    """Response with share URL"""
    share_id: str
    share_url: str
    expires_at: datetime | None


class SharedConversationView(BaseModel):
    """Shared conversation data for viewing"""
    share_id: str
    title: str | None
    messages: list[dict]
    created_at: datetime
    view_count: int


@router.post("/share", response_model=ShareConversationResponse)
async def share_conversation(
    request: ShareConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Share a conversation and get a public link.

    Creates a shareable link for the conversation that can be accessed by anyone.
    """
    # Generate unique share_id
    share_id = secrets.token_urlsafe(16)

    # Calculate expiration date
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

    # Create shared conversation
    shared_conv = SharedConversation(
        share_id=share_id,
        session_id=request.session_id,
        user_id=current_user.id,
        title=request.title,
        messages_list=request.messages,
        expires_at=expires_at,
        is_active=True,
        view_count=0
    )

    db.add(shared_conv)
    await db.commit()
    await db.refresh(shared_conv)

    return ShareConversationResponse(
        share_id=share_id,
        share_url=f"/shared/{share_id}",
        expires_at=expires_at
    )


@router.get("/{share_id}", response_model=SharedConversationView)
async def view_shared_conversation(
    share_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    View a shared conversation by its share_id.

    This endpoint is public and doesn't require authentication.
    """
    # Query the shared conversation
    result = await db.execute(
        select(SharedConversation).where(SharedConversation.share_id == share_id)
    )
    shared_conv = result.scalar_one_or_none()

    if not shared_conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared conversation not found"
        )

    # Check if expired
    if shared_conv.is_expired or not shared_conv.is_active:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This shared conversation has expired or is no longer available"
        )

    # Increment view count
    shared_conv.increment_view_count()
    await db.commit()

    return SharedConversationView(
        share_id=shared_conv.share_id,
        title=shared_conv.title,
        messages=shared_conv.messages_list,
        created_at=shared_conv.created_at,
        view_count=shared_conv.view_count
    )


@router.delete("/{share_id}")
async def delete_shared_conversation(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete/deactivate a shared conversation.

    Only the owner or admin can delete a shared conversation.
    """
    # Query the shared conversation
    result = await db.execute(
        select(SharedConversation).where(SharedConversation.share_id == share_id)
    )
    shared_conv = result.scalar_one_or_none()

    if not shared_conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared conversation not found"
        )

    # Check ownership or admin
    if shared_conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this shared conversation"
        )

    # Soft delete - just deactivate
    shared_conv.is_active = False
    await db.commit()

    return {"message": "Shared conversation deleted successfully"}


@router.get("/user/list")
async def list_user_shared_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List all shared conversations created by the current user.
    """
    result = await db.execute(
        select(SharedConversation)
        .where(SharedConversation.user_id == current_user.id)
        .where(SharedConversation.is_active == True)
        .order_by(SharedConversation.created_at.desc())
    )
    shared_convs = result.scalars().all()

    return [
        {
            "share_id": conv.share_id,
            "title": conv.title,
            "session_id": conv.session_id,
            "created_at": conv.created_at,
            "expires_at": conv.expires_at,
            "view_count": conv.view_count,
            "is_expired": conv.is_expired
        }
        for conv in shared_convs
    ]

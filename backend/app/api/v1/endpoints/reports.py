"""
Reports Endpoints
CRUD operations for reports
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db, require_permission
from app.infrastructure.database.models import Report, User
from app.schemas.report import ReportCreate, ReportListResponse, ReportResponse, ReportUpdate

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=list[ReportListResponse])
async def get_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("VIEW_REPORTS"))],
    status_filter: str | None = None,
) -> list[Report]:
    """Get all reports with optional status filter"""
    
    query = select(Report).order_by(Report.created_at.desc())
    
    if status_filter:
        query = query.where(Report.status == status_filter)
    
    result = await db.execute(query)
    reports = result.scalars().all()
    return list(reports)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("VIEW_REPORTS"))],
) -> Report:
    """Get report by ID"""
    
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Add author name
    author_result = await db.execute(
        select(User.username).where(User.id == report.author_id)
    )
    author_name = author_result.scalar_one_or_none()
    
    # Convert to dict and add author_name
    report_dict = {
        "id": report.id,
        "title": report.title,
        "description": report.description,
        "content": report.content,
        "status": report.status,
        "author_id": report.author_id,
        "author_name": author_name,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }
    
    return report_dict


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("CREATE_REPORTS"))],
) -> dict:
    """Create new report"""
    
    new_report = Report(
        title=report_data.title,
        description=report_data.description,
        content=report_data.content,
        status=report_data.status,
        author_id=current_user.id,
    )
    
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)
    
    return {
        "id": new_report.id,
        "title": new_report.title,
        "description": new_report.description,
        "content": new_report.content,
        "status": new_report.status,
        "author_id": new_report.author_id,
        "author_name": current_user.username,
        "created_at": new_report.created_at,
        "updated_at": new_report.updated_at,
    }


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: uuid.UUID,
    report_data: ReportUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("EDIT_REPORTS"))],
) -> dict:
    """Update report"""
    
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Check ownership (non-admins can only edit their own reports)
    if current_user.role != "admin" and report.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own reports"
        )
    
    # Update fields
    update_data = report_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)
    
    await db.commit()
    await db.refresh(report)
    
    return {
        "id": report.id,
        "title": report.title,
        "description": report.description,
        "content": report.content,
        "status": report.status,
        "author_id": report.author_id,
        "author_name": current_user.username,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("DELETE_REPORTS"))],
):
    """Delete report"""
    
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Check ownership (non-admins can only delete their own reports)
    if current_user.role != "admin" and report.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own reports"
        )
    
    await db.delete(report)
    await db.commit()


@router.post("/{report_id}/generate-pdf")
async def generate_pdf(
    report_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("VIEW_REPORTS"))],
) -> dict[str, str]:
    """
    Generate PDF for report
    
    TODO: Implement PDF generation with reportlab or weasyprint
    """
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Mock response - implement actual PDF generation
    return {
        "message": "PDF generation not yet implemented",
        "report_id": str(report_id),
        "report_title": report.title,
    }

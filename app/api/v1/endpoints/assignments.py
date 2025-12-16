from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models.models import Assignment, Assessment, ComplianceRequirement
from app.schemas.assignment import AssignmentResponse, AssessmentResponse, AssignmentCreate, AssessmentUpdate

router = APIRouter()


@router.get('/', response_model=List[AssignmentResponse])
async def list_assignments(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Assignment))
    items = result.scalars().all()
    return items


@router.get('/{assignment_id}', response_model=AssignmentResponse)
async def get_assignment(assignment_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Assignment not found')
    return item


@router.get('/{assignment_id}/assessments', response_model=List[AssessmentResponse])
async def get_assignment_assessments(assignment_id: int, db: AsyncSession = Depends(get_session)):
    # Eagerly load compliance_requirement to get statement and section
    result = await db.execute(
        select(Assessment)
        .options(selectinload(Assessment.compliance_requirement))
        .where(Assessment.assignment_id == assignment_id)
    )
    items = result.scalars().all()
    
    # Build response with enriched data from compliance_requirement
    response = []
    for item in items:
        # Use description if available, fall back to title, then control_identifier
        statement = item.control_identifier
        if item.compliance_requirement:
            statement = item.compliance_requirement.description or item.compliance_requirement.title
        
        data = {
            'id': item.id,
            'vendor_id': item.vendor_id,
            'assignment_id': item.assignment_id,
            'control_identifier': item.control_identifier,
            'statement': statement,
            'section': item.compliance_requirement.category if item.compliance_requirement else None,
            'compliant': item.compliant,
            'remark': item.remark,
            'poc': item.poc,
            'status': item.status
        }
        response.append(AssessmentResponse(**data))
    
    return response


@router.post('/', response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(payload: AssignmentCreate, db: AsyncSession = Depends(get_session)):
    a = Assignment(
        name=payload.name,
        description=payload.description,
        vendor_id=payload.vendor_id,
        standard_id=payload.standard_id,
        due_date=payload.due_date
    )
    db.add(a)
    await db.flush()
    await db.refresh(a)
    return a


@router.put('/assessments/{assessment_id}', response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: int, 
    payload: AssessmentUpdate, 
    db: AsyncSession = Depends(get_session)
):
    """Update an assessment with new compliance status, remarks, POC, etc."""
    result = await db.execute(
        select(Assessment)
        .options(selectinload(Assessment.compliance_requirement))
        .where(Assessment.id == assessment_id)
    )
    assessment = result.scalars().first()
    
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Assessment not found')
    
    # Update fields if provided
    if payload.compliant is not None:
        assessment.compliant = payload.compliant
    if payload.remark is not None:
        assessment.remark = payload.remark
    if payload.poc is not None:
        assessment.poc = payload.poc
    if payload.status is not None:
        assessment.status = payload.status
    
    await db.flush()
    await db.refresh(assessment)
    
    # Build enriched response
    statement = assessment.control_identifier
    if assessment.compliance_requirement:
        statement = assessment.compliance_requirement.description or assessment.compliance_requirement.title
    
    response_data = {
        'id': assessment.id,
        'vendor_id': assessment.vendor_id,
        'assignment_id': assessment.assignment_id,
        'control_identifier': assessment.control_identifier,
        'statement': statement,
        'section': assessment.compliance_requirement.category if assessment.compliance_requirement else None,
        'compliant': assessment.compliant,
        'remark': assessment.remark,
        'poc': assessment.poc,
        'status': assessment.status
    }
    
    return AssessmentResponse(**response_data)

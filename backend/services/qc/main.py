# QC Service - Backend Implementation for Phase 2.3
# This service provides QC Task management endpoints

"""
QC Task Backend Service
Provides API endpoints for QC task management
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

app = FastAPI(
    title="QC Task Service",
    description="Quality Control Task Management API",
    version="1.0.0"
)

# Enums
class QCTaskType(str, Enum):
    COI_VERIFICATION = "coi_verification"
    PAYMENT_VERIFICATION = "payment_verification"
    ITINERARY_REVIEW = "itinerary_review"
    DOCUMENT_CHECK = "document_check"
    OTHER = "other"

class QCTaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

# Models
class QCTaskCreate(BaseModel):
    charter_id: int
    task_type: QCTaskType
    title: str
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: datetime
    notes: Optional[str] = None

class QCTaskUpdate(BaseModel):
    status: Optional[QCTaskStatus] = None
    assigned_to: Optional[int] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None

class QCTask(QCTaskCreate):
    id: int
    status: QCTaskStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_to_name: Optional[str] = None

# Mock data storage (in production, use database)
qc_tasks: List[QCTask] = []
task_id_counter = 1

@app.get("/")
async def root():
    return {"service": "qc-tasks", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/qc/tasks", response_model=List[QCTask])
async def list_qc_tasks(
    status: Optional[QCTaskStatus] = Query(None),
    task_type: Optional[QCTaskType] = Query(None),
    charter_id: Optional[int] = Query(None)
):
    """Get all QC tasks with optional filters"""
    result = qc_tasks
    
    if status:
        result = [t for t in result if t.status == status]
    if task_type:
        result = [t for t in result if t.task_type == task_type]
    if charter_id:
        result = [t for t in result if t.charter_id == charter_id]
    
    return result

@app.get("/api/v1/qc/tasks/{task_id}", response_model=QCTask)
async def get_qc_task(task_id: int):
    """Get a specific QC task by ID"""
    task = next((t for t in qc_tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="QC task not found")
    return task

@app.post("/api/v1/qc/tasks", response_model=QCTask, status_code=201)
async def create_qc_task(task: QCTaskCreate):
    """Create a new QC task"""
    global task_id_counter
    
    new_task = QCTask(
        id=task_id_counter,
        status=QCTaskStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=None,
        completed_at=None,
        assigned_to_name=None,
        **task.dict()
    )
    
    qc_tasks.append(new_task)
    task_id_counter += 1
    
    return new_task

@app.put("/api/v1/qc/tasks/{task_id}", response_model=QCTask)
async def update_qc_task(task_id: int, task_update: QCTaskUpdate):
    """Update an existing QC task"""
    task = next((t for t in qc_tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="QC task not found")
    
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    task.updated_at = datetime.utcnow()
    
    return task

@app.post("/api/v1/qc/tasks/{task_id}/complete")
async def complete_qc_task(task_id: int):
    """Mark a QC task as completed"""
    task = next((t for t in qc_tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="QC task not found")
    
    task.status = QCTaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    
    return task

@app.post("/api/v1/qc/tasks/{task_id}/start")
async def start_qc_task(task_id: int):
    """Mark a QC task as in progress"""
    task = next((t for t in qc_tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="QC task not found")
    
    task.status = QCTaskStatus.IN_PROGRESS
    task.updated_at = datetime.utcnow()
    
    return task

@app.post("/api/v1/qc/tasks/{task_id}/fail")
async def fail_qc_task(task_id: int):
    """Mark a QC task as failed"""
    task = next((t for t in qc_tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="QC task not found")
    
    task.status = QCTaskStatus.FAILED
    task.updated_at = datetime.utcnow()
    
    return task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8015)

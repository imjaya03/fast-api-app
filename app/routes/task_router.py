from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from app.models.task_model import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskRead,
    TaskReadWithRelations,
    User,
    Project,
    Tag,
    Comment,
    TaskStatus,
    TaskPriority,
    PaginationParams,
)
from app.models.response_model import ResponseModel
from app.database import get_session

router: APIRouter = APIRouter()


@router.get("/", response_model=ResponseModel[List[TaskRead]])
def get_tasks(
    session: Session = Depends(get_session),
    pagination: PaginationParams = Depends(),
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
) -> ResponseModel[List[TaskRead]]:
    """Get all tasks with optional filtering"""
    query = select(Task)

    # Apply filters
    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    if project_id:
        query = query.where(Task.project_id == project_id)
    if assignee_id:
        query = query.where(Task.assignee_id == assignee_id)

    # Apply pagination
    query = query.offset(pagination.skip).limit(pagination.limit)

    tasks = session.exec(query).all()
    task_reads = [TaskRead.model_validate(task) for task in tasks]
    return ResponseModel(data=task_reads)


@router.get("/{task_id}", response_model=TaskReadWithRelations)
def get_task(
    task_id: int, session: Session = Depends(get_session)
) -> TaskReadWithRelations:
    """Get a single task with all relationships"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskReadWithRelations.model_validate(task)


@router.post("/", response_model=TaskRead)
def create_task(
    task_data: TaskCreate, session: Session = Depends(get_session)
) -> TaskRead:
    """Create a new task"""

    # Validate project exists if provided
    if task_data.project_id:
        project = session.get(Project, task_data.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    # Validate assignee exists if provided
    if task_data.assignee_id:
        assignee = session.get(User, task_data.assignee_id)
        if not assignee:
            raise HTTPException(status_code=404, detail="User not found")

    # Validate parent task exists if provided
    if task_data.parent_task_id:
        parent_task = session.get(Task, task_data.parent_task_id)
        if not parent_task:
            raise HTTPException(status_code=404, detail="Parent task not found")

    # Create task (excluding tag_ids from model_dump)
    task_dict = task_data.model_dump(exclude={"tag_ids"})
    task = Task(**task_dict)
    session.add(task)
    session.commit()
    session.refresh(task)

    # Add tags if provided
    if task_data.tag_ids:
        tags: List[Tag] = []
        for tag_id in task_data.tag_ids:
            tag = session.get(Tag, tag_id)
            if tag:
                tags.append(tag)
        task.tags.extend(tags)
        session.add(task)
        session.commit()
        session.refresh(task)

    return TaskRead.model_validate(task)


@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int, task_data: TaskUpdate, session: Session = Depends(get_session)
) -> TaskRead:
    """Update an existing task"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Validate assignee exists if provided
    if task_data.assignee_id:
        assignee = session.get(User, task_data.assignee_id)
        if not assignee:
            raise HTTPException(status_code=404, detail="User not found")

    # Update task fields
    update_data = task_data.model_dump(exclude_unset=True, exclude={"tag_ids"})
    for field, value in update_data.items():
        setattr(task, field, value)

    # Update tags if provided
    if task_data.tag_ids is not None:
        tags: List[Tag] = []
        for tag_id in task_data.tag_ids:
            tag = session.get(Tag, tag_id)
            if tag:
                tags.append(tag)
        task.tags = tags

    session.add(task)
    session.commit()
    session.refresh(task)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", response_model=TaskRead)
def delete_task(task_id: int, session: Session = Depends(get_session)) -> TaskRead:
    """Delete a task"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task_read = TaskRead.model_validate(task)
    session.delete(task)
    session.commit()
    return task_read


@router.get("/{task_id}/subtasks", response_model=ResponseModel[List[TaskRead]])
def get_subtasks(
    task_id: int, session: Session = Depends(get_session)
) -> ResponseModel[List[TaskRead]]:
    """Get all subtasks of a task"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    subtasks = session.exec(select(Task).where(Task.parent_task_id == task_id)).all()
    subtask_reads = [TaskRead.model_validate(subtask) for subtask in subtasks]
    return ResponseModel(data=subtask_reads)


@router.get("/{task_id}/comments", response_model=ResponseModel[List[Comment]])
def get_task_comments(
    task_id: int, session: Session = Depends(get_session)
) -> ResponseModel[List[Comment]]:
    """Get all comments for a task"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    comments = list(
        session.exec(select(Comment).where(Comment.task_id == task_id)).all()
    )
    return ResponseModel(data=comments)


# Statistics endpoints
@router.get("/stats/summary")
def get_task_stats(session: Session = Depends(get_session)) -> Dict[str, Any]:
    """Get task statistics summary"""
    total_tasks = len(session.exec(select(Task)).all())
    completed_tasks = len(session.exec(select(Task).where(Task.is_completed)).all())
    pending_tasks = len(
        session.exec(select(Task).where(Task.status == TaskStatus.PENDING)).all()
    )
    in_progress_tasks = len(
        session.exec(select(Task).where(Task.status == TaskStatus.IN_PROGRESS)).all()
    )

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "in_progress_tasks": in_progress_tasks,
        "completion_rate": round(
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2
        ),
    }

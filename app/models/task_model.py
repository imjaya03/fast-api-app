from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum


def utc_now() -> datetime:
    """Helper function to get current UTC datetime"""
    return datetime.now(timezone.utc)


# Enums for better type safety
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Association table for many-to-many relationship (Task <-> Tag)
class TaskTagLink(SQLModel, table=True):
    task_id: Optional[int] = Field(
        default=None, foreign_key="task.id", primary_key=True
    )
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)


# Base Models (shared fields)
class UserBase(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(regex=r"^[^@]+@[^@]+\.[^@]+$")
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)


class ProjectBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)


class TaskBase(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    is_completed: bool = Field(default=False)
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(default=None, ge=0)
    actual_hours: Optional[float] = Field(default=None, ge=0)


class TagBase(SQLModel):
    name: str = Field(min_length=1, max_length=50)
    color: Optional[str] = Field(default="#3498db", regex=r"^#[0-9A-Fa-f]{6}$")


class CommentBase(SQLModel):
    content: str = Field(min_length=1, max_length=1000)


# Database Models (table=True)
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # One-to-Many: User has many Projects
    owned_projects: List["Project"] = Relationship(back_populates="owner")

    # One-to-Many: User has many assigned Tasks
    assigned_tasks: List["Task"] = Relationship(back_populates="assignee")

    # One-to-Many: User has many Comments
    comments: List["Comment"] = Relationship(back_populates="author")


class Project(ProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Foreign Key: Many-to-One relationship with User
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")

    # Many-to-One: Project belongs to one User
    owner: Optional[User] = Relationship(back_populates="owned_projects")

    # One-to-Many: Project has many Tasks
    tasks: List["Task"] = Relationship(back_populates="project")


class Tag(TagBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)

    # Many-to-Many: Tags can be associated with many Tasks
    tasks: List["Task"] = Relationship(back_populates="tags", link_model=TaskTagLink)


class Task(TaskBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Foreign Keys
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    assignee_id: Optional[int] = Field(default=None, foreign_key="user.id")
    parent_task_id: Optional[int] = Field(default=None, foreign_key="task.id")

    # Many-to-One: Task belongs to one Project
    project: Optional[Project] = Relationship(back_populates="tasks")

    # Many-to-One: Task assigned to one User
    assignee: Optional[User] = Relationship(back_populates="assigned_tasks")

    # Self-referencing One-to-Many: Task can have subtasks
    parent_task: Optional["Task"] = Relationship(
        back_populates="subtasks", sa_relationship_kwargs={"remote_side": "Task.id"}
    )
    subtasks: List["Task"] = Relationship(back_populates="parent_task")

    # Many-to-Many: Task can have many Tags
    tags: List[Tag] = Relationship(back_populates="tasks", link_model=TaskTagLink)

    # One-to-Many: Task can have many Comments
    comments: List["Comment"] = Relationship(back_populates="task")


class Comment(CommentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Foreign Keys
    task_id: Optional[int] = Field(default=None, foreign_key="task.id")
    author_id: Optional[int] = Field(default=None, foreign_key="user.id")

    # Many-to-One: Comment belongs to one Task
    task: Optional[Task] = Relationship(back_populates="comments")

    # Many-to-One: Comment belongs to one User (author)
    author: Optional[User] = Relationship(back_populates="comments")


# Request Models (for API input)
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=100)


class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[str] = Field(default=None, regex=r"^[^@]+@[^@]+\.[^@]+$")
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class ProjectCreate(ProjectBase):
    owner_id: int


class ProjectUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class TaskCreate(TaskBase):
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    tag_ids: Optional[List[int]] = Field(default_factory=list)


class TaskUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    is_completed: Optional[bool] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(default=None, ge=0)
    actual_hours: Optional[float] = Field(default=None, ge=0)
    assignee_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None


class TagCreate(TagBase):
    pass


class TagUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    color: Optional[str] = Field(default=None, regex=r"^#[0-9A-Fa-f]{6}$")


class CommentCreate(CommentBase):
    task_id: int
    author_id: int


class CommentUpdate(SQLModel):
    content: Optional[str] = Field(default=None, min_length=1, max_length=1000)


# Response Models (for API output with populated relationships)
class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime


class UserReadWithRelations(UserRead):
    owned_projects: List["ProjectRead"] = []
    assigned_tasks: List["TaskRead"] = []
    comments: List["CommentRead"] = []


class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: Optional[int] = None


class ProjectReadWithRelations(ProjectRead):
    owner: Optional[UserRead] = None
    tasks: List["TaskRead"] = []


class TagRead(TagBase):
    id: int
    created_at: datetime


class TagReadWithTasks(TagRead):
    tasks: List["TaskRead"] = []


class CommentRead(CommentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    task_id: Optional[int] = None
    author_id: Optional[int] = None


class CommentReadWithRelations(CommentRead):
    task: Optional["TaskRead"] = None
    author: Optional[UserRead] = None


class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    parent_task_id: Optional[int] = None


class TaskReadWithRelations(TaskRead):
    project: Optional[ProjectRead] = None
    assignee: Optional[UserRead] = None
    parent_task: Optional["TaskRead"] = None
    subtasks: List["TaskRead"] = []
    tags: List[TagRead] = []
    comments: List[CommentRead] = []


# Pagination and Filter Models
class TaskFilter(SQLModel):
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    is_completed: Optional[bool] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None


class PaginationParams(SQLModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)


# Bulk Operations
class TaskBulkUpdate(SQLModel):
    task_ids: List[int]
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    add_tag_ids: Optional[List[int]] = None
    remove_tag_ids: Optional[List[int]] = None

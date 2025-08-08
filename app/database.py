from sqlmodel import SQLModel, create_engine, Session, select
from typing import Generator
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)


def create_db_and_tables():
    """Create database and tables"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    with Session(engine) as session:
        yield session


# Initialize database on import
def init_db():
    """Initialize database with sample data"""
    from app.models.task_model import (
        User,
        Project,
        Task,
        Tag,
        Comment,
        TaskStatus,
        TaskPriority,
    )

    create_db_and_tables()

    # Create sample data
    with Session(engine) as session:
        # Check if we already have data
        existing_users = session.exec(select(User)).first()
        if existing_users:
            return

        # Create users
        user1 = User(
            username="john_doe", email="john@example.com", full_name="John Doe"
        )
        user2 = User(
            username="jane_smith", email="jane@example.com", full_name="Jane Smith"
        )
        session.add(user1)
        session.add(user2)
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        # Create projects
        project1 = Project(
            name="Web Application",
            description="Building a modern web application",
            owner_id=user1.id,
        )
        project2 = Project(
            name="Mobile App",
            description="Creating a mobile application",
            owner_id=user2.id,
        )
        session.add(project1)
        session.add(project2)
        session.commit()
        session.refresh(project1)
        session.refresh(project2)

        # Create tags
        tag1 = Tag(name="Frontend", color="#3498db")
        tag2 = Tag(name="Backend", color="#e74c3c")
        tag3 = Tag(name="Database", color="#2ecc71")
        tag4 = Tag(name="Bug Fix", color="#f39c12")
        session.add_all([tag1, tag2, tag3, tag4])
        session.commit()

        # Create tasks
        task1 = Task(
            title="Create user authentication",
            description="Implement JWT authentication for the application",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            project_id=project1.id,
            assignee_id=user1.id,
            estimated_hours=8.0,
        )

        task2 = Task(
            title="Design database schema",
            description="Create the database schema for the application",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            project_id=project1.id,
            assignee_id=user2.id,
            estimated_hours=4.0,
            actual_hours=3.5,
            is_completed=True,
        )

        task3 = Task(
            title="Build React components",
            description="Create reusable React components for the UI",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            project_id=project1.id,
            assignee_id=user1.id,
            parent_task_id=None,  # This will be set after task1 is saved
            estimated_hours=12.0,
        )

        session.add_all([task1, task2, task3])
        session.commit()
        session.refresh(task1)
        session.refresh(task2)
        session.refresh(task3)

        # Set parent task relationship
        task3.parent_task_id = task1.id
        session.add(task3)
        session.commit()

        # Add tags to tasks (many-to-many)
        task1.tags.extend([tag2, tag3])  # Backend, Database
        task2.tags.append(tag3)  # Database
        task3.tags.append(tag1)  # Frontend
        session.add_all([task1, task2, task3])
        session.commit()

        # Create comments
        comment1 = Comment(
            content="Great progress on this task!", task_id=task1.id, author_id=user2.id
        )
        comment2 = Comment(
            content="Schema looks good, ready for implementation",
            task_id=task2.id,
            author_id=user1.id,
        )
        session.add_all([comment1, comment2])
        session.commit()

        print("✅ Database initialized with sample data!")


if __name__ == "__main__":
    init_db()

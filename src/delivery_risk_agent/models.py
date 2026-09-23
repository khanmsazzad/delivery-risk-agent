from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkItemStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class WorkItem(BaseModel):
    id: str
    title: str
    priority: Priority
    status: WorkItemStatus
    assignee: str | None = None
    created_at: datetime
    due_at: datetime | None = None
    blocked_by: list[str] = Field(default_factory=list)


class PullRequest(BaseModel):
    number: int
    title: str
    author: str
    created_at: datetime
    linked_work_item: str | None = None
    approved: bool = False
    ci_passed: bool = False


class ProjectSnapshot(BaseModel):
    name: str
    captured_at: datetime
    work_items: list[WorkItem] = Field(default_factory=list)
    pull_requests: list[PullRequest] = Field(default_factory=list)



class RiskFinding(BaseModel):
    rule_id: str
    title: str
    severity: RiskSeverity
    work_item_id: str | None = None
    pull_request_number: int | None = None
    evidence: list[str] = Field(default_factory=list)
    recommendation: str
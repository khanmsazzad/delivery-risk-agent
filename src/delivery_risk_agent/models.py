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
    approved: bool | None = None
    ci_passed: bool | None = None
    failed_checks: list[str] = Field(default_factory=list)


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

class PrioritizedRisk(BaseModel):
    rank: int
    title: str
    severity: RiskSeverity
    impact: str
    evidence: list[str]


class RecommendedAction(BaseModel):
    priority: int
    action: str
    rationale: str


class DeliveryRiskAssessment(BaseModel):
    executive_summary: str
    prioritized_risks: list[PrioritizedRisk] 
    recommended_actions: list[RecommendedAction] 



class RiskAdvice(BaseModel):
    finding_id: int
    impact: str
    recommended_action: str
    rationale: str

class AgentAdvice(BaseModel):
    executive_summary: str
    risk_advice: list[RiskAdvice]
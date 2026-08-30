"""Research orchestration (Ontology V2 §11, Mission 0.4).

Coordination, not analysis. This context owns the ResearchSession execution
lifecycle, the plan, the budget, job dispatch, progress, failure, resumability
and Research Completeness coordination. It owns no scraping, no embedding, no
scoring formula and no market or competitor logic.

    lifecycle.py     session status transitions -- the only place they are decided
    jobs.py          the generic job description and its ledger states
    dag.py           dependency ordering, without a workflow engine
    plan.py          the ResearchExecutionPlan and the blocked-capability register
    sources.py       per-source acquisition availability, read from the registry
    budget.py        configured / reserved / actual accounting and the guard
    completeness.py  the Research Completeness record. No formula
    repositories.py  persistence, over a duck-typed tenant database
    orchestrator.py  the coordinator

**Import discipline.** Nothing here imports `sros_gateway`: the repositories
take any object exposing `tenant_transaction(workspace_id)`. That is what keeps
the dependency graph in `service-boundaries.md` §4 acyclic while both contexts
share one deployable unit in Phase 1.

**Nothing here can dispatch blocked work.** Every domain capability is currently
blocked (D-03 scoring, D-12 and §34 NLP, and no collector-eligible source), the
planner marks those stages BLOCKED with a stated reason, and a BLOCKED job never
becomes READY. The guard is mechanical rather than remembered.

Since Mission 1.0 the acquisition reason is **derived from the Source Registry
per source** rather than restated here: D-07 is resolved, so "the registry does
not exist" would be a false reason. A planner with no registry wired blocks
acquisition anyway, because an unconsulted registry is a refusal.
"""

from .budget import (
    COST_UNIT,
    BudgetAccount,
    BudgetDecision,
    BudgetEntryKind,
    BudgetGuard,
    BudgetRefusedError,
)
from .completeness import CompletenessBasis, CompletenessRecord
from .dag import (
    DependencyCycleError,
    UnknownDependencyError,
    blocked_by_dependencies,
    dependency_closure,
    ready_job_ids,
    topological_order,
)
from .jobs import (
    ALLOWED_JOB_TRANSITIONS,
    TERMINAL_JOB_STATUSES,
    InvalidJobTransitionError,
    JobSpec,
    JobStatus,
    build_idempotency_key,
    deterministic_job_id,
    require_job_transition,
)
from .lifecycle import (
    ALLOWED_TRANSITIONS,
    CANCELLABLE_STATUSES,
    TERMINAL_STATUSES,
    InvalidTransitionError,
    can_transition,
    cancellation_target,
    is_terminal,
    next_statuses,
    require_transition,
)
from .plan import (
    BLOCKED_CAPABILITIES,
    NO_COLLECTOR_IMPLEMENTED,
    NO_NORMALIZER_IMPLEMENTED,
    PLANNER_VERSION,
    STATIC_BLOCKED_CAPABILITIES,
    BlockedCapability,
    Capability,
    PlannedStage,
    ResearchExecutionPlan,
    ResearchPlanner,
    acquisition_block,
    normalization_block,
)
from .sources import (
    RegistryDatabase,
    RegistrySourceAvailability,
    SourceAvailability,
    SourceAvailabilityProvider,
    SourceAvailabilityReport,
    StaticSourceAvailability,
    UnconsultedRegistry,
)

__all__ = [
    # lifecycle
    "ALLOWED_TRANSITIONS",
    "TERMINAL_STATUSES",
    "CANCELLABLE_STATUSES",
    "InvalidTransitionError",
    "can_transition",
    "require_transition",
    "is_terminal",
    "next_statuses",
    "cancellation_target",
    # jobs
    "JobSpec",
    "JobStatus",
    "ALLOWED_JOB_TRANSITIONS",
    "TERMINAL_JOB_STATUSES",
    "InvalidJobTransitionError",
    "require_job_transition",
    "build_idempotency_key",
    "deterministic_job_id",
    # dag
    "topological_order",
    "ready_job_ids",
    "blocked_by_dependencies",
    "dependency_closure",
    "DependencyCycleError",
    "UnknownDependencyError",
    # plan
    "Capability",
    "BlockedCapability",
    "BLOCKED_CAPABILITIES",
    "STATIC_BLOCKED_CAPABILITIES",
    "acquisition_block",
    "normalization_block",
    "PlannedStage",
    "ResearchExecutionPlan",
    "ResearchPlanner",
    "PLANNER_VERSION",
    "NO_COLLECTOR_IMPLEMENTED",
    "NO_NORMALIZER_IMPLEMENTED",
    # sources
    "SourceAvailability",
    "SourceAvailabilityReport",
    "SourceAvailabilityProvider",
    "UnconsultedRegistry",
    "StaticSourceAvailability",
    "RegistryDatabase",
    "RegistrySourceAvailability",
    # budget
    "COST_UNIT",
    "BudgetAccount",
    "BudgetDecision",
    "BudgetEntryKind",
    "BudgetGuard",
    "BudgetRefusedError",
    # completeness
    "CompletenessBasis",
    "CompletenessRecord",
]

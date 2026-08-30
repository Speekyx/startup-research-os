"""Compliance capabilities (Mission 1.4).

The layer between an approving review and a collector that may not exist yet.

    config.py         the obligations, as governance data rather than branches
    attribution.py    what attribution follows the data, and how it survives
    resources.py      which resources the approval actually covers
    credentials.py    whether a key is configured, never what it is
    capabilities.py   named capabilities, and the checks that make them real
    verification.py   running a verifier against a Mission 1.3 condition
    authorization.py  what a collector must hold before it may run
    readiness.py      the four separate facts, derived and never stored
    repositories.py   persisting a verification, and syncing the gate's boolean

**Nothing here grants anything.** Every rule is a restriction, every default is
the strict one, and a source, resource or element that was never established is
refused rather than assumed. The one thing that can move a condition from
unsatisfied to satisfied is a verifier that says what it checked and why, and
the database refuses the boolean without one.

**No collector, and no network.** This package governs acquisition and performs
none; CI asserts that it imports no HTTP client, browser driver or socket.
"""

from .attribution import (
    AttributedArtifact,
    AttributionFacts,
    AttributionIncompleteError,
    AttributionNotice,
    render_attribution,
)
from .authorization import (
    AcquisitionAuthorizationContext,
    AcquisitionNotAuthorizedError,
    AuthorizedAccess,
    RateLimit,
    build_authorization,
)
from .capabilities import CAPABILITIES, ComplianceCapability, capability, capability_failures
from .config import (
    DEFAULT_COMPLIANCE_PATH,
    AccessRestriction,
    AcquisitionBounds,
    AttributionObligation,
    AttributionRequirement,
    AuthorizedDataset,
    ComplianceConfig,
    DataMinimisationProfile,
    EnumeratedExclusion,
    ResourceScope,
    SourceCompliance,
    find_compliance_config,
    load_compliance,
)
from .credentials import CONFIGURED, NOT_CONFIGURED, CredentialStatus, credential_status
from .readiness import AcquisitionReadiness, evaluate_readiness
from .resources import ResourceAuthorization, ResourceDescriptor, authorize_resource
from .verification import (
    RUNTIME_VERIFICATIONS,
    VERIFIER_VERSION,
    ConditionVerificationRecord,
    design_eligible,
    satisfied_condition_keys,
    verify_condition,
    verify_source,
)

__all__ = [
    "CAPABILITIES",
    "CONFIGURED",
    "DEFAULT_COMPLIANCE_PATH",
    "NOT_CONFIGURED",
    "RUNTIME_VERIFICATIONS",
    "VERIFIER_VERSION",
    "AccessRestriction",
    "AcquisitionAuthorizationContext",
    "AcquisitionBounds",
    "AcquisitionNotAuthorizedError",
    "AcquisitionReadiness",
    "AttributedArtifact",
    "AttributionFacts",
    "AttributionIncompleteError",
    "AttributionNotice",
    "AttributionObligation",
    "AttributionRequirement",
    "AuthorizedAccess",
    "AuthorizedDataset",
    "ComplianceCapability",
    "ComplianceConfig",
    "ConditionVerificationRecord",
    "CredentialStatus",
    "DataMinimisationProfile",
    "EnumeratedExclusion",
    "RateLimit",
    "ResourceAuthorization",
    "ResourceDescriptor",
    "ResourceScope",
    "SourceCompliance",
    "authorize_resource",
    "build_authorization",
    "capability",
    "capability_failures",
    "credential_status",
    "design_eligible",
    "evaluate_readiness",
    "find_compliance_config",
    "load_compliance",
    "render_attribution",
    "satisfied_condition_keys",
    "verify_condition",
    "verify_source",
]

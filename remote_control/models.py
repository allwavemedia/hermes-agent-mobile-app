"""Framework-neutral remote-control protocol result models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One stable, serializable JSON Schema validation issue."""

    instance_path: str
    keyword: str
    message: str
    schema_path: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """The result of validating one untrusted protocol document."""

    valid: bool
    errors: tuple[ValidationIssue, ...]

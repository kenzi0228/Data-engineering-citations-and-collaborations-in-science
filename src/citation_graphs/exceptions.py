from __future__ import annotations


class PipelineError(Exception):
    """Base exception for pipeline-level errors."""


class MissingInputError(PipelineError):
    """Raised when an expected input file or directory does not exist."""


class ResourceAlreadyExistsError(PipelineError):
    """Raised when a target resource already exists and overwrite is disabled."""


class InvalidConfigurationError(PipelineError):
    """Raised when provided parameters are inconsistent or invalid."""

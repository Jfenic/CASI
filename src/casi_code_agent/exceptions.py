"""Project-specific exception hierarchy for casi_code_agent."""


class CasiError(Exception):
    """Base class for controlled casi_code_agent errors."""


class RepositoryError(CasiError):
    """Raised when a repository cannot be opened or analyzed safely."""


class SecurityError(CasiError):
    """Raised when an operation is blocked by security policy."""


class FileProcessingError(CasiError):
    """Raised during controlled file processing failures."""


class FileTooLargeError(FileProcessingError):
    """Raised when a file exceeds the allowed size limit."""


class BinaryFileError(FileProcessingError):
    """Raised when a file cannot be processed as text."""
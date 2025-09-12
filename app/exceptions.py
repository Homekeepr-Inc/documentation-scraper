"""
Standardized exception classes for the Home Equipment Manuals Corpus.
"""

class CrawlerError(Exception):
    """Base exception for crawler-related errors."""
    pass

class NetworkTimeoutError(CrawlerError):
    """Raised when network requests timeout."""
    pass

class AuthenticationError(CrawlerError):
    """Raised when authentication is required but not provided."""
    pass

class RobotsTxtBlockedError(CrawlerError):
    """Raised when robots.txt explicitly blocks crawling."""
    pass

class PDFProcessingError(CrawlerError):
    """Raised when PDF processing fails."""
    pass

class DatabaseError(CrawlerError):
    """Raised when database operations fail."""
    pass

class InvalidConfigurationError(CrawlerError):
    """Raised when configuration is invalid."""
    pass

def handle_spider_error(error: Exception, context: str = "") -> str:
    """Standardized error handling for spiders."""
    if isinstance(error, (NetworkTimeoutError, ConnectionError)):
        return f"🌐 Network timeout: {context}"
    elif isinstance(error, AuthenticationError):
        return f"🔒 Authentication required: {context}"
    elif isinstance(error, RobotsTxtBlockedError):
        return f"🚫 Robots.txt blocked: {context}"
    elif isinstance(error, PDFProcessingError):
        return f"📄 PDF processing failed: {context}"
    elif isinstance(error, DatabaseError):
        return f"💾 Database error: {context}"
    else:
        return f"❌ Unexpected error: {context} - {str(error)}"


class AccountSuspendedException(Exception):
    """Exception raised when an account gets suspended."""


class AccountLockedException(Exception):
    """Exception raised when an account gets locked."""


class RegionException(Exception):
    """Exception raised when Microsoft Rewards not available in a region."""
    
    
class UnusualActivityException(Exception):
    """Exception raised when Microsoft returns unusual activity detected"""
    
    
class ProxyIsDeadException(Exception):
    """Exception raised when proxy is dead to skip the account"""


class TOTPInvalidException(Exception):
    """Exception raised when the TOTP code is wrong"""
    
    
class InvalidCredentialsException(Exception):
    """Exception raised when the email is invalid"""
    
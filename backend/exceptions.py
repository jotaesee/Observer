class VersionNotFoundError(Exception):
    """Exception raised when looking for a nonexisting minecraft version"""
    pass

class NoConnectionToInternetError(Exception):
    """Exception raised when trying to get a response, but no internet connection is available."""
    pass

class DownloadCorruptedError(Exception):
    """Exception raised when the verify download proccess has failed"""
    pass
    
class RetriesFailedError(Exception):
    """All tries for downloading the jar have failed."""
    pass

class NetworkError(Exception):
    """Exception for all network related problems !!"""
    pass

class ExternalApiError(Exception):
    """Exception for all external api's errors"""
    pass

class InstanceNotFoundError(Exception):
    """Exception raised when searching an instance by id and it can't be found."""
    pass

class PortInUseError(Exception):
    """Exception raised when desired port for process is already being used. """
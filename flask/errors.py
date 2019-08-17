"""
Application-specific errors
"""
class AppError(Exception):
    msg = ""
    def __str__(self):
        s = "Fatal error: \n" + self.msg + super(AppError, self).__str__()
        return s

class InvalidIndexPayload(AppError):
    msg = "Invalid payload for POST request at index endpoint"

class IndexerError(AppError):
    msg = ""

class ExcerptError(AppError):
    msg = "Failed to generate excerpt"

class DatabasesOutOfSyncError(AppError):
    msg = "The flask database and bolt database are out of sync."

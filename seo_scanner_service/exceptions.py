class AppError(Exception):
    pass


class WritingError(AppError):
    pass


class ReadingError(AppError):
    pass

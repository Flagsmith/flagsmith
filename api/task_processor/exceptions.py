class TaskProcessingError(Exception):
    pass


class InvalidArgumentsError(TaskProcessingError):
    pass


class TaskQueueFullError(Exception):
    pass

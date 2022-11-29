class PipedriveError(Exception):
    pass


class PipedriveAPIError(PipedriveError):
    pass


class MultipleMatchingOrganizationsError(PipedriveError):
    pass


class EntityNotFoundError(PipedriveError):
    pass

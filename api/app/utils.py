import shortuuid


def create_hash() -> str:
    """Helper function to create a short hash"""
    return shortuuid.uuid()

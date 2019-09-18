# Feature State Value Types
INTEGER = "int"
STRING = "unicode"
BOOLEAN = "bool"


def get_value_type(value):
    if is_integer(value):
        return INTEGER
    elif is_boolean(value):
        return BOOLEAN
    else:
        return STRING


def is_integer(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def is_boolean(value):
    return value in ('true', 'True', 'false', 'False')


def get_integer_from_string(value):
    try:
        return int(value)
    except ValueError:
        return 0


def get_boolean_from_string(value):
    if value in ('false', 'False'):
        return False
    else:
        return True

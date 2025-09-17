import re

from django.core.validators import RegexValidator

RE_VALID_IDENTIFIER = re.compile(r"^[\w !#$%&*+/=?^_`{}|~@.\-]+$")

identifier_regex_validator = RegexValidator(
    regex=RE_VALID_IDENTIFIER,
    message="Identifier can only contain unicode letters, numbers, spaces and the symbols: ! # $ %% & * + / = ? ^ _ ` { } | ~ @ . -",
)

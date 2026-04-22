from integrations.gitlab.services.url_parsing import parse_project_path


def test_parse_project_path__empty_input__returns_none() -> None:
    # Given / When
    none_result = parse_project_path(None)
    empty_result = parse_project_path("")

    # Then
    assert none_result is None
    assert empty_result is None

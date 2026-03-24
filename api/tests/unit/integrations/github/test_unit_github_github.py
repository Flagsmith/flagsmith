from integrations.github.github import tag_feature_per_github_event


def test_tag_feature_per_github_event__empty_feature__returns_none(db: None) -> None:
    # Given / When
    result = tag_feature_per_github_event(  # type: ignore[func-returns-value]
        event_type="test",
        action="closed",
        metadata={},
        repo_full_name="test/repo",
    )

    # Then
    assert result is None

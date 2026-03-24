def gitlab_webhook_payload_is_valid(
    secret_token: str, gitlab_token_header: str | None,
) -> bool:
    """Verify that the webhook was sent from GitLab by comparing the secret token."""
    if not gitlab_token_header:
        return False
    return secret_token == gitlab_token_header

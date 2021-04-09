def get_example_telemetry_data(
    organisations: int = 1,
    projects: int = 1,
    environments: int = 1,
    features: int = 1,
    segments: int = 1,
    users: int = 1,
    debug_enabled: bool = True,
    env: str = "test",
):
    return {
        "organisations": organisations,
        "projects": projects,
        "environments": environments,
        "features": features,
        "segments": segments,
        "users": users,
        "debug_enabled": debug_enabled,
        "env": env,
    }

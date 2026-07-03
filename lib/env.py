import os


def require_env(name: str) -> str:
    """Return the named environment variable, raising a clear error if it's unset or empty."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value

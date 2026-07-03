import typing

import pydantic

__all__ = ["Aliased"]


def Aliased(
    alias: str | None = None,
    default: typing.Any = ...,
    **kwargs: typing.Any,
) -> typing.Any:
    """Create an aliased field."""
    return pydantic.Field(default, alias=alias, **kwargs)

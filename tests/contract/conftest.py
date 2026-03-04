"""Contract test helpers for response shape validation."""

from pydantic import BaseModel, ValidationError


def assert_matches_schema(data: dict, schema_class: type[BaseModel]) -> None:
    """Validate a dict against a Pydantic model. Fails with details on error."""
    try:
        schema_class.model_validate(data)
    except ValidationError as e:
        raise AssertionError(
            f"Data does not match {schema_class.__name__}:\n{e}"
        ) from e


def assert_list_matches_schema(data: list, schema_class: type[BaseModel]) -> None:
    """Validate each item in a list against a Pydantic model."""
    assert isinstance(data, list), f"Expected list, got {type(data).__name__}"
    for i, item in enumerate(data):
        try:
            schema_class.model_validate(item)
        except ValidationError as e:
            raise AssertionError(
                f"Item {i} does not match {schema_class.__name__}:\n{e}"
            ) from e


def assert_error_response(response, expected_status: int) -> None:
    """Check that a response has the expected status and a 'detail' key."""
    assert response.status_code == expected_status, (
        f"Expected {expected_status}, got {response.status_code}"
    )
    data = response.json()
    assert "detail" in data, f"Expected 'detail' key in error response, got: {data}"

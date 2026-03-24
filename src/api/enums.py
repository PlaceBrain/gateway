from fastapi import HTTPException

# --- Places ---

ROLE_MAP = {0: "unspecified", 1: "owner", 2: "admin", 3: "viewer"}
ROLE_REVERSE = {"owner": 1, "admin": 2, "viewer": 3}

# --- Devices ---

STATUS_MAP = {0: "unspecified", 1: "online", 2: "offline"}
VALUE_TYPE_MAP = {0: "unspecified", 1: "number", 2: "boolean", 3: "enum"}
VALUE_TYPE_REVERSE = {"number": 1, "boolean": 2, "enum": 3}
THRESHOLD_TYPE_MAP = {0: "unspecified", 1: "min", 2: "max"}
THRESHOLD_TYPE_REVERSE = {"min": 1, "max": 2}
SEVERITY_MAP = {0: "unspecified", 1: "warning", 2: "critical"}
SEVERITY_REVERSE = {"warning": 1, "critical": 2}


def resolve_enum(mapping: dict[str, int], value: str, field_name: str) -> int:
    result = mapping.get(value)
    if result is None:
        allowed = ", ".join(mapping.keys())
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field_name}: '{value}'. Allowed: {allowed}",
        )
    return result

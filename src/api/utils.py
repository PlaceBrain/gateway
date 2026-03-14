from fastapi import FastAPI


def generate_openapi_file(app: FastAPI) -> None:
    import json

    from src.core.config import BASE_DIR

    try:
        output_path = BASE_DIR / "var" / "app" / "openapi.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(app.openapi(), f, indent=2)

        print(f"OpenAPI JSON generated at {output_path}")
    except Exception as e:
        print(f"Failed to generate OpenAPI file: {e}")

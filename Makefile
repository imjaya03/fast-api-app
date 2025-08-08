.PHONY: install dev start lint format test clean build

# Install all dependencies (main + dev)
install:
	uv sync

# Run development server with auto-reload
dev:
	uv run uvicorn main:app --reload

# Run production server
start:
	uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Lint code using ruff (install via: uv add ruff --dev)
lint:
	uv run ruff check .

# Format code using ruff (install via: uv add ruff --dev)
format:
	uv run ruff format .

# Run tests (using pytest or any framework you use)
test:
	uv run pytest

# Clean __pycache__, .pytest_cache, etc
clean:
	find . -type d -name "__pycache__" -exec rm -r {} + || true
	rm -rf .pytest_cache

# Build dist (if you package the app)
build:
	uv run python -m build

lint:
	uv run isort app
	uv run black app
	uv run ruff check app
	uv run flake8 app

test:
	uv run pytest

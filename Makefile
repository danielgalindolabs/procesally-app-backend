lint:
	uv run isort app
	uv run black app
	uv run ruff check app
	uv run flake8 app

test:
	uv run pytest

parse-reset:
	./scripts/dev_parsing_reset.sh

parse-up:
	docker compose up --build

parse-down:
	docker compose down -v

parse-analysis:
	uv run python scripts/build_legal_parser_dataset.py --laws-dir leyes --output-dir leyes/analysis --windows-per-file 40 --sample-files-target 60

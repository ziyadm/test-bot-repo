there_is_no_default_target:
	@echo "there is no default target, look at the makefile to see what targets you can build"
	@exit 1


flake_line_too_long_error_code = E501
flake_line_break_before_binary_operator_error_code = W503


setup: ../.env
	python3 -m pip install poetry
	python3 -m pip install black
	python3 -m pip install flake8
	python3 -m pip install isort
	ln ../.env ./.env


build: pyproject.toml
	python3 -m poetry lock --no-update
	python3 -m poetry install


clean:
	rm -rf __pycache__
	rm poetry.lock


format:
	black .
	isort .
	flake8 \
	  --max-line-length=88 \
	  --ignore=${flake_line_too_long_error_code},${flake_line_break_before_binary_operator_error_code} \
	  $(pwd)


discord_client: build main.py
	python3 -m poetry run python3 main.py

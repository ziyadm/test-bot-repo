there_is_no_default_target:
	@echo "there is no default target, look at the makefile to see what targets you can build"
	@exit 1


###### project setup and building ######


setup: ../.env
	python3 -m pip install poetry
	python3 -m pip install black
	python3 -m pip install isort
	if [[ ! -f ".env" ]]; then \
	  ln ../.env ./.env; \
	fi


build: pyproject.toml
	python3 -m poetry lock --no-update
	python3 -m poetry install


clean:
	rm -rf __pycache__
	rm poetry.lock


format:
	black .
	isort .


###### run apps ######


discord_client: build main.py
	python3 -m poetry run python3 main.py


###### git helpers ######


branch:
	git checkout -b $(shell bash -c 'read branch_name')
	git push --set-upstream origin ${branch_name}


push: format
	git commit -am "_"
	git push

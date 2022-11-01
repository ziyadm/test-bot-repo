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


clean: __pycache__ poetry.lock
	rm -rf __pycache__
	rm poetry.lock


format:
	isort .
	black .


###### run apps ######


discord_client: build main.py
	python3 -m poetry run python3 main.py


###### git helpers ######


feature:
	@read -p "feature name (eg make-bot-do-thing): " feature_name; \
  echo ${feature_name}
	# \
	# git checkout main; \
	# git pull; \
	# \
	# git checkout -b ${feature_name}; \
	# git push --set-upstream origin ${feature_name}


push: format
	git add .
	git commit -am "_"
	git push

there_is_no_default_target:
	@echo "there is no default target, look at the makefile to see what targets you can build"
	@exit 1


###### project setup and building ######

setup_no_env: 
	python3 -m pip install poetry
	python3 -m pip install black
	python3 -m pip install isort
	python3 -m pip install requests

setup: ../.env
	python3 -m pip install poetry
	python3 -m pip install black
	python3 -m pip install isort
	if [[ ! -f ".env" ]]; then \
	  ln ../.env ./.env; \
	fi

env:
	echo "airtable_api_key=${airtable_api_key}" > .env
	echo "airtable_database_id=${airtable_database_id}" >> .env
	echo "discord_guild_id=${discord_guild_id}" >> .env
	echo "discord_secret_token=${discord_secret_token}" >> .env
	echo "discord_review_channel_id=${discord_review_channel_id}" >> .env

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


discord_bot: build discord_bot.py
	python3 -m poetry run python3 discord_bot.py


upload_leetcode_questions_to_airtable: build upload_leetcode_questions_to_airtable.py
	python3 -m poetry run python3 upload_leetcode_questions_to_airtable.py


###### git helpers ######


feature:
	@read -p "feature name (eg make-bot-do-thing): " feature_name; \
	\
	git checkout main; \
	git pull; \
	\
	git checkout -b $${feature_name}; \
	git push --set-upstream origin $${feature_name}


push: format
	git add .
	git commit -am "_" --allow-empty
	git push


release: push
	gh pr create --base main --title "$(shell git branch --show-current)" --body "_"

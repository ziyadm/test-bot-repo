# Discord bot for SWE interview prep


## How to set up local environment
create a [.env] file one level up from where this [README.md] file is and fill it with the required secrets

./setup.sh


## How to run locally
./build.sh


## Airtable

* https://airtable.com/app8xDpApplv8WrVJ/tblq9OP7XbjDidPZC/viwuD5OT73LN5yaEg?blocks=hide
* one base named "interview" (analogous to a database)
* one table name "interview" (analogous to a table in a database)
* has two columns (name/message)

## Discord

* server here: https://discord.gg/Qbm4mgSr
* has a bot called "interview"
* this bot is backed by a python file (in this directory) that is deployed on replit (runs a mini python process for us)

## TODOs

* TODO: figure out if we can limit commands to specific roles/channels
* TODO: turn off all messages
* TODO: make one channel for general chat
* TODO ziyadm: reviewing flow
* claiming a review flow
	** go to thread for the review notification
	** /claim will lock that for the reviewer
	** make a new channel for -review (copies over the state from code_review / design_review, copies question link)
* lgtm flow
	** last message is review content
	** /lgtm command has a single param for the score
	** close / delete channel / cleanup
	** summarize in player's home channel in a thread/message
* scoring/evolving module
	** if the score sends you to the next rank, update ranks

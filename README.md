# Discord bot for SWE interview prep


## How to set up local environment
create a [.env] file one level up from where this [README.md] file is and fill it with the required secrets

./setup.sh


## How to run locally
./build.sh


## Links

airtable: https://airtable.com/app8xDpApplv8WrVJ/tblq9OP7XbjDidPZC/viwuD5OT73LN5yaEg?blocks=hide
discord: https://discord.gg/Qbm4mgSr


## TODOs

TODO: send reviewer the question link when they claim a question for review

TODO ziyadm: evolution

TODO: have suriels spren explain how to do a mission at the start of every mission channel

TODO: create a thread in the player's path channel for every mission they have done / are actively doing. update this thread whenever the status changes

TODO: only allow commands to be run by the right set of users

TODO: only allow commands to be run in channels that makes sense:
* all review related commands happen in review channels only
* claiming review happens only in the main review channel
* /train works only in path channel
* /submit works only in mission channel

TODO: create one general chat that all users can chat in

TODO: only allow users to send messages in mission channels

TODO: /stats command for players to see all their stats
* how many questions
* progress in evolution

TODO: update all text / command names to fit one theme:
* seems like we want some sort of mission/quest based theme

TODO: time limit for player to submit a mission stage
* 1 hour per stage, we send our solution for that stage if time runs out

TODO: time limit for someone to have claimed an unclaimed question
* 5 minutes

TODO: time limit for reviewers to review a claimed question
* 25 minutes per stage

TODO: tell player to do another training mission while they wait for feedback

TODO: idle state player goes offline
* pause mission timers

TODO: when player goes online, send some sort of message or do something to get them back in the groove
* remind them of what they were doing and where they were at

TODO: update time spent with suriels spren typing (when sending player instructions) to a realistic value

TODO: refactor immutable updates logic into an [Immutable_dict] module

TODO: sync roles from ranks

TODO: handle case when there are no more questions gracefully

TODO: replace instances of "Suriel" with the actual suriel username in discord

TODO: update review channel names to be unique, the current implementation will use the same name every time a question is asked

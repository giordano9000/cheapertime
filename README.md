# cheapertimebot

**DESCRIPTION**
\
\
Simple bot for telegram to insert timesheet in an integrated system.\
The bot can receive written and vocal messages.
The message format is:\
\
`<project_name> <minutes> <description>`\
\
The bot will check if the project exists and if the minutes are valid,\
it will also check if the user is authorized to insert timesheet for the project.\
Therefore if the user is authorized, insert the timesheet in the system.

**CONFIGURATION**
\
Rename the file 'app.conf_example' to 'app.conf' and fill the fields with the correct values.\
In the authorized_users.json file, insert the telegram id of the users authorized to insert timesheet, 
and associate it with the id of that users within the integrated system.

**COMMANDS**
\
\
**To pass to BotFather**\
\
get_my_telegram_id - Get your personal Telegram ID\
get_projects_list - Get the list of available projects

**TEST**
\
\
set webhook: https://api.telegram.org/bot{bot_token}/setWebhook?url={ngrok_temp_url_port_5500}/{bot_token}

url webhook for production: https://api.telegram.org/bot{bot_token}/setWebhook?url=cheapertime.domain.com/{bot_token}
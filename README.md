> [!WARNING]
> As of September 2024, since Deta Space is being [sunset](https://web.archive.org/web/20240902151210/https://deta.space/sunset) this repository (as well as any other projects based on deta-discord-interactions) may stop working.
>
> I have yet to decide whenever I will update it or Archive the repository.

# Deta-Utils-Bot
A serverless discord bot made with [deta-discord-interactions](https://github.com/etrotta/deta-discord-interactions) for simple utility features.

# Installing
Install it in [Deta Space](https://deta.space/discovery/@etrotta/utilsbot)
You have to create an App in https://discord.com/developers/applications and store following:
- (General Information tab) Application ID 
  (same as the OAuth2 tab Client ID)
- (General Information tab) Public Key
- (OAuth2 tab) Client Secret

Set their respective Environment Variables in the Space App Settings
After setting them, you have to go back to the Application page and set the `Interactions Endpoint Url` to the `/discord` route of your app, as in `https://example.deta.app/discord`
(copy paste the URL and manually include the `/discord` part)

You can manage Notes and Tags by using the "see data" option in Space.
This does means that the bot's admin is able to see all users' notes. Make sure to instruct them not to store sensitive information there.

# Running locally
Whatever works for you. I personally go with something like:
```
py -m venv .venv
./.venv/scripts/activate
cd bot
pip install -e .
cd ..
pip install pytest
# Create a ".env" file in the `bot/` directory similar to the ".env.example" example in the repository root
py bot/run_local.py
```
I do the vast majority of the development and debugging using tests, since creating fake HTTP requests for the commands would be painful and `space push` takes ages.

# Considerations
- There are no measures in place to prevent users from creating and sharing spam, abusive content or even illegal content. As such, I removed the option to make `/notes` results non-ephemeral.

# Credits
- icon made by dalle2 then cropped

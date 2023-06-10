---
app_name: "Discord Utils Bot"
tagline: "A discord bot with some utility features"
git: "https://github.com/etrotta/deta-utils-discord-bot"
homepage: "https://github.com/etrotta/deta-utils-discord-bot"
---

Mostly created as an example of how to use my [Interactions](https://github.com/etrotta/deta-discord-interactions) library, this bot features some utility features and can be installed and used as-is.
## Features:
- Opt-in / Opt-out of each feature via Environment Variables
- Allow for users to create and store individual Notes
- Create and manage global Tags users can access, while restricting who can edit them

## Setting up the bot:
This is essentially a self-hosted bot. You need to create a Bot application and point it to your instance.
- Create an App in https://discord.com/developers/applications and store following:
- - (General Information tab) Application ID 
  (= OAuth2 tab Client ID)
- - (General Information tab) Public Key
- - (OAuth2 tab) Client Secret

Set their respective `Environment Variables` in the `Space App Settings`.

After setting them, you have to go back to the Discord Developers Application page and set the `Interactions Endpoint Url` to the `/discord` route of your app, as in `https://example.deta.app/discord`
(copy/paste the URL and manually include the `/discord` part)

You can manage Notes and Tags by using the "see data" option in Space.
This does means that the bot's admin (the user who installed the app, ***not*** the bot's developer) is able to see all users' notes. Make sure to instruct them not to store sensitive information there.

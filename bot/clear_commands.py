import os
import pathlib
from deta_discord_interactions import DiscordInteractions

# You might want to consider using python-dotenv instead
env = pathlib.Path(__file__).parent / '.env'
if env.is_file():
    with env.open('r') as file:
        for line in file:
            try:
                k, v = line.strip().split("=")
                os.environ[k] = v
            except Exception:
                pass

from utilsbot.main import update_commands

guilds = os.getenv("GUILDS")
if guilds:
    guilds = guilds.split("&")
# assert guilds, "Avoid using global commands while developing"
blank_app = DiscordInteractions()
update_commands(blank_app, micro=False, guilds=guilds)

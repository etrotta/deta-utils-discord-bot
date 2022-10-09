import os

# use python-dotenv for local developing only. Use `deta update -e` for updating the micro's env variables
try:
    from dotenv import load_dotenv
    load_dotenv("local.env")
    load_dotenv(".env")
    print("Loaded .env file")
except ImportError:
    pass


from deta_discord_interactions import DiscordInteractions

# If you want to use Webhooks / Discord OAuth:
# from deta_discord_interactions.utils.oauth import enable_oauth

from blueprints.faq import blueprint as faq_bp
from blueprints.notes import blueprint as notes_bp
from blueprints.tags import blueprint as tags_bp



app = DiscordInteractions()
# enable_oauth(app)

# app.update_commands()

app.register_blueprint(faq_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(tags_bp)


# # If you do not want to install the library localy:
# @app.route('/update_commands')
# def home(request, start_response, abort):
#     app.update_commands(from_inside_a_micro=True)
#     start_response('200 OK', [])
#     return ['updated commands'.encode('UTF-8')]


if __name__ == '__main__':
    print("Updating commands")
    guilds = os.getenv("GUILDS")
    print(guilds)
    if guilds:
        for guild in guilds.split("&"):
            print(f"Updating commands for guild {guild}")
            app.update_commands(guild_id=guild)
    else:
        app.update_commands()

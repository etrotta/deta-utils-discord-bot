import os
import pathlib
from typing import Optional
from deta_discord_interactions import DiscordInteractions

# If you want to use Webhooks / Discord OAuth:
# from deta_discord_interactions.utils.oauth import enable_oauth

app = DiscordInteractions()

if int(os.getenv("NOTES_SETTINGS")) & 1:
    from utilsbot.blueprints.notes import blueprint as notes_bp
    app.register_blueprint(notes_bp)

if int(os.getenv("TAGS_SETTINGS")) & 1:
    from utilsbot.blueprints.tags import public_blueprint as public_tags_bp
    app.register_blueprint(public_tags_bp)

if int(os.getenv("TAGS_SETTINGS")) & 2:
    from utilsbot.blueprints.tags import admin_blueprint as manage_tags_bp
    app.register_blueprint(manage_tags_bp)


# enable_oauth(app)

def update_commands(app_: DiscordInteractions, micro: bool, guilds: Optional[list[str]]):
    if guilds:
        for guild in guilds:
            print(f"Updating commands for guild {guild}")
            app_.update_commands(guild_id=guild, from_inside_a_micro=micro)
    else:
        print(f"Updating global commands")
        app_.update_commands(from_inside_a_micro=micro)


@app.route('/setup')
def setup_stuff(request, start_response, abort):
    guilds = os.getenv("GUILDS")
    if guilds is not None:
        guilds = guilds.split("&")
        msg = f"Updated commands for {guilds=}."
    else:
        msg = f"Updated commands globally."
    update_commands(app, micro=True, guilds=guilds)

    if int(os.getenv("TAGS_SETTINGS")) & 4:
        from utilsbot.blueprints.tags import drive
        for tag in (pathlib.Path(__file__).parent / "default_tags").iterdir():
            print(f"Setting tag {tag.stem}")
            (drive / tag.name).put(local_file=tag)
        msg += "\nSet default tags."

    start_response('200 OK', [])
    return [msg.encode('UTF-8')]


@app.route('/clear')
def clear_commands(request, start_response, abort):
    blank_app = DiscordInteractions()
    # ...think of it like unregistering the blueprints but more drastical
    update_commands(blank_app, micro=True)
    start_response('200 OK', [])
    return [f'Deleted all commands for current GUILDS environment variable'.encode('UTF-8')]


@app.route('/')
def check_bot(request, start_response, abort):
    from deta_discord_interactions.utils.oauth import OAuthToken
    token = OAuthToken.from_client_credentials()
    application = token.get_auth_data().application
    start_response('200 OK', [])
    return [f'Registered as {application.name}, ID {application.id}'.encode('UTF-8')]

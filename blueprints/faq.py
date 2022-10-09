from deta_discord_interactions import DiscordInteractionsBlueprint
from deta_discord_interactions import Context, Option, Choice
from deta_discord_interactions import Message
from deta_discord_interactions import Embed

BOT_COLOR = 0xbb3892


info = Embed(
    title="Bot Information",
    description="Utility discord interactions bot, written in Python and hosted on Deta."
    " Relevant links:"
    " [Source code on GitHub](https://github.com/etrotta/deta-utils-discord-bot),"
    " [Library on GitHub](https://github.com/etrotta/deta-discord-interactions),"
    " [Library on pypi](https://pypi.org/project/deta-discord-interactions/)",
    color=BOT_COLOR,
)


notes = """Create, Read, Update, Delete and List personal notes.
**Do not store any kind of sensitive or inappropriate information.
The bot's owner can see your notes.**"""


messages = {
    "help": Message(
        content="You are already using it!",
        ephemeral=True,
    ),
    "deta": Message(
        content="TODO improve this message",
        ephemeral=True,
    ),
    "community_resources": Message(
        content="TODO improve this message",
        ephemeral=True,
    ),
    "serverless": Message(
        content="TODO improve this message",
        ephemeral=True,
    ),
    "bot_info": Message(
        embed=info,
        ephemeral=True,
    ),
    "notes_commands": Message(
        content=notes,
        ephemeral=True,
    ),
}


blueprint = DiscordInteractionsBlueprint()

@blueprint.command(
    "faq",
    "Information about Deta and this Bot",
    options=[
        Option(
            name="question",
            type=str,
            description="Topic to get help about",
            required=True,
            choices=[
                Choice(k, k)
                for k in messages.keys()
            ]
        )
    ],
)
def get_help(ctx: Context, question: str):
    return messages[question]

import os
import json
import functools

from deta_discord_interactions import (
    DiscordInteractionsBlueprint,
    Context,

    Message,
    Modal,

    ActionRow,
    TextInput,
    TextStyles,

    SelectMenu,
    SelectMenuOption,

    Autocomplete,
    Option,
    Choice,
)
from deta_discord_interactions.enums.permissions import PERMISSION

from deta_discord_interactions.utils.database import Drive

drive = Drive("discord_tags")

public_blueprint = DiscordInteractionsBlueprint()
admin_blueprint = DiscordInteractionsBlueprint()

ENV_SETTINGS = int(os.environ["TAGS_SETTINGS"])
READ_ENABLED = ENV_SETTINGS & 1
MANAGE_ENABLED = ENV_SETTINGS & 2

manage_group = admin_blueprint.command_group(
    "managetags",
    "Create, Update and Delete bot tags.",
    dm_permission=False,
    default_member_permissions=PERMISSION.ADMINISTRATOR,
)


def requires_read(foo):
    @functools.wraps(foo)
    def wrapper(*args, **kwargs):
        if READ_ENABLED:
            return foo(*args, **kwargs)
        return Message(
            "The Tags module has been disabled.\n"
            "You may want to contact the bot administrator to remove the permissions "
            "to use the tag related commands or completely remove them.",
            ephemeral=True
        )
    return wrapper


def requires_management(foo):
    @functools.wraps(foo)
    def wrapper(*args, **kwargs):
        if MANAGE_ENABLED:
            return foo(*args, **kwargs)
        elif READ_ENABLED:
            return Message(
                f"The Tags module has been limited to read-only.\n"
                "You may want to contact the bot administrator to remove the permissions "
                "to use the tag management commands or completely remove them.\n"
                "The bot's administrator can still manage tags via their Deta Drive.",
                ephemeral=True,
            )
        else:
            return Message(
                f"The Tags module has been disabled.\n"
                "You may want to contact the bot administrator to remove the permissions "
                "to use the related commands or completely remove them",
                ephemeral=True,
            )
    return wrapper


# Modal to create / edit
def modal(name: str, description: str) -> Modal:
    return Modal(
        "tags_modal",
        "Create or edit a Tag",
        [
            ActionRow(
                [TextInput("tag_name", "Name", value=name)],
            ),
            ActionRow(
                [TextInput("tag_body", "Body", style=TextStyles.PARAGRAPH, value=description)],
            ),
        ]
    )


@admin_blueprint.custom_handler("tags_modal")
@requires_management
def save_modal_tag(ctx: Context):
    name = ctx.get_component("tag_name").value
    description = ctx.get_component("tag_body").value.strip()

    if not description.startswith("{"):
        description = json.dumps({"content": description})

    try:
        Message.from_dict(json.loads(description)).encode()
    except Exception as err:
        return Message(f"Aborted operation - body content validation raised an error: ```\n{err}```", ephemeral=True)

    (drive / f'{name}.json').write_text(description)

    return Message(f"Set tag {name}", ephemeral=True)


# Create / Update - Admin only
@manage_group.command("manage", "Add or edit a bot tag.")
@requires_management
def manage_tag(ctx: Context, name: Autocomplete[str]):
    body = (drive / f'{name}.json').read_text()  # Returns an empty string if the file was not found
    if len(body) > 4000:
        return Message("This tag's body is too large to edit via Discord!", ephemeral=True)
    return modal(name, body)


# Read - Public
@public_blueprint.command("tag", "Retrieve a bot tag.")
@requires_read
def get_tag(ctx: Context, name: Autocomplete[str]):
    tag = (drive / f'{name}.json').read_text()
    if not tag:
        return Message("Tag not found.", ephemeral=True)
    try:
        msg = json.loads(tag)
        return Message.from_dict(msg)
    except Exception:
        import traceback
        traceback.print_exc()
        return Message("Failed to load the tag", ephemeral=True)


# Delete - Admin only
@manage_group.command("delete", "Delete a bot tag.")
@requires_management
def delete_tag(ctx: Context, name: Autocomplete[str]):
    (drive / f'{name}.json').delete()
    return Message(f"Tag {name} deleted (or already didn't exist)", ephemeral=True)


# List - Public
@public_blueprint.command("tags", "List all tags from this bot")
@requires_read
def list_tags(ctx: Context, ephemeral: bool = False):
    bot_tags = [path.stem for path in drive.iterdir()]
    if not bot_tags:
        return Message("There are no tags.", ephemeral=ephemeral)

    # If it fits in a Select Menu
    if len(bot_tags) <= 25:
        options = [SelectMenuOption(name, name) for name in bot_tags]
        return Message(
            "Select a tag to see it:",
            components=[ActionRow([SelectMenu("tags_list", options)])],
            ephemeral=ephemeral,
        )
    else:
        # Put in a normal message.
        result = "```\n" + ", ".join(bot_tags) + "```"
        return Message(result, ephemeral=ephemeral, allowed_mentions={"parse": []})


@public_blueprint.custom_handler("tags_list")
@requires_read
def show_full_tag(ctx: Context):
    name = ctx.values[0]
    tag = (drive / f"{name}.json").read_text()
    if not tag:
        return Message("Tag not found.", ephemeral=True)
    data = json.loads(tag)
    msg = Message.from_dict(data)
    if data.get("ephemeral") is None:
        msg.ephemeral = True
    return msg


@manage_tag.autocomplete()
@get_tag.autocomplete()
@delete_tag.autocomplete()
def tag_name_autocomplete_handler(ctx, name: Option = None, **_):
    if name is None or not name.focused:
        return []
    if not READ_ENABLED:
        return []
    tags = sorted(stem for path in drive.iterdir() if (stem := path.stem).startswith(name.value))
    options = [Choice(tag, tag) for tag in tags[:25]]
    return options

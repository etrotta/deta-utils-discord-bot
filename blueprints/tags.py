import json
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

from deta import Deta

deta = Deta()
drive = deta.Drive("discord_tags")

blueprint = DiscordInteractionsBlueprint()

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


@blueprint.custom_handler("tags_modal")
def save_modal_tag(ctx: Context):
    name = ctx.get_component("tag_name").value
    description = ctx.get_component("tag_body").value.strip()

    if not description.startswith("{"):
        description = json.dumps({"content": description})

    drive.put(name, description.encode("UTF-8"), content_type="text/plain")

    return Message(f"Set tag {name}", ephemeral=True)


# Create / Update - Admin only
@blueprint.command("manage", "Add or edit a bot tag.", dm_permission=False, default_member_permissions=PERMISSION.ADMINISTRATOR)
def manage_tag(ctx: Context, name: Autocomplete[str]):
    tag = drive.get(name)
    if tag is None:
        body = ""
    else:
        try:
            body = tag.read().decode("UTF-8")
        finally:
            tag.close()
    if len(body) > 4000:
        return Message("This tag's body is too large to edit via Discord!", ephemeral=True)
    return modal(name, body)

# Read - Public
@blueprint.command("tag", "Retrieve a bot tag.")
def get_tag(ctx: Context, name: Autocomplete[str]):
    tag = drive.get(name)
    if tag is None:
        return Message("Tag not found.", ephemeral=True)
    try:
        msg = json.loads(tag.read().decode("UTF-8"))
    finally:
        tag.close()
    return Message.from_dict(msg)


# Delete - Admin only
@blueprint.command("delete", "Delete an existing bot tag.", default_member_permissions=PERMISSION.ADMINISTRATOR, dm_permission=False)
def delete_tag(ctx: Context, name: Autocomplete[str]):
    drive.delete(name)
    return Message(f"Tag {name} deleted", ephemeral=True)


# List - Public
@blueprint.command("tags", "List all tags from this bot")
def list_tags(ctx: Context, ephemeral: bool = False):
    bot_tags = drive.list().get("names")
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


@blueprint.custom_handler("tags_list")
def show_full_tag(ctx: Context):
    name = ctx.values[0]
    tag = drive.get(name)
    if tag is None:
        return Message("Tag not found.", ephemeral=True)
    try:
        msg = json.loads(tag.read().decode("UTF-8"))
    finally:
        tag.close()
    msg = Message.from_dict(msg)
    msg.ephemeral = True
    return msg


@manage_tag.autocomplete()
@get_tag.autocomplete()
@delete_tag.autocomplete()
def tag_name_autocomplete_handler(ctx, name: Option = None, **_):
    if name is None or not name.focused:
        return []
    tags = drive.list(25, name.value)
    options = [Choice(tag, tag) for tag in tags.get("names", [])]
    return options

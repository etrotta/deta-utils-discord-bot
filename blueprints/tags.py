from deta_discord_interactions import (
    DiscordInteractionsBlueprint,
    Context,

    Message,
    Modal,

    ActionRow,
    TextInput,
    TextStyles,

    ApplicationCommandType,
    SelectMenu,
    SelectMenuOption,

    Autocomplete,
    Option,
    Choice,
)
from deta_discord_interactions.utils.database import Database, AutoSyncRecord
from deta_discord_interactions.enums.permissions import PERMISSION

blueprint = DiscordInteractionsBlueprint()
database = Database(name="guilds_tags", record_type=AutoSyncRecord)


tags = blueprint.command_group(
    "tags",
    "Create, Update or Delete public server wide Tags.",
    default_member_permissions=PERMISSION.MANAGE_MESSAGES,
    dm_permission=False,  # Should not really matter unless you setup an actual bot account for it
)

# Create - Moderator only
@tags.command("create", "Add a new tag to the server.")
def add_tag(ctx: Context, name: str, description: str):
    server_tags = database[ctx.guild_id].setdefault("tags", {})
    if name in server_tags:
        return Message(f"Tag {name} already exists, use `/tags update` if you want to change it", ephemeral=True)
    server_tags[name] = description
    return Message(f"Registered tag {name}", ephemeral=True)

# Read - Public
@blueprint.command("tag", "Retrieve a server tag.", dm_permission=False)
def get_tag(ctx: Context, name: Autocomplete[str], ephemeral: bool = False):
    tag = database[ctx.guild_id].setdefault("tags", {}).get(name)
    return Message(
        tag or f"Tag {name} not found",
        ephemeral=(ephemeral) and (tag is not None),
        allowed_mentions={"parse": []},  # Does not pings even if there's a @mention
    )

# Update - Moderator only
@tags.command("update", "Update an existing server Tag")
def update_tag(ctx: Context, name: Autocomplete[str], description: str):
    server_tags = database[ctx.guild_id].setdefault("tags", {})
    if name not in server_tags:
        return Message(f"Tag {name} not found. Use `/tags create` to add a new one", ephemeral=True)
    elif server_tags[name] == description:
        return Message(f"Tag {name} was already set to that", ephemeral=True)
    else:
        server_tags[name] = description
        return Message(f"Tag {name} updated", ephemeral=True)


# Delete - Moderator only
@tags.command("delete", "Delete an existing server Tag")
def delete_tag(ctx: Context, name: Autocomplete[str]):
    server_tags = database[ctx.guild_id].setdefault("tags", {})
    if name not in server_tags:
        return Message(f"Tag {name} not found", ephemeral=True)
    else:
        del server_tags[name]
        return Message(f"Tag {name} deleted", ephemeral=True)


# Alternative methods to create / update
def modal(name: str, description: str) -> Modal:
    return Modal(
        "tags_modal",
        "Create or edit a Tag",
        [
            ActionRow(
                [TextInput("tag_name", "Name", value=name)],
            ),
            ActionRow(
                [TextInput("tag_description", "Description", style=TextStyles.PARAGRAPH, value=description)],
            ),
        ]
    )


@tags.command("modal", "Opens a modal for you to add or edit a Tag.")
def tag_modal(ctx: Context, name: Autocomplete[str] = ''):
    if name:
        server_tags = database[ctx.guild_id].setdefault("tags", {})
        return modal(name, server_tags.get(name, ''))
    else:
        return modal('', '')


@blueprint.command("Save as Tag", "Save this message as a server wide Tag.", type=ApplicationCommandType.MESSAGE)
def message_to_tag(ctx: Context, message: Message):
    if len(message.content) > 4000:
        return Message("This message is too long to save as a tag!", ephemeral=True)
    return modal('', message.content)


@blueprint.custom_handler("create_tag_modal")
def save_modal_tag(ctx: Context):
    server_tags = database[ctx.guild_id].setdefault("tags", {})
    name = ctx.get_component("tag_name").value
    is_update = name in server_tags
    description = ctx.get_component("tag_description").value
    server_tags[name] = description
    if is_update:
        return Message(f"Updated tag {name}", ephemeral=True)
    else:
        return Message(f"Registered tag {name}", ephemeral=True)


# List - Public
@blueprint.command("taglist", "List all tags from this server", dm_permission=False)
def list_tags(ctx: Context, ephemeral: bool = False):
    server_tags = database[ctx.guild_id].setdefault("tags", {})

    # If it fits in a Select Menu
    if len(server_tags) <= 25:
        options = []
        for name, description in server_tags.items():
            if len(description) > 100:
                description = (description)[:97] + "..."
            options.append(
                SelectMenuOption(name, name, description),
            )
        return Message(
            "Select a tag to see it:",
            components=[ActionRow([SelectMenu("tags_list", options)])],
            ephemeral=ephemeral,
        )
    else:
        # Put in a normal message. Try to preview each tag.
        result = "\n".join(
            f"{key}: {description if len(description) <= 100 else description[:97]+'...'}"
            for key, description in server_tags.items()
        )
        if len(result) < 1950:
            result = '```' + result + '```'
        else:
            # Too large with the preview -> just send each key
            result = "```\n" + ", ".join(server_tags.keys()) + "```"
        return Message(result, ephemeral=ephemeral, allowed_mentions={"parse": []})


@blueprint.custom_handler("tags_list")
def show_full_tag(ctx: Context):
    name = ctx.values[0]
    tag = database[ctx.guild_id]["tags"].get(name)
    if tag is None:
        return Message("Tag not found. It might have been deleted?", ephemeral=True)
    return Message(
        tag,
        ephemeral=True,
    )


@get_tag.autocomplete()
@update_tag.autocomplete()
@delete_tag.autocomplete()
@tag_modal.autocomplete()
def tag_name_autocomplete_handler(ctx, name: Option = None, **_):
    if name is None or not name.focused:
        return []
    server_tags = database[ctx.guild_id].setdefault("tags", {})
    options = []
    for key, description in server_tags.items():
        if key.startswith(name.value):
            display = f"{key}: {description}"
            if len(display) > 100:
                display = display[:97] + '...'
            options.append(Choice(name=display, value=key))
            # It will visually fill in the command with the `name` if you click it, 
            # but it will send with the correct `value` even then
    options.sort(key=lambda option: option.name)
    return options[:25]

import dataclasses
import os
import io
import functools
import json
import csv

import requests

from deta_discord_interactions import (
    Attachment,
    DiscordInteractionsBlueprint,
    Context,

    Message,
    Modal,

    ActionRow,

    Button,
    ButtonStyles,

    TextInput,
    TextStyles,

    ApplicationCommandType,
    SelectMenu,
    SelectMenuOption,

    Autocomplete,
    Option,
    Choice,
)
from deta_discord_interactions.enums.context_types import CONTEXT_TYPE, INTEGRATION_TYPE
from deta_discord_interactions.utils.database import Database, LoadableDataclass

@dataclasses.dataclass
class UserRecord(LoadableDataclass):
    notes: dict[str, str] = dataclasses.field(default_factory=dict)

database = Database("user_notes", record_type=UserRecord)

blueprint = DiscordInteractionsBlueprint()

ENV_SETTINGS = int(os.environ["NOTES_SETTINGS"])
READ_ENABLED = ENV_SETTINGS & 1
MANAGE_ENABLED = ENV_SETTINGS & 2


def requires_read(foo):
    @functools.wraps(foo)
    def wrapper(*args, **kwargs):
        if READ_ENABLED:
            return foo(*args, **kwargs)
        return Message(
            "The Notes module has been disabled.\n"
            "You may want to contact the bot administrator to remove the permissions "
            "to use the command or completely remove the bot's `/notes` command.",
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
                "The Notes module has been limited to read-only.\n"
                "If the administrator has announced plans to fully terminate access to the `/notes` commands, "
                "you may want to export your existing notes using `/notes export`.",
                ephemeral=True,
            )
        else:
            return Message(
                "The Notes module has been disabled.\n"
                "You may want to contact the bot administrator to remove the permissions "
                "to use the command or completely remove the bot's `/notes` command.",
                ephemeral=True,
            )
    return wrapper


notes = blueprint.command_group(
    "notes",
    "Create, Read, Update, Delete and List personal notes. WARNING: The bots admin can see your notes.",
    integration_types=[INTEGRATION_TYPE.GUILD_INSTALL, INTEGRATION_TYPE.USER_INSTALL],
    contexts=[CONTEXT_TYPE.GUILD, CONTEXT_TYPE.BOT_DM, CONTEXT_TYPE.PRIVATE_CHANNEL],
)

# Create
@notes.command("create", "Add a new note to your collection")
@requires_management
def add_note(ctx: Context, name: str, description: str):
    user = database.get(ctx.author.id) or UserRecord()
    if name in user.notes:
        return Message(f"Note `{name}` already exists, use `/notes update` if you want to change it.", ephemeral=True)
    user.notes[name] = description
    database[ctx.author.id] = user
    return Message(f"Registered note `{name}`.", ephemeral=True)

# Read
@notes.command("get", "Retrieve a note from your collection")
@requires_read
def get_note(ctx: Context, name: Autocomplete[str]):
    user = database.get(ctx.author.id)
    if user is None or not user.notes:
        return Message("You have no notes.", ephemeral=True)
    return Message(
        user.notes.get(name, f"Note `{name}` not found."),
        ephemeral=True,
    )

# Update
@notes.command("update", "Update an existing note")
@requires_management
def update_note(ctx: Context, name: Autocomplete[str], description: str):
    user = database.get(ctx.author.id)
    if user is None or not user.notes:
        return Message("You have no notes.", ephemeral=True)
    elif name not in user.notes:
        return Message(f"Note `{name}` not found. Use `/notes create` to add a new one", ephemeral=True)
    elif user.notes[name] == description:
        return Message(f"Note `{name}` was already set to that", ephemeral=True)
    else:
        user.notes[name] = description
        database[ctx.author.id] = user
        return Message(f"Note `{name}` updated", ephemeral=True)


# Delete
@notes.command("delete", "Delete an existing note")
@requires_management
def delete_note(ctx: Context, name: Autocomplete[str]):
    user = database.get(ctx.author.id)
    if user is None or not user.notes:
        return Message("You have no notes.", ephemeral=True)
    elif name not in user.notes:
        return Message(f"Note `{name}` not found.", ephemeral=True)
    else:
        del user.notes[name]
        database[ctx.author.id] = user
        return Message(f"Note `{name}` deleted.", ephemeral=True)


# Alternative methods to create / update
@notes.command("set", "Update an existing note or create a new one")
@requires_management
def set_note(ctx: Context, name: Autocomplete[str], description: str):
    user = database.get(ctx.author.id) or UserRecord()
    if user.notes.get(name) == description:
        return Message(f"Note `{name}` was already set to that.", ephemeral=True)
    
    is_update = name in user.notes
    user.notes[name] = description
    database[ctx.author.id] = user
    if is_update:
        return Message(f"Note `{name}` updated.", ephemeral=True)
    else:
        return Message(f"Note `{name}` registered.", ephemeral=True)


def modal(name: str, description: str) -> Modal:
    return Modal(
        "notes_modal",
        "Create or edit a note",
        [
            ActionRow(
                [TextInput("note_name", "Name", value=name)],
            ),
            ActionRow(
                [TextInput("note_description", "Description", style=TextStyles.PARAGRAPH, value=description)],
            ),
        ]
    )


@notes.command("modal", "Opens a modal for you to add or edit a note.")
@requires_management
def note_modal(ctx: Context, name: Autocomplete[str] = ''):
    if name:
        user = database.get(ctx.author.id) or UserRecord()
        return modal(name, user.notes.get(name, ''))
    else:
        return modal('', '')


@blueprint.command(
    "Save as note",
    "Save this message as a personal note.",
    type=ApplicationCommandType.MESSAGE,
    integration_types=[INTEGRATION_TYPE.GUILD_INSTALL, INTEGRATION_TYPE.USER_INSTALL],
    contexts=[CONTEXT_TYPE.GUILD, CONTEXT_TYPE.BOT_DM, CONTEXT_TYPE.PRIVATE_CHANNEL],
)
@requires_management
def message_to_note(ctx: Context, message: Message):
    if not message.content:  # only embeds or only components
        return Message("Cannot save this kind of message as a note.", ephemeral=True)
    if len(message.content) > 4000:
        return Message("This message is too long to save as a note!", ephemeral=True)
    return modal('', message.content)


@blueprint.custom_handler("notes_modal")
@requires_management 
def save_modal_note(ctx: Context):
    user = database.get(ctx.author.id) or UserRecord()
    name = ctx.get_component("note_name").value
    is_update = name in user.notes
    description = ctx.get_component("note_description").value
    user.notes[name] = description
    database[ctx.author.id] = user
    if is_update:
        return Message(f"Updated note {name}", ephemeral=True)
    else:
        return Message(f"Registered note {name}", ephemeral=True)


# List
@notes.command("list", "List all notes from your collection")
@requires_read
def list_notes(ctx: Context):
    user = database.get(ctx.author.id) or UserRecord()
    if not user.notes:
        return Message("You have no notes.", ephemeral=True)

    # If it fits in a Select Menu
    if len(user.notes) <= 25:
        options = []
        for name, description in user.notes.items():
            if len(description) > 100:
                description = (description)[:97] + "..."
            options.append(
                SelectMenuOption(name, name, description),
            )
        return Message(
            "Select a note to see it:",
            components=[ActionRow([SelectMenu("notes_list", options)])],
            ephemeral=True,
        )
    else:
        # Put in a normal message. Try to preview each note.
        result = "\n".join(
            f"{key}: {description if len(description) <= 100 else description[:97]+'...'}"
            for key, description in user.notes.items()
        )
        if len(result) < 1950:
            result = '```' + result + '```'
        else:
            # Too large with the preview -> just send each key
            result = "```\n" + ", ".join(user.notes.keys()) + "```"
        return Message(result, ephemeral=True)


@blueprint.custom_handler("notes_list")
@requires_read
def show_full_note(ctx: Context):
    name = ctx.values[0]
    note = (database.get(ctx.author.id) or UserRecord()).notes.get(name)
    if note is None:
        return Message(f"Note {name} not found. You may have deleted it?", ephemeral=True)

    if MANAGE_ENABLED:
        components = [
            ActionRow([
                Button(
                    ("update_note", name),
                    ButtonStyles.SECONDARY,
                    "Update this note."
                ),
                Button(
                    ("delete_note", name),
                    ButtonStyles.DANGER,
                    "Delete this note."
                ),
            ])
        ]
    else:
        components = []

    return Message(
        note,
        ephemeral=True,
        components=components,
    )

@blueprint.custom_handler("update_note")
@requires_management
def update_note_button(ctx: Context, note_name: str):
    return modal(note_name, database[ctx.author.id].notes.get(note_name, ''))

@blueprint.custom_handler("delete_note")
@requires_management
def delete_note_button(ctx: Context, note_name: str):
    user = database[ctx.author.id]
    if note_name in user.notes:
        del user.notes[note_name]
        database[ctx.author.id] = user
        return Message(f"Deleted note {note_name}.", ephemeral=True)
    else:
        return Message(f"Note {note_name} not found.", ephemeral=True)

# Importing / Exporting files
@notes.command(
    "export",
    "Export your existing notes as a file",
    options=[
        Option("file_type", str, choices=[Choice(x.upper(), x) for x in ("csv", "json")], required=True),
    ]
)
@requires_read
def export_notes(ctx: Context, file_type: str):
    user = database.get(ctx.author.id)
    if user is None or not user.notes:
        return Message("You have no notes.", ephemeral=True)
    file = io.StringIO()
    if file_type == "json":
        json.dump(user.notes, file, indent=4)
    elif file_type == "csv":
        rows = [(key, value) for key, value in user.notes.items()]
        csv.writer(file).writerows(rows)
    else:
        return Message("Invalid file type", ephemeral=True)  # Should never happen
    file.seek(0)
    msg = Message("Here's your notes: ", file=(f'notes.{file_type}', file), ephemeral=True)
    return msg


@notes.command("import", "Import your Notes into the bot")
@requires_management
def import_notes(ctx: Context, file: Attachment):
    user = database.get(ctx.author.id) or UserRecord()
    if file.filename.endswith("csv"):
        data = requests.get(file.url).text
        data = list(csv.reader(data.splitlines()))
    elif file.filename.endswith("json"):
        data = requests.get(file.url).json()
        data = [(k, v) for k, v in data.items()]
    else:
        return Message("File type not supported", ephemeral=True)
    for note_name, note_value in data:
        user.notes[note_name.strip()] = note_value.strip()
    database[ctx.author.id] = user
    return Message("Updated your notes", ephemeral=True)


@get_note.autocomplete()
@update_note.autocomplete()
@delete_note.autocomplete()
@set_note.autocomplete()
@note_modal.autocomplete()
# @requires_read but doesn't returns messages so cannot use the decorator as-is 
def note_name_autocomplete_handler(ctx, name: Option = None, **_):
    if name is None or not name.focused:
        return []
    if not READ_ENABLED:
        return []
    user = database.get(ctx.author.id) or UserRecord()
    options = []
    for key, description in user.notes.items():
        if key.startswith(name.value):
            display = f"{key}: {description}"
            if len(display) > 100:
                display = display[:97] + '...'
            options.append(Choice(name=display, value=key))
            # It will visually fill in the command with the `name` if you click it, 
            # but it will send with the correct `value` even then
    options.sort(key=lambda option: option.name)
    return options[:25]

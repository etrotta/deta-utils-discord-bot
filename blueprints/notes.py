from deta_discord_interactions import (
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
from deta_discord_interactions.utils.database import Database, AutoSyncRecord

blueprint = DiscordInteractionsBlueprint()
database = Database(record_type=AutoSyncRecord)


notes = blueprint.command_group(
    "notes",
    "Create, Read, Update, Delete and List personal notes. See the FAQ for privacy details."
)

# Create
@notes.command("create", "Add a new note to your collection.")
def add_note(ctx: Context, name: str, description: str):
    user = database[ctx.author]
    user_notes = user.setdefault("notes", {})
    if name in user_notes:
        return Message(f"Note {name} already exists, use `/notes update` if you want to change it", ephemeral=True)
    user_notes[name] = description
    return Message(f"Registered note {name}", ephemeral=True)

# Read
@notes.command("get", "Retrieve a note from your collection.")
def get_note(ctx: Context, name: Autocomplete[str]):
    user = database[ctx.author]
    return Message(
        user.setdefault("notes", {}).get(name, f"Note {name} not found"),
        ephemeral=True,
    )

# Update
@notes.command("update", "Update an existing note")
def update_note(ctx: Context, name: Autocomplete[str], description: str):
    user = database[ctx.author]
    user_notes = user.setdefault("notes", {})
    if name not in user_notes:
        return Message(f"Note {name} not found. Use `/notes create` to add a new one", ephemeral=True)
    elif user_notes[name] == description:
        return Message(f"Note {name} was already set to that", ephemeral=True)
    else:
        user_notes[name] = description
        return Message(f"Note {name} updated", ephemeral=True)


# Delete
@notes.command("delete", "Delete an existing note")
def delete_note(ctx: Context, name: Autocomplete[str]):
    user = database[ctx.author]
    user_notes = user.setdefault("notes", {})
    if name not in user_notes:
        return Message(f"Note {name} not found", ephemeral=True)
    else:
        del user_notes[name]
        return Message(f"Note {name} deleted", ephemeral=True)


# Alternative methods to create / update
@notes.command("set", "Update an existing note or create a new one")
def set_note(ctx: Context, name: Autocomplete[str], description: str):
    user = database[ctx.author]
    user_notes = user.setdefault("notes", {})
    is_update = name in user_notes
    user_notes[name] = description
    if is_update:
        return Message(f"Note {name} updated", ephemeral=True)
    else:
        return Message(f"Note {name} registered", ephemeral=True)


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
def note_modal(ctx: Context, name: Autocomplete[str] = ''):
    if name:
        user = database[ctx.author]
        user_notes = user.setdefault("notes", {})
        return modal(name, user_notes.get(name, ''))
    else:
        return modal('', '')


@blueprint.command("Save as note", "Save this message as a personal note.", type=ApplicationCommandType.MESSAGE)
def message_to_note(ctx: Context, message: Message):
    if len(message.content) > 4000:
        return Message("This message is too long to save as a note!", ephemeral=True)
    return modal('', message.content)


@blueprint.custom_handler("notes_modal")
def save_modal_note(ctx: Context):
    user = database[ctx.author]
    user_notes = user.setdefault("notes", {})
    name = ctx.get_component("note_name").value
    is_update = name in user_notes
    description = ctx.get_component("note_description").value
    user_notes[name] = description
    if is_update:
        return Message(f"Updated note {name}", ephemeral=True)
    else:
        return Message(f"Registered note {name}", ephemeral=True)


# List
@notes.command("list", "List all notes from your collection")
def list_notes(ctx: Context):
    user = database[ctx.author]
    user_notes = user.setdefault("notes", {})

    # If it fits in a Select Menu
    if len(user_notes) <= 25:
        options = []
        for name, description in user_notes.items():
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
            for key, description in user_notes.items()
        )
        if len(result) < 1950:
            result = '```' + result + '```'
        else:
            # Too large with the preview -> just send each key
            result = "```\n" + ", ".join(user_notes.keys()) + "```"
        return Message(result, ephemeral=True)


@blueprint.custom_handler("notes_list")
def show_full_note(ctx: Context):
    name = ctx.values[0]
    note = database[ctx.author]["notes"].get(name)
    if note is None:
        return Message("Note not found. You may have deleted it?", ephemeral=True)
    return Message(
        note,
        ephemeral=True,
        components=[
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
    )

@blueprint.custom_handler("update_note")
def update_note_button(ctx: Context, note_name: str):
    return modal(note_name, database[ctx.author]["notes"].get(note_name, ''))

@blueprint.custom_handler("delete_note")
def delete_note_button(ctx: Context, note_name: str):
    user_notes = database[ctx.author]["notes"]
    if note_name in user_notes:
        del user_notes[note_name]
        return Message(f"Deleted note {note_name}", ephemeral=True)
    else:
        return Message(f"Note {note_name} not found", ephemeral=True)


@get_note.autocomplete()
@update_note.autocomplete()
@delete_note.autocomplete()
@set_note.autocomplete()
@note_modal.autocomplete()
def note_name_autocomplete_handler(ctx, name: Option = None, **_):
    if name is None or not name.focused:
        return []
    user = database[ctx.author]
    user_notes = user.setdefault("notes", {})
    options = []
    for key, description in user_notes.items():
        if key.startswith(name.value):
            display = f"{key}: {description}"
            if len(display) > 100:
                display = display[:97] + '...'
            options.append(Choice(name=display, value=key))
            # It will visually fill in the command with the `name` if you click it, 
            # but it will send with the correct `value` even then
    options.sort(key=lambda option: option.name)
    return options[:25]

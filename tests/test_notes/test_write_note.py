import pytest

from deta_discord_interactions import ActionRow, Client, Component, Context, Message, Modal, TextInput, User
from deta_discord_interactions.utils.database import Database

from utilsbot.blueprints import notes

@pytest.fixture()
def database(tmp_path):
    database = Database("test_database", notes.UserRecord, base_mode="DISK", base_folder=tmp_path)
    database["0"] = notes.UserRecord({})
    database["1"] = notes.UserRecord({"test": "hello world", "other": "goodbye world"})
    return database


def test_set_note(client: Client, database: Database, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(notes, "database", database)
    with client.context(Context(author=User(id="0"))):
        result: Message = client.run("notes", "set", "numbers", "123")
        assert 'registered' in result.content.casefold()
        result: Message = client.run("notes", "set", "numbers", "123456789")
        assert 'updated' in result.content.casefold()

        assert database["0"].notes == {"numbers": "123456789"}
        # Test a get just in case
        result: Message = client.run("notes", "get", "numbers")
        assert result.content == "123456789"

def test_create_note(client: Client, database: Database, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(notes, "database", database)
    with client.context(Context(author=User(id="0"))):
        result: Message = client.run("notes", "create", "letters", "abc")
        assert 'registered' in result.content.casefold()
        result: Message = client.run("notes", "create", "letters", "abcxyz")
        assert 'already exists' in result.content.casefold()

        assert database["0"].notes == {"letters": "abc"}

def test_update_note(client: Client, database: Database, monkeypatch: pytest.MonkeyPatch):
    database["0"] = notes.UserRecord(notes={"letters": "abc"})
    monkeypatch.setattr(notes, "database", database)
    with client.context(Context(author=User(id="0"))):
        result: Message = client.run("notes", "update", "nonexisting", "abc")
        assert 'not found' in result.content.casefold()
        result: Message = client.run("notes", "update", "letters", "abcxyz")
        assert 'updated' in result.content.casefold()

        assert database["0"].notes == {"letters": "abcxyz"}

def test_model_note(client: Client, database: Database, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(notes, "database", database)
    ctx = Context(
        components=[
            ActionRow([TextInput("note_name", value="modalnote")]),
            ActionRow([TextInput("note_description", value="From a modal!")]),
        ],
        author=User(
            id="42"
        )
    )
    with client.context(ctx):
        result: Message = client.run_handler("notes_modal")
        assert 'registered note' in result.content.casefold()
        result: Message = client.run_handler("notes_modal")
        assert 'updated note' in result.content.casefold()
        
    assert database["42"].notes == {"modalnote": "From a modal!"}
    # ---
    with client.context(Context(author=User(id="42"))):
        result: Modal = client.run("notes", "modal", "nonexisting")
        name: TextInput = result.components[0].components[0]
        desc: TextInput = result.components[1].components[0]
        assert name.label == "Name"
        assert name.value == "nonexisting"
        assert desc.label == "Description"
        assert desc.value == ""
        # ---
        result: Modal = client.run("notes", "modal", "modalnote")
        name: TextInput = result.components[0].components[0]
        desc: TextInput = result.components[1].components[0]
        assert name.value == "modalnote"
        assert desc.value == "From a modal!"

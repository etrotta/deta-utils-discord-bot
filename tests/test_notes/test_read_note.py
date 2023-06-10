import pytest

from deta_discord_interactions import Client, Context, Message, User
from deta_discord_interactions.utils.database import Database

from utilsbot.blueprints import notes

@pytest.fixture(autouse=True)
def database_fixture(tmp_path, monkeypatch: pytest.MonkeyPatch):
    database = Database("test_database", notes.UserRecord, base_mode="DISK", base_folder=tmp_path)
    database["0"] = notes.UserRecord({})
    database["1"] = notes.UserRecord({"test": "hello world", "other": "goodbye world"})
    monkeypatch.setattr(notes, "database", database)


def test_new_user(client: Client):
    "User does not exists"
    with client.context(Context(author=User(id="999"))):
        result: Message = client.run("notes", "get", "test")
        assert result.content == "You have no notes."

def test_empty_notes(client: Client):
    "User exists, but does not have notes"
    with client.context(Context(author=User(id="0"))):
        result: Message = client.run("notes", "get", "test")
        assert result.content == "You have no notes."

def test_note_not_found(client: Client):
    "User exists, but does not have the note"
    with client.context(Context(author=User(id="1"))):
        result: Message = client.run("notes", "get", "doesnotexists")
        assert result.content == "Note `doesnotexists` not found."

def test_note_exists(client: Client):
    "User exists, and does have the note"
    with client.context(Context(author=User(id="1"))):
        result: Message = client.run("notes", "get", "test")
        assert result.content == "hello world"

def test_note_autocomplete(client: Client):
    with client.context(Context(author=User(id="1"))):
        result = client.run_autocomplete("notes", "get", "")
        choices = result.choices
        assert sorted(x.value for x in choices) == ["other", "test"]

    with client.context(Context(author=User(id="1"))):
        result = client.run_autocomplete("notes", "get", "te")
        choices = result.choices
        assert sorted(x.value for x in choices) == ["test"]

def test_note_read_handler(client: Client):
    with client.context(Context(values=["test"], author=User(id="1"))):
        result: Message = client.run_handler("notes_list")
        assert result.content == "hello world"


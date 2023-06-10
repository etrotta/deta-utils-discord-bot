import json
import pytest
from deta_discord_interactions import Client, Context, Message, SelectMenu
from deta_discord_interactions.utils.database import Drive

from utilsbot.blueprints import tags

@pytest.fixture(autouse=True)
def drive(tmp_path, monkeypatch: pytest.MonkeyPatch):
    drive = Drive("test_drive", drive_mode="DISK", drive_folder=tmp_path)

    (drive / 'hello.json').write_text(json.dumps({"content": "Hello World!"}))
    (drive / 'embed.json').write_text(json.dumps({"embed": {"title": "Hello Embeds!"}}))

    monkeypatch.setattr(tags, 'drive', drive)


def test_get(client: Client, context: Context):
    with client.context(context):
        result: Message = client.run("tag", "hello")
        assert result.content == "Hello World!"

        result: Message = client.run("tag", "embed")
        assert result.content is None
        assert result.embed.title == "Hello Embeds!"

        result: Message = client.run("tag", "unknown")
        assert result.content == "Tag not found."

def test_list(client: Client, context: Context):
    with client.context(context):
        result: Message = client.run("tags")
        assert result.content == "Select a tag to see it:"
        select_menu: SelectMenu = result.components[0].components[0]

        assert sorted(x.value for x in select_menu.options) == ["embed", "hello"]

def test_list_handler(client: Client, context: Context):
    with client.context(Context(values=["hello"])):
        result: Message = client.run_handler("tags_list")
        assert result.content == "Hello World!"

def test_autocomplete(client: Client, context: Context):
    with client.context(context):
        result = client.run_autocomplete("tag", "")
        choices = result.choices
        assert sorted(x.value for x in choices) == ["embed", "hello"]

    with client.context(context):
        result = client.run_autocomplete("tag", "hell")
        choices = result.choices
        assert sorted(x.value for x in choices) == ["hello"]

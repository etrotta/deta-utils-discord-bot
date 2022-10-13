from main import app
from deta_discord_interactions import Client
from deta_discord_interactions import Context
from deta_discord_interactions import ActionRow, TextInput

client = Client(app)

commands = [
    # ("tag", "bot_info"),
    # ("tag", "testnote123"),
    # ("manage", "testnote123"),
    # ("delete", "testnote123"),
]

handlers = [
    # ("tags_list", "bot_info"),
    # ("tags_list", "testnote123"),
    # ("tags_modal", ),
]

autocompletes = [
    # ("tag", ""),
]

with open("test.log", 'w') as file:
    ctx = Context(
        guild_id="903078036272975922",
        components=[
            ActionRow(
                [
                    TextInput(
                        custom_id="tag_name",
                        label="Name",
                        value="testnote123",
                    )
                ]
            ),
            ActionRow(
                [
                    TextInput(
                        custom_id="tag_body",
                        label="Body",
                        value="Test note value 1 2 3 4 5",
                    )
                ]
            )
        ],
    )
    with client.context(ctx):
        for command in commands:
            test = client.run(*command)
            print(command, test, end='\n\n')
            print(command, test, sep='\n', end='\n\n', file=file)

        for handler_id, *values in handlers:
            client.current_context.values = values

            test = client.run_handler(handler_id)
            print((handler_id, values), test, end='\n\n')
            print((handler_id, values), test, sep='\n', end='\n\n', file=file)

        for autocomplete in autocompletes:
            test = client.run_autocomplete(*autocomplete)
            print(autocomplete, test, end='\n\n')
            print(autocomplete, test, sep='\n', end='\n\n', file=file)
            print(len(test.choices))

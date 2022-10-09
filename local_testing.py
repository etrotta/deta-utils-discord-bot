from main import app
from deta_discord_interactions import Client
from deta_discord_interactions import Context

client = Client(app)

commands = [
    # ("faq", "bot_info"),

    # ("tags", "create", "test", "Testing tag"),
    # ("tag", "test"),
]

autocompletes = [
    # ("tag", ""),
]

with open("test.log", 'w') as file:
    ctx = Context(guild_id="903078036272975922")
    with client.context(ctx):
        for command in commands:
            test = client.run(*command)
            print(command, test, end='\n\n')
            print(command, test, sep='\n', end='\n\n', file=file)

        for autocomplete in autocompletes:
            test = client.run_autocomplete(*autocomplete)
            print(autocomplete, test, end='\n\n')
            print(autocomplete, test, sep='\n', end='\n\n', file=file)
            print(len(test.choices))

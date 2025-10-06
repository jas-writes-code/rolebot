from discord import *
import json
import re

with open('config.json', 'r') as f:
    config = json.load(f)

client = Client(intents=Intents.all())
key = config["key"]

async def list_roles(message, discard):
    async with message.channel.typing():
        guild = client.get_guild(int(message.guild.id))
        content = "**Configured response roles for this server:**"
        count = 0
        with open('config.json', 'r') as f:
            info = json.load(f)
        roles_data = info.get("roles", {}).get(str(message.guild.id), {})
        for item, role_id in roles_data.items():
            role = guild.get_role(int(role_id))
            role_name = role.name if role else "Unknown Role"
            content += f"\n**{item}**: {role_name} ({role.id})"
            count += 1
        if count == 0:
            content += "\nNo roles configured."
        await message.reply(content)

async def add_roles(message, args):
    async with message.channel.typing():
        with open('config.json', 'r') as f:
            info = json.load(f)
        if args[0] == "all":
            for element in info["roles"][str(message.guild.id)]:
                role = message.guild.get_role(int(info["roles"][str(message.guild.id)][element]))
                await message.author.add_roles(role)
            await message.reply("Added all responsive roles to your profile.")
            return
        content = "Added the following roles to your profile:"
        for element in args:
            try:
                role = message.guild.get_role(int(info["roles"][str(message.guild.id)][str(element)]))
            except KeyError:
                await message.reply("One or more roles not found. Have you checked `!roles`?")
            await message.author.add_roles(role)
            content += f"\n{role.name}"
        await message.reply(content)

async def remove_roles(message, args):
    async with message.channel.typing():
        with open('config.json', 'r') as f:
            info = json.load(f)
        if args[0] == "all":
            for element in info["roles"][str(message.guild.id)]:
                role = message.guild.get_role(int(info["roles"][str(message.guild.id)][element]))
                await message.author.remove_roles(role)
            await message.reply("Removed all responsive roles from your profile.")
            return
        content = "Removed the following roles from your profile:"
        for element in args:
            try:
                role = message.guild.get_role(int(info["roles"][str(message.guild.id)][str(element)]))
            except KeyError:
                await message.reply("One or more roles not found. Have you checked `!roles`?")
            await message.author.add_roles(role)
            await message.author.remove_roles(role)
            content += f"\n{role.name}"
        await message.reply(content)

async def add_to_list(message, args):
    async with message.channel.typing():
        if not message.author.guild_permissions.manage_roles:
            await message.reply("You're not allowed to do that.")
            return
        if not all(re.fullmatch(r"\d+", arg) for arg in args):
            await message.reply("Please ensure all role IDs are correct.\nUsage: !include <role ids>")
            return
        with open("config.json", "r") as f:
            config = json.load(f)
        content = ""
        guild_id = str(message.guild.id)
        existing_roles = config["roles"].get(guild_id, {})
        existing_role_ids = set(existing_roles.values())
        duplicates = [role_id for role_id in args if role_id in existing_role_ids]
        if duplicates:
            content += f"The following roles already exist and were not added: "
            for element in duplicates:
                role = message.guild.get_role(int(element))
                content += f"\n{role.name}"
        if existing_roles:
            next_index = max(int(k) for k in existing_roles.keys()) + 1
        else:
            next_index = 0
        # Add new roles
        for element in args:
            if element in existing_role_ids:
                continue
            existing_roles[str(next_index)] = element
            next_index += 1
        # Save updated roles back to config
        config["roles"][guild_id] = existing_roles
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
            content += f"\nAdded **{len(args) - len(duplicates)}** new responsive roles to **{message.guild.name}**. "
            content += f"Total roles configured: **{len(existing_roles)}**. Use !roles for more info"
        await message.reply(content)

async def set_roles(message, args):
    async with message.channel.typing():
        if not message.author.guild_permissions.manage_roles:
            await message.reply("You're not allowed to do that.")
            return
        if str(args[0]) == "0":
            with open("config.json", "r") as f:
                config = json.load(f)
            payload = {}
            config["roles"][str(message.guild.id)] = payload
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
            await message.reply(f"Removed all responsive roles for this server\nServer **{message.guild.name}** now has **0** responsive roles setup. Use !roles for more info.")
            return
        if not all(re.fullmatch(r"\d+", arg) for arg in args):
            await message.reply("Please ensure all role IDs are correct.\nUsage: !set <role ids>")
            return
        with open("config.json", "r") as f:
            config = json.load(f)
        payload = {}
        count = 0
        await message.reply("Updating config...")
        for element in args:
            payload[str(count)] = element
            count += 1
        if "roles" not in config:
            config["roles"] = {}
        config["roles"][str(message.guild.id)] = payload
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
        await message.reply(
            f"Server **{message.guild.name}** now has **{len(args)}** responsive roles setup. Use !roles for more info.")

@client.event
async def on_ready():
    print('-----')
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('-----')
    print("Init complete. This terminal will not provide feedback unless there is an error.")

@client.event
async def on_message(message):
    if not message.author.bot or message.author.system:
        parts = message.content.strip().split()
        cmd = parts[0].lstrip("!")
        args = parts[1:]
        if cmd in config["commands"]:
            action_name = config["commands"][cmd]
            func = globals().get(action_name)
            if callable(func):
                await func(message, args)
            else:
                print(f"No function defined for action '{action_name}'")

client.run(str(key))

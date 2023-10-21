import discord
from discord.ext import commands
import asyncio
import random

intents = discord.Intents.all()
client = commands.Bot(command_prefix="/", intents=intents)

game_started = False
min_players = 9
mafia_players = 2
killed_players = []

@client.event
async def on_ready():
    print("Bot hazırdır:")

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return
    
    await client.process_commands(message)

@client.command()
async def startgame(ctx):
    global game_started
    if game_started:
        await ctx.send("Əə bala sən geysən ? Görmürsən oyun başlayıb?")
        return

    await ctx.send("Salam əziz mafiasevərlər bu gün bura Fərrux kişinin xoş günündə mübarəkbazdığ eləməyə deyil mafia oynamaq üçün toplanmışıq. Elə indi /qosul yazıb göndərərək qırğın deyişməli oyunumuza qoşula bilərsiniz...")
    game_started = True

@client.command()
async def qosul(ctx):
    global game_started, killed_players
    if not game_started:
        await ctx.send("Ayə sən adam balasısan bu oyunu birinci /startgame yazıb başlat sonra /qosul yaz.")
        return

    player_gameready = discord.utils.get(ctx.guild.text_channels, name="gameready")
    players_ingame = discord.utils.get(ctx.guild.voice_channels, name="ingame")

    if player_gameready and players_ingame:
        if ctx.author.voice and ctx.author.voice.channel:
            voice_channel = ctx.author.voice.channel
            await ctx.author.move_to(players_ingame)
            await player_gameready.send(f"{ctx.author.name} ömrümüzə paz oldu.")
            
            # Get a list of players who joined the game
            joined_players = [member.name for member in players_ingame.members if member != client.user]
            joined_players_str = ', '.join(joined_players)
            
            await player_gameready.send(f"{ctx.author.name}  {voice_channel.name} kanalına qoşuldu...")
            await player_gameready.send(f"Həyatımıza girənlər: {joined_players_str}")
        else:
            await ctx.send("Blya zaybat eləmisize sən öl . Gözüvü aç bidənə sol kənara bax. orda kanallar var , ordan ingame olana qoşul ,qorxmaginən bu kanallardan su gəlmir(şit zarafatımı eləməliydim) sora gəlib /qosul yazarsan .")

@client.command()
async def start(ctx):
    global game_started, min_players, mafia_players, killed_players
    if not game_started:
        await ctx.send("Admin hara baxırsan ayə gəl oyunu başlat görüm")
        return

    await ctx.send("Qırğın deyişmə başlayır...")

    player_ingame = discord.utils.get(ctx.guild.text_channels, name="ingame")
    killedplayers_voice = discord.utils.get(ctx.guild.voice_channels, name="killedplayers")

    # Assign roles to players
    roles = ["Vətəndaş"] * 4 + ["Mafia"] * mafia_players + ["Komissar", "Doktor", "Kamikadze"]
    players_ingame = discord.utils.get(ctx.guild.voice_channels, name="ingame")

    if len(players_ingame.members) >= min_players:
        # Send poll to see if players want to start the game
        poll_message = await player_gameready.send("Yetəri qədər yetqa var . Bəlkə başdıyaq")
        await poll_message.add_reaction("✅")
        await poll_message.add_reaction("❌")

        await asyncio.sleep(60)  # Wait for players to vote

        poll_message = await player_gameready.fetch_message(poll_message.id)
        reactions = poll_message.reactions
        start_votes = 0
        wait_votes = 0

        for reaction in reactions:
            if reaction.emoji == "✅":
                start_votes += reaction.count
            elif reaction.emoji == "❌":
                wait_votes += reaction.count

        if start_votes >= (len(players_ingame.members) / 2):
            await player_gameready.send("Belə gördüm ki,çoxunun o biri gələcəy oyunçular qozuna deyil.Tak şto başlıyırıq")
            game_started = True
            await assign_roles(ctx)
            await nighttime(ctx)
        else:
            await player_gameready.send("Majority voted for waiting for new players.")
            game_started = False
    else:
        await ctx.send("9 oyunçu yoxdusa niyə mıxıvı dirəmisən mənə?")

async def assign_roles(ctx):
    global mafia_players, killed_players
    roles = ["Vətəndaş"] * 4 + ["Mafia"] * mafia_players + ["Komissar", "Doktor", "Kamikadze"]
    players_ingame = discord.utils.get(ctx.guild.voice_channels, name="ingame")

    # Assign random roles to players
    for player in players_ingame.members:
        role = random.choice(roles)
        roles.remove(role)
        await player.send(f"Sənin rolun budu gələ sür: {role} Sonra demiyin ki,Botun mizahı zad yoxdu")

    # Determine mafia players
    mafia_players_roles = discord.utils.get(ctx.guild.roles, name="Mafia")
    mafia_players = [player for player in players_ingame.members if mafia_players_roles in player.roles]

    # Send private message to Mafia players with the names of other Mafia players
    for mafia_player in mafia_players:
        other_mafia_players = [player.name for player in mafia_players if player != mafia_player]
        await mafia_player.send(f"Əzizim sən bir mafiasan oduki kimi istəsən gecələr rahat vurub mındar eliyə bilərsən , bu yetmdə mafiadı bunu vurmaginən {', '.join(other_mafia_players)}")

@client.command()
async def nighttime(ctx):
    players_ingame = discord.utils.get(ctx.guild.voice_channels, name="ingame")

    # Mute all players except for Mafia players
    for player in players_ingame.members:
        if player not in mafia_players:
            await player.edit(mute=True)

    await asyncio.sleep(45)  # Wait for 45 seconds

    # Unmute all players
    for player in players_ingame.members:
        await player.edit(mute=False)

@client.command()
async def mafianight(ctx):
    players_ingame = discord.utils.get(ctx.guild.voice_channels, name="ingame")
    killedplayers_voice = discord.utils.get(ctx.guild.voice_channels, name="killedplayers")
    mafia_players = [player for player in players_ingame.members if player.role.name == "Mafia"]

    # Mute all players except for Mafia players
    for player in players_ingame.members:
        if player not in mafia_players:
            await player.edit(mute=True)

    # Send poll to Mafia players with names of the players except the Mafia players
    other_players = [player.name for player in players_ingame.members if player not in mafia_players]
    poll_message = await killedplayers_voice.send(f"Vote to select a player to kill: {', '.join(other_players)}")
    for emoji in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]:
        await poll_message.add_reaction(emoji)

    await asyncio.sleep(60)  # Wait for 60 seconds

    poll_message = await killedplayers_voice.fetch_message(poll_message.id)
    reactions = poll_message.reactions
    voted_player = None

    for reaction in reactions:
        if reaction.count >= 2:
            voted_player = reaction.emoji
            break

    if voted_player:
        voted_player_index = int(voted_player.strip("️⃣")) - 1
        selected_player = [player for idx, player in enumerate(players_ingame.members) if idx == voted_player_index]
        await selected_player[0].move_to(killedplayers_voice)
        await players_ingame.send(f"{selected_player[0].name} Zor uşağ idi hayf ki həyat onu erkən dombaltdı")

@client.command()
async def morning(ctx):
    players_ingame = discord.utils.get(ctx.guild.voice_channels, name="ingame")
    killedplayers_voice = discord.utils.get(ctx.guild.voice_channels, name="killedplayers")

    # Unmute all players
    for player in players_ingame.members:
        await player.edit(mute=False)

    # Move killed players to "Killed Player" channel
    for member in players_ingame.members:
        if member.voice.channel == players_ingame:
            await member.move_to(killedplayers_voice)

    killed_players = killedplayers_voice.members

    # Send message for each killed player
    for player in killed_players:
        await players_ingame.send(f"{player.name} ala yığılışun Makedonu xosumbay elədilər")

@client.command()
async def discussion(ctx):
    await asyncio.sleep(60)  # Wait for 60 seconds

@client.command()
async def voting(ctx):
    players_ingame = discord.utils.get(ctx.guild.voice_channels, name="ingame")
    killedplayers_voice = discord.utils.get(ctx.guild.voice_channels, name="killedplayers")
    
    alive_players = [player for player in players_ingame.members if player not in killedplayers_voice.members]

    poll_options = ""
    for i, player in enumerate(alive_players):
        poll_options += f"{i+1}. {player.name}\n"

    poll_message = await killedplayers_voice.send(f"Sənə səlahiyyət verirəm vur birin mındar eləginən,:\n{poll_options}")
    for i in range(len(alive_players)):
        emoji = emoji_numbers[i]
        await poll_message.add_reaction(emoji)

    await asyncio.sleep(120)  # Wait for 120 seconds

    eliminated_players = []
    poll_message = await killedplayers_voice.fetch_message(poll_message.id)
    reactions = poll_message.reactions

    for reaction in reactions:
        if reaction.count >= len(alive_players) // 2:
            emoji = reaction.emoji
            player_index = emoji_numbers.index(emoji)
            eliminated_player = alive_players[player_index]
            eliminated_players.append(eliminated_player)

    for eliminated_player in eliminated_players:
        await eliminated_player.move_to(killedplayers_voice)
        await players_ingame.send(f"{eliminated_player.name} Ayə bunu kim xəşil elədi???.")


client.run("MTE2Mzc1NTI1MjU0NjI4OTY3NQ.GTr8rq.32bby95zaCJvd7abYxxG61kWYFxoYRKh58F9-8")

import os
import json
import discord
import logging
import asyncio
import requests
import datetime
import pickledb
import configparser
from owrap import Owrap
from pymongo import MongoClient
from discord.ext import commands

##########################################################

list_of_players_in_daily = []

config = configparser.ConfigParser()
config.read(os.path.abspath("config.conf"))
owrap = Owrap()

osu_token = config['Tokens']['osu_token']
TOKEN = config['Tokens']['discord_token']
prefix = config['Bot']['prefix']

setdb = pickledb.load(config['Names']['set_db'], True)
logging.basicConfig(filename=config['Names']['log_file'], level=logging.INFO, format='%(asctime)s %(message)s')
mongoclient = MongoClient(config['Names']['mongoclient'])
client = commands.Bot(command_prefix = prefix)

client.remove_command("help")

db = mongoclient['database']
collection = db['collection']

daily_db = mongoclient['daily_database']
daily_collection = db['collection']

##########################################################

def track_thing(r, uid, latest: bool = None, daily: bool = None):
    try:
        now = datetime.datetime.now()
        osu = owrap.osu(r)
        if daily == True:
            c = daily_collection
        else:
            c = collection
        document = False
        try:
            document = c.find_one({'_id': uid})
        except:
            print("nothing found adding")
        finally:
            a = {}
            a.update({'_id': uid})
            a.update({'time': now.strftime("%d-%b-%Y %I:%M:%S")})
            for key, val in osu.items():
                a.update({key: val})
            if document:
                if latest == True:
                    return c.find_one({'_id': uid})
                c.update_one({'_id': uid}, {"$set": a})
            else:
                c.insert_one(a)
                
        return c.find_one({'_id': uid})
    except Exception as e:
        logging.warning(e)

def embed_maker(ll, r):
    try:
        a300, a100, a50 = client.get_emoji(748991269526700214), client.get_emoji(748991283758104698), client.get_emoji(748991293308272750)
        sign1, sign2 ="-" if int(r['pp_rank']) >= ll['pp_rank'] else "+", "+" if float(r['accuracy']) >= ll['accuracy'] else ""
    
        embed=discord.Embed(color=0xff8f8f)
        embed.set_author(name=f"osu profil for {r['username']}", url=f"https://osu.ppy.sh/users/{r['user_id']}", icon_url=f"https://www.countryflags.io/{r['country']}/shiny/32.png")
        embed.set_thumbnail(url=f"http://s.ppy.sh/a/{r['user_id']}")
    
        embed.add_field(name=f"- Performance -", value=f"""
**Rank**: #{r['pp_rank']} ({sign1}{abs(int(r['pp_rank'])-ll['pp_rank'])})
**PP**: {r['pp_raw']} (+{round(float(r['pp_raw'])-ll['pp_raw'], 3)})
**Level**: {r['level']} (+{round(float(r['level'])-ll['level'], 3)})
**Accuracy**: {round(float(r['accuracy']), 2)} ({sign2}{round(float(r['accuracy'])-ll['accuracy'], 2)})
**Playcount**: {r['playcount']} (+{int(r['playcount'])-ll['playcount']})""", inline=True)
    
        embed.add_field(name=f"- Score -", value=f"""
**Ranked score**: {format(int(r['ranked_score']), ',d')} (+{format(int(r['ranked_score'])-ll['ranked_score'], ',d')})
**Total score**: {format(int(r['total_score']), ',d')} (+{format(int(r['total_score'])-ll['total_score'], ',d')})
**{a300}**: {format(int(r['count300']), ',d')} (+{format(int(r['count300'])-ll['count300'], ',d')})
**{a100}**: {format(int(r['count100']), ',d')} (+{format(int(r['count100'])-ll['count100'], ',d')})
**{a50}**: {format(int(r['count50']), ',d')} (+{format(int(r['count50'])-ll['count50'], ',d')})""", inline=True)
    
        embed.set_footer(text=f"Joined in {r['join_date']} || Playtime: {int(int(r['total_seconds_played'])/3600)}h || Last call: {ll['time']}")

        return embed
    except Exception as e:
        logging.warning(e)
    
async def daily_refresh(uid):
    try:
        list_of_players_in_daily.append(uid)
        for x in range(0, 2):
            p = {"k": osu_token, "u": uid}
            r = requests.get("https://osu.ppy.sh/api/get_user", params=p).json()[0]
            track_thing(r, r['user_id'], daily=True)
            await asyncio.sleep(60*60*24)
        list_of_players_in_daily.pop(uid)
    except Exception as e:
        logging.warning(e)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(f"{prefix}help"))
    print("bot started")
    logging.info('Bot started.')
# .format(sign2="+" if r['accuracy'] >= ll['accuracy'] else "-"

@commands.cooldown(1, 10, commands.BucketType.user)
@client.command(pass_context=True, no_pm=True)
async def profil(ctx, user: str = None):
    try:
        if user == None:
            user = setdb.get(str(ctx.message.author.id)) if setdb.get(str(ctx.message.author.id)) != False else ctx.message.author.name
	
        p = {"k": osu_token, "u": user}
        r = requests.get("https://osu.ppy.sh/api/get_user", params=p).json()[0]
        ll = track_thing(r, int(str(round(ctx.message.author.id/10000000))+r['user_id']), True)
        track_thing(r, int(str(round(ctx.message.author.id/10000000))+r['user_id']))

        await ctx.send(embed=embed_maker(ll, r))
    except Exception as e:
        logging.warning(e)
    #await ctx.send(f"{r['user_id']}\n{r['username']}\n{r['joinc['pp_rank']}\n{r['level']}\n{r['pp_raw']}")

@commands.cooldown(1, 10, commands.BucketType.user)
@client.command(pass_context=True, no_pm=True)
async def daily(ctx, user: str = None):
    try:
        if user == None:
            user = setdb.get(str(ctx.message.author.id)) if setdb.get(str(ctx.message.author.id)) != False else ctx.message.author.name
        
        p = {"k": osu_token, "u": user}
        r = requests.get("https://osu.ppy.sh/api/get_user", params=p).json()[0]
        ll = track_thing(r, r['user_id'], True)

        if r['user_id'] in list_of_players_in_daily:
            await ctx.send(embed=embed_maker(ll, r))
        else:
            await ctx.send(f"added {user} to daily tracking. this will expire in 72 hours.")
            await daily_refresh(r['user_id'])
    except Exception as e:
        logging.warning(e)

@client.command(pass_context=True)
async def help(ctx):
    await ctx.send(f"`{prefix}profil [name]` -> best profile shower with best tracking !\n`{prefix}daily [name]` -> shows how much earned in a day\n`{prefix}set [name]` -> links assigned name with your discord id so that you can do `{prefix}profil` without specifing name\n\nChangelog: https://github.com/jeesusmies/osuprofil/blob/master/changelog.md\nVersion: 0.9.1")

@client.command(pass_context=True, no_pm=True)
async def set(ctx, uname: str = None):
    try:
        if uname == None:
            await ctx.send("type a name")
            return
        if len(uname) > 32:
            await ctx.send("type a name shorter than 32 characters")

        setdb.set(str(ctx.message.author.id), uname)
        await ctx.send(f"added name {uname} to database")
    except Exception as e:
        logging.warning(e)

@profil.error
async def profil_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        msg = 'this command is ratelimited, please try again in {:.2f}s'.format(error.retry_after)
        await ctx.send(msg)
    else:
        raise error

@daily.error
async def daily_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        msg = 'this command is ratelimited, please try again in {:.2f}s'.format(error.retry_after)
        await ctx.send(msg)
    else:
        raise error
    

client.run(TOKEN)

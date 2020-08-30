import discord
from discord.ext import commands
import requests
import json
import datetime
import pickledb
from owrap import Owrap
from pymongo import MongoClient

osu_token = "token"
TOKEN = "token"

owrap = Owrap()
client = commands.Bot(command_prefix = "jimi ")
setdb = pickledb.load('setid.db', True)
mongoclient = MongoClient('mongodb://localhost:27017/')

client.remove_command("help")

db = mongoclient['database']
collection = db['collection']

def track_thing(r, uid, latest: bool = None):
    now = datetime.datetime.now()
    osu = owrap.osu(r)
    document = False
    try:
        document = collection.find_one({'_id': uid})
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
                return collection.find_one({'_id': uid})
            collection.update_one({'_id': uid}, {"$set": a})
        else:
            collection.insert_one(a)
                
    return collection.find_one({'_id': uid})
@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game("jimi help"))
    print("work")
# .format(sign2="+" if r['accuracy'] >= ll['accuracy'] else "-"

@commands.cooldown(1, 7, commands.BucketType.user)
@client.command(pass_context=True, no_pm=True)
async def profil(ctx, user: str = None):
    if user == None:
        user = setdb.get(str(ctx.message.author.id)) if setdb.get(str(ctx.message.author.id)) != False else ctx.message.author.name
	
    p = {"k": osu_token, "u": user}
    r = requests.get("https://osu.ppy.sh/api/get_user", params=p).json()[0]
    a300, a100, a50 = client.get_emoji(748991269526700214), client.get_emoji(748991283758104698), client.get_emoji(748991293308272750)

    ll = track_thing(r, int(str(round(ctx.message.author.id/10000000))+r['user_id']), True)
    track_thing(r, int(str(round(ctx.message.author.id/10000000))+r['user_id']))

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
    await ctx.send(embed=embed)
    #await ctx.send(f"{r['user_id']}\n{r['username']}\n{r['join_date']}\n{r['count300']}\n{r['count100']}\n{r['count50']}\n{r['playcount']}\n{r['ranked_score']}\n{r['total_score']}\n{r['pp_rank']}\n{r['level']}\n{r['pp_raw']}")

@client.command(pass_context=True)
async def help(ctx):
    await ctx.send("`jimi profil {name}` -> best profile shower with best tracking !\n`jimi daily {}` -> shows how much earned in a day (IN PROGRESS)\n`jimi set {name}` -> links assigned name with your discord id so that you can do `jimi profil` without specifing name")

@client.command(pass_context=True, no_pm=True)
async def set(ctx, uname: str = None):
    if uname == None:
        await ctx.send("type a name")
        return
    if len(uname) > 32:
        await ctx.send("type a name shorter than 32 characters")

    setdb.set(str(ctx.message.author.id), uname)
    await ctx.send(f"added name {uname} to database")
    

client.run(TOKEN)

from common import *


wager_choices = [
  discord.OptionChoice(
    name=str(i),
    value=i
  )
  for i in range(1, 26)
]

@bot.slash_command(
  name="setwager",
  description="Set your default wager for /poker and /slots"
)
@option(
  name="wager",
  description="How much would you like to wager?",
  required=True,
  choices=wager_choices
)
async def setwager(ctx:discord.ApplicationContext, wager:int):
  """
  This function is the main entrypoint of the /setwager command
  and will a user's wager value to the amount passed between 1-25
  """
  min_wager = 1
  max_wager = 25
  player = get_user(ctx.author.id)
  current_wager = player["wager"]
  if min_wager <= wager <= max_wager:
    set_player_wager(ctx.author.id, wager)
    await ctx.respond(embed=discord.Embed(
      title="Wager Updated!",
      description=f"{ctx.author.mention}: Your default wager has been changed from `{current_wager}` to `{wager}`",
      color=discord.Color.green()
    ), ephemeral=True)
  else:
    await ctx.respond(embed=discord.Embed(
      title="Invalid Wager",
      description=f"{ctx.author.mention}: Wager must be between `{min_wager}` and `{max_wager}`\nYour current wager is: `{current_wager}`",
      color=discord.Color.red()
    ), ephemeral=True)


def set_player_wager(discord_id, amt):
  """
  This function takes a player's discord ID
  and a positive integer and updates the wager
  value for that user in the db
  """
  with AgimusDB(dictionary=True) as query:
    amt = max(amt, 0)
    sql = "UPDATE users SET wager = %s WHERE discord_id = %s"
    vals = (amt, discord_id)
    query.execute(sql, vals)
  
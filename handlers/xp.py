import math
from time import sleep
from numpy import block
from common import *
from commands.badges import give_user_badge, send_badge_reward_message
from queries.wishlist import db_autolock_badges_by_filenames_if_in_wishlist, db_get_user_wishlist_badges
from utils.badge_utils import db_get_user_badges, db_purge_users_wishlist

# rainbow of colors to cycle through for the logs
xp_colors = [
    Fore.RED,
    Fore.LIGHTRED_EX,
    Fore.YELLOW,
    Fore.LIGHTYELLOW_EX,
    Fore.GREEN,
    Fore.LIGHTGREEN_EX,
    Fore.LIGHTCYAN_EX,
    Fore.CYAN,
    Fore.LIGHTBLUE_EX,
    Fore.BLUE,
    Fore.MAGENTA,
    Fore.LIGHTMAGENTA_EX
]
current_color = 0

f = open("./data/level_up_messages.json")
random_level_up_messages = json.load(f)
f.close()

# {user} got xp for {reason}
reasons = {
  "posted_message" : "posting a message",
  "added_reaction" : "adding a reaction",
  "got_reactions"  : "getting lots of reactions",
  "intro_message"  : "posting an introduction in #first-contact",
  "starboard_post" : "getting a post sent to the starboard",
  "slot_win"       : "winning the slots",
  "quiz_win"       : "winning a quiz",
  "trivia_win"     : "winning at trivia",
  "trivia_play"    : "participating in trivia",
  "poker_win"      : "winning a hand of poker",
  "used_computer"  : "using the computer",
  "asked_agimus"   : "asking agimus a question",
  "used_wordcloud" : "generating a wordcloud",
  "played_zork"    : "playing zork",
  "created_event"  : "creating an event"
}

# handle_message_xp(message) - calculates xp for a given message
# message[required]: discord.Message
async def handle_message_xp(message:discord.Message):
    blocked_channel_ids = get_channel_ids_list(config["handlers"]["xp"]["blocked_channels"])
    # we don't like bots round here, or some channels
    if message.author.bot or message.channel.id in blocked_channel_ids:
      return

    # base XP
    xp_amt = 0

    # if the message is equal to or longer than 3 words +1 xp
    if len(message.content.split()) >= 3:
      xp_amt += 1

      # if that message also has any of our server emoji, +1 xp
      # case sensitive (cool != COOL)
      for e in config["all_emoji"]:
        if message.content.find(e) != -1:
          xp_amt += 1
          break

    # if the message is longer than 33 words +1 more xp
    if len(message.content.split()) > 33:
      xp_amt += 1

    # ...and 66, +1 more xp
    if len(message.content.split()) > 66:
      xp_amt += 1

    # if there's an attachment, +1 xp
    if len(message.attachments) > 0:
      xp_amt += 1

    if xp_amt != 0:
      await increment_user_xp(message.author, xp_amt, "posted_message", message.channel) # commit the xp gain to the db

    # Handle Auto-Promotions
    promotion_roles_config = config["roles"]["promotion_roles"]
    if promotion_roles_config["enabled"]:
      cadet_role = promotion_roles_config["ranks"]["cadet"]
      ensign_role = promotion_roles_config["ranks"]["ensign"]
      guild_roles = await message.author.guild.fetch_roles()
      guild_role_names = [r.name for r in guild_roles]
      if cadet_role in guild_role_names and ensign_role in guild_role_names:
        await handle_intro_channel_promotion(message)
        await handle_rank_xp_promotion(message, xp_amt)
      else:
        logger.info(f"Promotion is enabled but {Fore.CYAN}Cadet{Fore.RESET} and {Fore.CYAN}Ensign{Fore.RESET} roles are not available from the guild!")
        logger.info(f"Available roles are: {Style.BRIGHT}{guild_role_names}{Style.RESET_ALL}.")


# If this message is in the intro channel, handle their auto-promotion
async def handle_intro_channel_promotion(message):
  promotion_roles_config = config["roles"]["promotion_roles"]

  if message.channel.id == get_channel_id(config["intro_channel"]):
    member = message.author
    cadet_role_name = promotion_roles_config["ranks"]["cadet"]
    author_role_names = [r.name for r in message.author.roles]
    guild_roles = await message.author.guild.fetch_roles()

    cadet_role = None
    for role in guild_roles:
      if role.name == cadet_role_name:
        cadet_role = role

    if cadet_role_name not in author_role_names:
      # if they don't have this role, give them this role!
      logger.info(f"Adding {Fore.CYAN}Cadet{Fore.RESET} role to {Style.BRIGHT}{message.author.name}{Style.RESET_ALL}")
      await member.add_roles(cadet_role)
      await increment_user_xp(member, 10, "intro_message", message.channel)

      # add reactions to the message they posted
      welcome_reacts = [get_emoji("ben_wave_hello"), get_emoji("adam_wave_hello")]
      random.shuffle(welcome_reacts)
      for i in welcome_reacts:
        await message.add_reaction(i)

      # Give them a nice welcoming badge if they don't have one already
      give_welcome_badge(message.author.id)

      # send message to admins
      usher_msgs = config["handlers"]["xp"]["usher_messages"]
      welcome_embed = discord.Embed(
        title=f"Could someone {random.choice(usher_msgs)}?",
        color=discord.Color.random(),
        description=f"Please greet our new crewmember in <#{get_channel_id(config['channels']['ten-forward'])}>! Here are tips for welcoming a Friend of Desoto aboard the Hood:\n"
      )

      welcome_embed.set_image(url=random.choice(config["handlers"]["xp"]["welcome_images"]))

      welcome_embed.add_field(name=f"Offer advice {get_emoji('pakled_smart_lol')}", value=f"Recommend they visit the <#{get_channel_id(config['channels']['channel-guide'])}> and <#{get_channel_id(config['channels']['roles-and-pronouns'])}> channels", inline=False)
      welcome_embed.add_field(name=f"Greet them in the spirit of Shimoda {get_emoji('drunk_shimoda_smile_happy')}", value="Provide a humorous, fun, and even a little bit embarrassing welcome to them", inline=False)

      welcome_embed.add_field(name=f"Read their intro {get_emoji('bashir_zoom_look_huh')}", value=f"Make your greeting personalized based on what they posted! Find their intro here: {message.jump_url}", inline=False)
      welcome_embed.add_field(name=f"Bring them into the fold {get_emoji('kira_good_morning_hello')}", value=f"Let them know it's okay to jump in anywhere, anytime. Offer a channel for them to get started on! (like <#{get_channel_id(config['channels']['animal-holophotography'])}>)", inline=False)

      welcome_embed.set_footer(text="Thank you officers! 💖")
      mods_channel = bot.get_channel(get_channel_id(config["mods_channel"]))
      await mods_channel.send(content=f"@here -- attention senior officers! {message.author.mention} has just posted an intro!\n\n", embed=welcome_embed)

# If they've hit an XP threshold, auto-promote to general ranks
async def handle_rank_xp_promotion(message, xp):
  promotion_roles_config = config["roles"]["promotion_roles"]

  cadet_role_name = config["roles"]["promotion_roles"]["ranks"]["cadet"]
  ensign_role_name = config["roles"]["promotion_roles"]["ranks"]["ensign"]
  author_role_names = [r.name for r in message.author.roles]

  guild_roles = await message.author.guild.fetch_roles()

  cadet_role = None
  ensign_role = None
  for role in guild_roles:
    if role.name == cadet_role_name:
      cadet_role = role
    if role.name == ensign_role_name:
      ensign_role = role

  user_xp = get_user_xp(message.author.id).get("xp") # second element of tuple is the xp

  if cadet_role_name not in author_role_names:
    # if they don't have cadet yet and they are over the required xp, give it to them
    if user_xp >= promotion_roles_config["required_rank_xp"]["cadet"]:
      await message.author.add_roles(cadet_role)
      logger.info(f"{Style.BRIGHT}{message.author.display_name}{Style.RESET_ALL} has been promoted to {Fore.CYAN}Cadet{Fore.RESET} via XP!")
      # Give them a nice welcoming badge if they don't have one already
      give_welcome_badge(message.author.id)
  elif ensign_role_name not in author_role_names:
    # if they do have cadet but not ensign yet, give it to them
    if user_xp >= promotion_roles_config["required_rank_xp"]["ensign"]:
      await message.author.add_roles(ensign_role)
      logger.info(f"{Style.BRIGHT}{message.author.display_name}{Style.RESET_ALL} has been promoted to {Fore.GREEN}Ensign{Fore.RESET} via XP!")


async def handle_react_xp(reaction:discord.Reaction, user:discord.User):
  # Check if this user has already reacted to this message with this emoji
  blocked_channel_ids = get_channel_ids_list(config["handlers"]["xp"]["blocked_channels"])
  if reaction.message.author.bot or user.bot or reaction.message.channel.id in blocked_channel_ids:
    return

  global current_color

  reaction_already_counted = check_react_history(reaction, user)
  if reaction_already_counted:
    return

  log_react_history(reaction, user)
  await increment_user_xp(user, 1, "added_reaction", reaction.message.channel)

  # Give the author some bonus XP if they've made a particularly reaction-worthy message!
  threshold_relevant_emojis = [
    get_emoji("data_lmao_lol"),
    get_emoji("picard_yes_happy_celebrate"),
    get_emoji("love_heart_tgg"),
    get_emoji("BITS"),
    get_emoji("weyoun_love_heart"),
    get_emoji("tendi_smile_happy"),
    get_emoji("THIS"),
    get_emoji("NICE"),
    get_emoji("YES"),
    get_emoji("picard_yes_happy_celebrate")
  ]

  xp_amt = 0
  if reaction.emoji in threshold_relevant_emojis and reaction.count >= 5 and reaction.count < 10:
    xp_amt = 1

  if f"{reaction.emoji}" in threshold_relevant_emojis and reaction.count >= 10 and reaction.count < 20:
    xp_amt = 2

  if f"{reaction.emoji}" in threshold_relevant_emojis and reaction.count >= 20:
    xp_amt = 5

  if xp_amt > 0:
    await increment_user_xp(reaction.message.author, xp_amt, "got_reactions", reaction.message.channel)

async def handle_event_creation_xp(event):
  creator = await bot.fetch_user(event.creator_id)
  location = event.location.value
  if type(location) == str:
    # Users might create an event that isn't a VoiceChannel
    return
  await increment_user_xp(creator, 30, "created_event", location)

# calculate_xp_for_next_level(current_level)
# current_level[required]: int
# returns the amount of xp required to level up for the given level
def calculate_xp_for_next_level(current_level:int):
  return int( (current_level*69) + (current_level * current_level) - 1)

# util function for debug - shows an XP chart like D&D
def show_list_of_levels():
  level_chart = ""
  previous_xp_amt = 0
  for i in range(101):
    xp_required = calculate_xp_for_next_level(i)
    amt_diff = xp_required - previous_xp_amt
    previous_xp_amt = xp_required
    level_chart += f"{i} - {xp_required} - ({amt_diff})\n"
  logger.info(level_chart)

# level_up_user(user, level)
# user[required]:discord.User
# level[required]:int
# level up user to next level and give them a badge (in the DB)
# also fires the send_level_up_message function
async def level_up_user(user:discord.User, level:int):
  rainbow_l = f"{Back.RESET}{Back.RED} {Back.YELLOW} {Back.GREEN} {Back.CYAN} {Back.BLUE} {Back.MAGENTA} {Back.RESET}"
  rainbow_r = f"{Back.RESET}{Back.MAGENTA} {Back.BLUE} {Back.CYAN} {Back.GREEN} {Back.YELLOW} {Back.RED} {Back.RESET}"
  logger.info(f"{rainbow_l} {Style.BRIGHT}{user.display_name}{Style.RESET_ALL} has reached {Style.BRIGHT}level {level}!{Style.RESET_ALL} {rainbow_r}")
  with AgimusDB() as query:
    sql = "UPDATE users SET level = level + 1 WHERE discord_id = %s"
    vals = (user.id,)
    query.execute(sql, vals)
  badge = give_user_badge(user.id)
  was_on_wishlist = False

  if badge != None:
    user_wishlist_badges = db_get_user_wishlist_badges(user.id)
    was_on_wishlist = badge in [b['badge_filename'] for b in user_wishlist_badges]
    # Lock the badge if it was in their wishlist
    db_autolock_badges_by_filenames_if_in_wishlist(user.id, [badge])
    # Remove any badges the user may have on their wishlist that they now possess
    db_purge_users_wishlist(user.id)

  await send_level_up_message(user, level, badge, was_on_wishlist)

def give_welcome_badge(user_id):
  user_badge_names = [b['badge_filename'] for b in db_get_user_badges(user_id)]
  if "Friends_Of_DeSoto.png" not in user_badge_names:
    with AgimusDB() as query:
      sql = "INSERT INTO badges (user_discord_id, badge_filename) VALUES (%s, 'Friends_Of_DeSoto.png');"
      vals = (user_id,)
      query.execute(sql, vals)

# send_level_up_message(user, level, badge)
# user[required]:discord.User
# level[required]:int
# badge[required]:str
async def send_level_up_message(user:discord.User, level:int, badge:str, was_on_wishlist:bool):
  notification_channel_id = get_channel_id(config["handlers"]["xp"]["notification_channel"])
  channel = bot.get_channel(notification_channel_id)

  embed_title = "Level up!"
  thumbnail_image = random.choice(config["handlers"]["xp"]["celebration_images"])
  embed_description = f"{user.mention} has reached **Level {level}**"
  if badge == None:
    embed_description += "! They've already collected ALL BADGES EVERYWHERE! Congratulations on the impressive feat!"
  else:
    embed_description += f" and earned a new badge!"

  if level == 2:
    embed_description += " and earned their first new unique badge!\n\nCongrats! To check out your full list of badges use `/badges showcase`.\n\nMore info about XP and the badge system and XP can be found by using `/help` in this channel."
  if was_on_wishlist:
    embed_description += "\n\n" + f"Exciting! This was also one they had on their **wishlist**! {get_emoji('picard_yes_happy_celebrate')}"

  message = random.choice(random_level_up_messages["messages"]).format(user=user.mention, level=level, prev_level=(level-1))
  await send_badge_reward_message(message, embed_description, embed_title, channel, thumbnail_image, badge, user)

# increment_user_xp(author, amt)
# messauge.author[required]: discord.User
# amt[required]: int
# channel[required]: discord.Channel
# This function will increment a users' XP and log the gain to the history
async def increment_user_xp(user:discord.User, amt:int, reason:str, channel):
  global current_color
  msg_color = xp_colors[current_color]
  star = f"{msg_color}{Style.BRIGHT}*{Style.NORMAL}{Fore.RESET}"
  is_weekend = bool(datetime.today().weekday() >= 4)
  xp_multiplier = 1
  if is_weekend:
    xp_multiplier = 2
  amt = int(amt * xp_multiplier)
  with AgimusDB() as query:
    sql = "UPDATE users SET xp = xp + %s, name = %s WHERE discord_id = %s AND xp_enabled = 1"
    vals = (amt, user.display_name, user.id)
    query.execute(sql, vals)
    updated = query.rowcount
  if updated > 0:
    log_xp_history(user.id, amt, channel.id, reason)
    # If reaction hasn't been logged already, go ahead and do so and then award some XP!
    reason_text = reasons[reason]
    if not reason_text:
      reason_text = reason
    logger.info(f"{star} {msg_color}{user.display_name}{Fore.RESET} earns {msg_color}{amt} XP{Fore.RESET} for {Style.BRIGHT}{reason_text}{Style.RESET_ALL}! {star}")
    current_color = current_color + 1
    if current_color >= len(xp_colors):
        current_color = 0
    user_xp_data = get_user_xp(user.id)
    user_xp = user_xp_data["xp"]
    next_level_xp = calculate_xp_for_next_level(user_xp_data["level"])
    #logger.info(f'User XP: {user_xp} User level: {user_xp_data["level"]} Next level XP: {next_level_xp}')
    if user_xp >= next_level_xp:
      try:
        await level_up_user(user, user_xp_data["level"]+1)
      except Exception as e:
        logger.info(f"Error trying to level up user: {e}")
        logger.info(traceback.format_exc())

# get_user_xp(discord_id)
# discord_id[required]: int
# Returns a users current XP
def get_user_xp(discord_id):
  with AgimusDB() as query:
    sql = "SELECT level, xp FROM users WHERE discord_id = %s"
    vals = (discord_id,)
    query.execute(sql, vals)
    user_xp = query.fetchone()
  return { "level": user_xp[0], "xp" : user_xp[1] }


def check_react_history(reaction:discord.Reaction, user:discord.User):
  with AgimusDB() as query:
    sql = "SELECT id FROM reactions WHERE user_id = %s AND reaction = %s AND reaction_message_id = %s"
    vals = (user.id, f"{reaction}", reaction.message.id)
    query.execute(sql, vals)
    reaction_exists = query.fetchone()
  return reaction_exists

def log_react_history(reaction:discord.Reaction, user:discord.User):
  with AgimusDB() as query:
    sql = "INSERT INTO reactions (user_id, user_name, reaction, reaction_message_id) VALUES (%s, %s, %s, %s)"
    vals = (user.id, user.display_name, f"{reaction}", reaction.message.id)
    query.execute(sql, vals)

# log_xp_history(user_discord_id:int, amt:int, channel_name:str, reason:str)
# user_discord_id[required]: int
# amt[required]: int
# channel_id[required]: int
# reason[required]: str
# This function will log xp gains to a table for reporting
def log_xp_history(user_discord_id:int, amt:int, channel_id:int, reason:str):
  with AgimusDB() as query:
    sql = "INSERT INTO xp_history (user_discord_id, amount, channel_id, reason) VALUES (%s, %s, %s, %s)"
    vals = (user_discord_id, amt, channel_id, reason)
    query.execute(sql, vals)
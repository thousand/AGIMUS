# AGIMUS

The Friends of DeSoto are a group of fans of Star Trek and [The Greatest Generation podcast](http://gagh.biz). AGIMUS is our Discord bot for [The USS Hood Discord Server](https://drunkshimoda.com).

Details on how to contribute to the project can be found in [CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Makefile

Provided in this repository is a makefile to aid in building, testing and running AGIMUS in a variety of deployment environments. To see all available makefile targets, clone the repository and run `make help` in a terminal.

### Local Dependencies

To execute makefile commands, some third-party dependencies must be installed locally to run, build and test AGIMUS:

- [Docker](https://docs.docker.com/get-docker/)
- [KinD](https://kind.sigs.k8s.io/docs/user/quick-start/#installing-from-release-binaries)
- [Helm](https://helm.sh/docs/intro/install/)
- [Semver](https://github.com/fsaintjacques/semver-tool)
- [jq](https://stedolan.github.io/jq/)
- [yq](https://github.com/mikefarah/yq)

> **Note**  
> If you're using `homebrew` on macOS, you can install most of these in one go:  
> `$ brew install kind helm jq yq`  
> `docker` and `semver` are more easily installed through according to their maintainers' docs.

### Docker Usage

This discord bot is built with python using the [discord.py library](https://discordpy.readthedocs.io/en/stable/api.html) and requires a mysql db with credentials stored in a .env file ([.env example](.env-example)). To develop locally, docker is used to standardize infrastructure and dependencies.

```bash
# Clone AGIMUS source
git clone https://github.com/jp00p/AGIMUS.git && cd AGIMUS

# Fill out .env vars...
cp .env-example .env

# Build and start the docker containers
make docker-start

# Mysql session with database
make db-mysql

# Bash session in mysql container
make db-bash

# Mysql dump to file
make db-dump

# Mysql load from a file
make db-load

# Stop the containers
make docker-stop

# Blatent cheating
UPDATE users SET score=42069, spins=420, jackpots=69, wager=25, high_roller=1 WHERE id=1;
```

### Kubernetes Usage

AGIMUS can also be deployed in kubernetes. The provided helm chart includes a persistent volume claim for mysql to run in a pod, and the agimus container itself. To run AGIMUS in a KinD cluster, use the following makefile targets:

```bash
# Clone AGIMUS source
git clone https://github.com/jp00p/AGIMUS.git && cd AGIMUS

# Fill out .env vars...
cp .env-example .env

# Create a KinD cluster
make kind-create

# Build AGIMUS, and load it into the running KinD cluster
make kind-load

# Install AGIMUS via helm and
make kind-test
```

To install AGIMUS in an existing kubernetes cluster, a helm chart is published in this repository (note: ensure .env file is populated):

```bash
helm repo add agimus https://jp00p.github.io/AGIMUS
kubectl create namespace agimus
make helm-install
```

## Discord Permissions

First you will need a discord app and bot token to send messages. See this youtube playlist to learn how: https://www.youtube.com/playlist?list=PLRqwX-V7Uu6avBYxeBSwF48YhAnSn_sA4

Additional [discord role permissions](https://support.discord.com/hc/en-us/articles/206029707-Setting-Up-Permissions-FAQ):

- View channels
- Send messages
- Send messages in thread
- Add reaction
- Manage messages

Also for the Slash Commands you'll need to enable the `applications.commands` Scope for your bot _Application_ via the OAuth2 URL Generator.
Instructions for how to do this are available through this video at the 58 second timestamp: https://youtu.be/ygc-HdZHO5A?t=58

The bot now requires `Intents.members` and `Intents.presences`.  You must enable this through the "Privileged Gateway Intents" page on the Application page of the Discord developer's portal.

![AGIMUS permissions](https://i.imgur.com/rcZnQCo.png)

![AGIMUS "intents"](https://i.imgur.com/bGl9pf9.png)

## AGIMUS Commands and Triggers

Bot commands are triggered by typing an exclamation point followed by a command. Commands must be defined in the [configuration.json](configuration.json) file, a python file in the [commands directory](commands), and an import line added to [main.py](main.py).

| Command                                                                                                                                           | File                                          | Description                                                                                                                             |
| :-----------------------------------------------------------------------------------------------------------------------------------------------  | :-------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------- |
| `!clear_media`                                                                                                                                    | [clear_media.py](commands/clear_media.py)     | Deletes all .mp4s in `data/drops` and `data/clips` to ensure fresh copies are pulled down on command execution                          |
| `!qget [user]`                                                                                                                                    | [q.py](commands/q.py)                         | Get the information in mysql for a specific user                                                                                        |
| `!qset [user] [score \| spins \| jackpots \| wager \| high_roller \| profile_photo \| profile_sticker_1 \| xp] [new-value]`                       | [q.py](commands/q.py)                         | Set a value of a specific user in mysql                                                                                                 |
| `!quiz [tng \| voy \| ds9 \| friends \| firefly \| simpsons \| enterprise \| tos \| lowerdecks \| disco \| picard \| tas \| sunny]`               | [quiz.py](commands/quiz.py)                   | Guess the episode from a screen-shot!                                                                                                   |
| `!scores`                                                                                                                                         | [scores.py](commands/scores.py)               | Show the leaderboard of points                                                                                                          |
| `$testslots`                                                                                                                                      | [testslots.py](commands/testslots.py)         | Restricted command to run through 1k `/slots spin` commands to test success/failure rate                                                |
| `!update_status [playing \| listening \| watching] <status>`                                                                                      | [update_status.py](commands/update_status.py) | Update the bot's server profile status                                                                                                  |

### Slash Commands

Slash commands are triggered by typing a forward slash (`/`) followed by the command text. The same basic rules apply as the regular ! commands above as far as the info necessary in the [configuration.json](configuration.json) file, python file in the [commands directory](commands), and import line in [main.py](main.py).

| Command                                                                                                                                                           | File                                       | Description                                                                                                                                         |
| :---------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/badges [show_to_public]`                                                                                                                                        | [badges.py](commands/badges.py)            | Shows your collected badges                                                                                                                         |
| `/badge_sets [show_to_public] <category> <selection>`                                                                                                             | [badge_sets.py](commands/badges.py)        | Show off a set of badges and which ones you've collected so far                                                                                     |
| `/clip [post\|list] <query> (<private>)`                                                                                                                          | [clip.py](commands/clip.py)                | Posts a .mp4 clip file if it finds a match from the user's query. Clips are short videos while drops are for pod audio.                             |
| `/drop [post\list] <query> (<private>)`                                                                                                                           | [drop.py](commands/drop.py)                | Posts a .mp4 drop file if it finds a match from the user's query. Drops are for audio from the pod while clips are for short videos.                |
| `/dustbuster`                                                                                                                                                     | [dustbuster.py](commands/dustbuster.py)    | Return 5 random trek characters as discussion prompt                                                                                                |
| `/fmk`                                                                                                                                                            | [fmk.py](commands/fmk.py)                  | Return 3 random trek characters as discussion prompt                                                                                                |
| `/help`                                                                                                                                                           | [help.py](commands/help.py)                | Show a help message for a specific channel                                                                                                          |
| `/info [tng \| voy \| ds9 \| friends \| firefly \| simpsons \| enterprise \| tos \| lowerdecks \| disco \| picard \| tas \| sunny] [s##e##]`                      | [info.py](commands/info.py)                | Show information about a specific episode!                                                                                                          |
| `/setwager`                                                                                                                                                       | [setwager.py](commands/setwager.py)        | Wager value for poker game                                                                                                                          |
| `/slots jackpot`                                                                                                                                                  | [jackpot.py](commands/jackpot.py)          | Show the current jackpot value                                                                                                                      |
| `/slots jackpots`                                                                                                                                                 | [jackpots.py](commands/jackpots.py)        | Show the last 10 jackpot winners                                                                                                                    |
| `/slots spin [tng \| ds9 \| voy \| holodeck \| ships]`                                                                                                            | [slots.py](cogs/slots.py)                  | Slot machine game with trek characters or ships                                                                                                     |
| `/ping`                                                                                                                                                           | [ping.py](cogs/ping.py)                    | respond pong                                                                                                                                        |
| `/poker`                                                                                                                                                          | [poker.py](cogs/poker.py)                  | 5 card stud style game                                                                                                                              |
| `/profile`                                                                                                                                                        | [profile.py](commands/profile.py)          | Generate profile card with user statistics/options                                                                                                  |
| `/randomep [trek \| nontrek \| any \| tos \| tas \| tng \| ds9 \| voy \| enterprise \| lowerdecks \| disco \| picard \| friends \| firefly \| simpsons \| sunny]` | [randomep.py](commands/randomep.py)        | Show information about a random episode!                                                                                                            |
| `/setwager [wager]`                                                                                                                                               | [setwager.py](commands/setwager.py)        | Set your default wager for Slots and Poker                                                                                                          |
| `/shop [photos \| stickers \| roles]`                                                                                                                             | [shop.py](cogs/shop.py)                    | Shop with your points earned at games                                                                                                               |
| `/trekduel`                                                                                                                                                       | [trekduel.py](commands/trekduel.py)        | Return 2 random trek characters as discussion prompt                                                                                                |
| `/trektalk`                                                                                                                                                       | [trektalk.py](commands/trektalk.py)        | Return a random trek related discussion prompt                                                                                                      |
| `/trivia <category>`                                                                                                                                              | [trivia.py](cogs/trivia.py)                | Trivia game. (optional dropdown lists available categories)                                                                                         |
| `/tuvix`                                                                                                                                                          | [tuvix.py](commands/tuvix.py)              | Return 2 random trek characters as discussion prompt                                                                                                |
| `/wordcloud [enable logging: yes\| no]`                                                                                                                           | [wordcloud.py](commands/wordcloud.py)      | Generates a wordcloud based on a user's logged messages                                                                                             |

### "Computer:"/"AGIMUS:" Prompt
In addition to the `/` and `!` commands we have a special case for handling messages that begin with a "Computer:" or "AGIMUS:" prompt. It has an entry within `configuration.json` and the same rules apply to it as the `!` commands. Extending the feature should be done within `commands/computer.py`.

| Command                                  | File                                          | Description                                                                                                                             |
| :--------------------------------------- | :-------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------- |
| `[Computer:\|AGIMUS:] <text query>`      | [computer.py](commands/computer.py)           | Runs the user's query against Wolfram Alpha and OpenAI to provide a Star Trek "Computer"-like experience with context-aware responses.  |

#### Generating a Wolfram Alpha API ID

In order to use the basic "Computer:"/"AGIMUS:" prompt you'll need to also provide a Wolfram Alpha API ID which can be obtained from their site at https://products.wolframalpha.com/api . Full instructions for obtaining the API ID can be found in their [documentation](https://products.wolframalpha.com/api/documentation/).

A development ID key is free and supports up to 2000 queries per month.

Once generated it should be placed in your `.env` file as per the section in `.env-example`:

```bash
export WOLFRAM_ALPHA_ID=YOURKEYHERE
```

If the `.env` entry is not present, you'll see logs from the command firing but no action will be taken in response to the messages.

#### Generating an OpenAI API Key

In order to use the "advanced" "Computer:"/"AGIMUS:" prompt you'll need an OpenAI API Key with access to (by default) the "text-davinci-002" model. Signing up is very simple, just go to their site at https://beta.openai.com/ and create an account and you'll be granted a trial with an $18 credit for the first 3 months. The API Key can be found through your profile in the left sidebar.

Once generated it should be placed in your `.env` file as per the section in `.env-example`:

```bash
export OPENAI_API_KEY=YOURKEYHERE
```

The .env variable is automatically picked up by the `openai` python package.


OpenAI requests use "tokens" and for the Davinci model it costs 6 cents for 1k tokens. Each of our requests uses 196 tokens.

If you'd like to use a different (cheaper) model like "text-curie-002", you can enter one in `configuration.json` "computer" command config under `"openai_model"`

### configuration.json

The [configuration.json](configuration.json) file defines metadata about each command like what channel they can be executed in, what parameters can be passed, if the command requires additional data loaded, or if it should be enabled/disabled.

```json
"setwager": {
  "channels": [821892686201094154, 934827868066828308],
  "enabled": true,
  "data": null,
  "parameters": [{
    "name": "wager_value",
    "allowed": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25],
    "required": true
  }]
}
```

The file also provides the "Guild ID" for your server, note this is required in order for the slash commands to register properly and will cause a permissions error on startup if not provided!

```json
"guild_ids": [
  820440093898440756
]
```

### commands/command.py

Each command requires a python script that accepts a discord message as input where the first word matches the filename (Example: `!setwager 25` => [commands/setwager.py](commands/setwager.py))

```python
from .common import *
# setwager() - Entrypoint for !setwager command
# message[required]: discord.Message
# This function is the main entrypoint of the !setwager command
# and will a user's wager value to the amount passed between 1-25
async def setwager(message:discord.Message):
  min_wager = 1
  max_wager = 25
  wager_val = message.content.lower().replace("!setwager ", "")
  player = get_user(message.author.id)
  current_wager = player["wager"]
  if wager_val.isnumeric():
    wager_val = int(wager_val)
    if wager_val >= min_wager and wager_val <= max_wager:
      set_player_wager(message.author.id, wager_val)
      msg = f"{message.author.mention}: Your default wager has been changed from `{current_wager}` to `{wager_val}`"
      await message.channel.send(msg)
    else:
      msg = f"{message.author.mention}: Wager must be a whole number between `{min_wager}` and `{max_wager}`\nYour current wager is: `{current_wager}`"
      await message.channel.send(msg)
  else:
    msg = f"{message.author.mention}: Wager must be a whole number between `{min_wager}` and `{max_wager}`\nYour current wager is: `{current_wager}`"
    await message.channel.send(msg)

# set_player_wager(discord_id, amt)
# discord_id[required]: int
# amt[required]: int
# This function takes a player's discord ID
# and a positive integer and updates the wager
# value for that user in the db
def set_player_wager(discord_id, amt):
  db = getDB()
  amt = max(amt, 0)
  query = db.cursor()
  sql = "UPDATE users SET wager = %s WHERE discord_id = %s"
  vals = (amt, discord_id)
  query.execute(sql, vals)
  db.commit()
  query.close()
  db.close()
```

### main.py

Each command requires an explicit import in the [main.py](main.py) script.

```python
from commands.setwager import setwager
```

## Automation

The automation detailed below run in github action runners.

### Pull Requests and Merges

Pull requests to the main branch of the AGIMUS repository will automatically build a container and attempt to run the bot in a [KinD cluster](https://kind.sigs.k8s.io/docs/user/quick-start/#installing-from-release-binaries) and it uses [helm](https://helm.sh/docs/intro/install/) to install the kubernetes manifests into a running cluster. There are also make targets to assist in building and running AGIMUS in a KinD cluster locally. On merges to the main branch, another action will run to build and push the AGIMUS container to the github container registry and release a helm chart hosted as a github pages deployment.

### generate_episode_json.py

The repo also currently provides a way to automatically generate the files for the Greatest Gen `.json` files located under `data/episodes/` (such as `tgg_voy.json` for example). The utility is under `utils` as `generate_episode_json.py`.

The script uses Google to gather some of the metadata necessary for each entry, so you'll need to provide two additional ENV variables if you'd like to use this script.

```bash
export GOOGLE_API_KEY=
export GOOGLE_CX=
```

Step-by-step instructions for how to generate these credentials are documented in this [Stack Overflow post](https://stackoverflow.com/a/37084643)

Once those have been placed in your .env file, you can execute the script by providing the series prefix and path to the desired output file.

```bash
python utils/generate_episode_json.py -p VOY -o data/episodes/voy.json
```

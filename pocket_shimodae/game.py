from common import *
from .objects import *

class PoshimoGame:
  """
  The base Poshimo game object
  This handles initialization of the game along with
  almost all of the functionality exposed to the cog
  
  Methods
  ----

  `register_trainer(user_id)`
    Register a new trainer to the database
  
  `get_all_trainers()`
    Returns a list of all trainers in the database

  `get_trainer(discord_id)`
    Get trainer details by Discord ID

  """
  def __init__(self, cog):
    self.cog = cog
    self.world = PoshimoWorld() 
    self.active_battles = [] 
    self.starter_poshimo = [
      Poshimo(name="Worf"), 
      Poshimo(name="Jim Shimoda"), 
      Poshimo(name="Captain Picard")
    ]
    
  def find_in_world(self, location_name) -> PoshimoLocation:
    """ find a location in the world based on the location name """
    return self.world.locations[location_name]

  def get_all_trainers(self) -> list:
    """ get a list of discord ids from all the registered trainers """
    with AgimusDB() as query:
      sql = "SELECT users.discord_id, poshimo_trainers.id FROM poshimo_trainers LEFT JOIN users ON poshimo_trainers.user_id = users.id"
      query.execute(sql)
      all_trainers = [int(i[0]) for i in query.fetchall()]
    return all_trainers

  def get_trainer(self, discord_id) -> PoshimoTrainer:
    """
    Get a PoshimoTrainer object from the database based on discord ID
    """
    logger.info(f"Attempting lookup on poshimo trainer {discord_id}...")
    with AgimusDB(dictionary=True) as query:
      sql = '''SELECT *, poshimo_trainers.id as trainer_id FROM poshimo_trainers 
            LEFT JOIN users ON poshimo_trainers.user_id = users.id 
            WHERE users.discord_id = %s'''
      vals = (discord_id,)
      query.execute(sql, vals)
      trainer_data = query.fetchone()
      logger.info(f"Trainer found!")
    return PoshimoTrainer(trainer_id=trainer_data["trainer_id"])

  def register_trainer(self, user_id) -> PoshimoTrainer:
    """
    Register a new trainer to the database

    Parameters
    ----
    `user_id`:`int`
      the users ID from the `users` table

    Returns
    ----
    PoshimoTrainer
    """
    logger.info(f"Attempting to register new trainer {user_id}")
    with AgimusDB() as query:
      sql = "INSERT INTO poshimo_trainers (user_id) VALUES (%s)"
      vals = (user_id,)    
      query.execute(sql, vals)
      trainer_id = query.lastrowid
      if trainer_id:
        logger.info(f"Success! new trainer ID: {trainer_id}")
    return PoshimoTrainer(trainer_id)

  def test_add_poshimo(self, discord_id):
    trainer = self.get_trainer(discord_id)
    trainer.add_poshimo(random.choice(self.starter_poshimo))
    trainer.wins += 5
    trainer.scarves += 69

  def test_unlock_loc(self, discord_id, location_name):
    trainer = self.get_trainer(discord_id)
    trainer_locs = trainer.locations_unlocked
    trainer_locs.add(location_name)
    trainer.locations_unlocked = trainer_locs

  def test_give_poshimo(self, discord_id):
    trainer = self.get_trainer(discord_id)
    sample_poshimo = Poshimo(name="Worf")
    new_poshimo = trainer.add_poshimo(sample_poshimo)
    return new_poshimo

  def test_clear_db(self):
    with AgimusDB() as query:
      sql = "DELETE FROM poshimo_trainers WHERE id > 0;"
      query.execute(sql)
    self.cog.all_trainers = []
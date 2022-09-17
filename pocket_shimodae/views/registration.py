""" 
this contains all the views for registering a player and choosing their first poshimo
the StarterChosen view will actually do the registration, everything else is just UI
"""
from common import *
from ..ui import PoshimoView, Confirmation
from ..objects import Poshimo

class Welcome(PoshimoView):
  """ first message a new user sees """
  def __init__(self, cog):
    super().__init__(cog)
    self.embeds = [
      discord.Embed(
        title=f"You heard about this game going around the ship...",
        description="""
        INTRO TEXT WILL GO HERE THIS ISNT REAL
        Supposedly it's a holodeck program that's intensely immersive, addicting, and nobody knows who wrote it. Everyone's been talking about it, or at least they were a few days ago, but now the ship seems oddly quiet.\n
        Having never been briefed on the dangers of alien games or even Ktarians, you naively decide to try it for yourself: you punch in your access codes, and step into the holodeck.\n
        The doors quickly close behind you, and a familiar voice crackles from the intercom:\n
        "WELCOME TO POCKET SHIMODAE, FOOLISH MORTAL!\n
        The doors are locked, and of course the safeties are off. You must play the game and prove your worth as a Poshimo Trainer before I will consider letting you escape."\n\n
        It seems AGIMUS has trapped you in here until you have finished the game or the game finishes you...
        """
      )
    ]

class StarterPoshimoConfirmation(Confirmation):
  """ confirmation for picking your starter poshimo """
  def __init__(self, cog, choice:Poshimo):
    super().__init__(cog, choice)
    self.embeds = [
      discord.Embed(
        title=f"You chose {choice.name}. Are you sure?",
        description="You can't undo this, but you can always find the other ones later!"
      )
    ]
    
  async def cancel_callback(self, button, interaction:discord.Interaction):
    """ cancel the starter poshimo choice, nothing happens """
    await interaction.response.edit_message(content="Give it a good hard think and come back when you're ready! (Type `/ps start` to try again)", view=None, embed=None)
    self.stop()
    
  async def confirm_callback(self, button, interaction:discord.Interaction):
    """ confirm the poshimo choice, register the player! """
    view = StarterChosen(self.cog, self.choice, get_user(interaction.user.id))
    await interaction.response.edit_message(view=view, embeds=view.embeds)


class StarterPages(PoshimoView):
  """ The pages for choosing a starter poshimo """
  def __init__(self, cog):
    super().__init__(cog)
    self.starters = self.game.starter_poshimo
    self.welcome_embed = Welcome(self.cog).get_embed()
    
    for s in self.starters:
      embed = discord.Embed(
        title="Choose your starter Poshimo", 
        description=f"**{s.name}**", 
        fields=[
          discord.EmbedField(name="Types", value=f"{' and '.join([s.name for s in s.types])}"), 
          discord.EmbedField(name="Moves", value=f"{', '.join([m.display_name for m in s.move_list if m is not None])}")]
      )
      self.pages.append(pages.Page(
        embeds=[self.welcome_embed, embed]
      ))
    
    self.paginator = pages.Paginator(
      pages=self.get_pages(),
      custom_view=self
    )

  @discord.ui.button(label="Choose this one", emoji="🟢", style=discord.ButtonStyle.blurple, row=2)
  async def button_callback(self, button, interaction:discord.Interaction):
    """ a single button to confirm their selection, depending on which page they were on """
    pchoice = self.starters[self.paginator.current_page] # page corresponds to the starter poshimo
    view = StarterPoshimoConfirmation(self.cog, pchoice)
    await interaction.response.edit_message(view=view, embeds=view.embeds)

class StarterChosen(PoshimoView):
  """ 
  when you have successfully chosen a starter 
  - this actually registers the player and their poshimo to the DB
  - not really a view after all, is it? heh heh heh
  """
  def __init__(self, cog, choice:Poshimo, user):
    super().__init__(cog)
    # ~ THE MAGIC HAPPENS HERE ~ #
    self.trainer = self.game.register_trainer(user["id"]) # register player
    self.poshimo = self.trainer.add_poshimo(choice, True) # give them this poshimo as their active poshimo
    self.cog.all_trainers = self.game.get_all_trainers() # add em to the big list
    self.embeds = [
      discord.Embed(
        title=f"Congratulations TRAINER #{self.trainer.id}! You have selected your first poshimo: **{self.poshimo.name}**! Poshimo ID: {self.poshimo.id}", 
        description="Live long, and may the force prosper within you."
      )
    ]
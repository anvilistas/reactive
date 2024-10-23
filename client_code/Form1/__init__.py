from ._anvil_designer import Form1Template
from anvil import *
from ..main import reactive_class, render_effect

@reactive_class
class Form1(Form1Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        self.items = {"foo": 42}

        # Any code you write here will run before the form opens.

    @render_effect
    def label(self):
        self.label_1.text = self.items["foo"]

    def button_1_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.items["foo"] += 1

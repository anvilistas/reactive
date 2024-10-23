from ._anvil_designer import Form1Template
from anvil import *
from ..main import reactive_class, render_effect

@reactive_class
class Form1(Form1Template):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        self.items = {}

        # Any code you write here will run before the form opens.

    @render_effect
    def label(self):
        print()
        print("RENDER EFFECT 1")
        self.label_1.text = self.items.get("foo", 42)

    @render_effect
    def contains(self):
        print()
        print("RENDER EFFECT 2")
        self.label_1_copy.text = "foo" in self.items

    def button_1_click(self, **event_args):
        """This method is called when the button is clicked"""
        print()
        print("BUTTON CLICKED")
        v = self.items.get("foo", 42) + 1
        print()
        print("SETTING TO VALUE ", v)
        self.items["foo"] = v

    def button_2_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.items.clear()

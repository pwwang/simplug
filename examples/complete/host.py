import itertools

from simplug import Simplug
# make sure specs are imported
from . import hookspecs
from . import lib

simplug = Simplug('complete-example')
simplug.register(lib)

condiments_tray = {"pickled walnuts": 13, "steak sauce": 4, "mushy peas": 2}

class EggsellentCook:
    FAVORITE_INGREDIENTS = ("egg", "egg", "egg")

    def __init__(self, hooks):
        self.hooks = hooks
        self.ingredients = None

    def add_ingredients(self):
        results = self.hooks.add_ingredients(
            ingredients=self.FAVORITE_INGREDIENTS
        )
        my_ingredients = list(self.FAVORITE_INGREDIENTS)
        # Each hooks returns a list - so we chain this list of lists
        other_ingredients = list(itertools.chain(*results))
        self.ingredients = my_ingredients + other_ingredients

    def serve_the_food(self):
        condiment_comments = self.hooks.prep_condiments(
            condiments=condiments_tray
        )
        print(f"Your food. Enjoy some {', '.join(self.ingredients)}")
        print(f"Some condiments? We have {', '.join(condiments_tray.keys())}")
        if any(condiment_comments):
            print("\n".join(condiment_comments))

def main():
    simplug.register(__name__.replace('.host', '.plugin'))
    cook = EggsellentCook(simplug.hooks)
    cook.add_ingredients()
    cook.serve_the_food()

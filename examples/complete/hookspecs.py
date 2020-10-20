from simplug import Simplug

simplug = Simplug('complete-example')

@simplug.spec
def add_ingredients(ingredients: tuple):
    """Have a look at the ingredients and offer your own.

    :param ingredients: the ingredients, don't touch them!
    :return: a list of ingredients
    """

@simplug.spec
def prep_condiments(condiments: dict):
    """Reorganize the condiments tray to your heart's content.

    :param condiments: some sauces and stuff
    :return: a witty comment about your activity
    """

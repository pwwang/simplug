from simplug import Simplug

simplug = Simplug('complete-example')
priority = -99 # make sure this plugin executes first

@simplug.impl
def add_ingredients(ingredients):
    spices = ["salt", "pepper"]
    you_can_never_have_enough_eggs = ["egg", "egg"]
    ingredients = spices + you_can_never_have_enough_eggs
    return ingredients

@simplug.impl
def prep_condiments(condiments):
    condiments["mint sauce"] = 1

from simplug import Simplug

simplug = Simplug('complete-example')

@simplug.impl
def add_ingredients(ingredients):
    """Here the caller expects us to return a list."""
    if "egg" in ingredients:
        spam = ["lovely spam", "wonderous spam"]
    else:
        spam = ["splendiferous spam", "magnificent spam"]
    return spam


@simplug.impl
def prep_condiments(condiments):
    """Here the caller passes a mutable object, so we mess with it directly."""
    try:
        del condiments["steak sauce"]
    except KeyError:
        pass
    condiments["spam sauce"] = 42
    return "Now this is what I call a condiments tray!"

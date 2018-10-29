import os
import json

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.routing import Map, Rule

from backend.Recipe import Recipe, Content
from backend.Ingredient import Ingredient
from backend.User import User
from backend.DBHandler import DBHandler
from backend.DBEntry import FoodEncoder, Allergy, IngredientCategory
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure db access and JSON encoder
db = DBHandler()
enc = FoodEncoder(indent = 2)


@app.route("/")
@login_required
def index():
    # <TODO>
    """Show user's home page"""

    kwargs = {}

    return render_template("index.html", **kwargs)


@app.route("/constructor")
@login_required
def constructor():
    """Show constructor main page"""

    return render_template("constructor.html", rows=False)


@app.route("/constructor/allergies", methods=["GET", "POST"])
@login_required
def constructor_allergies():
    """Show allergies constructor page for GET.
    Write new allergies to DB for POST.
    """
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        rows = db.get_rows("allergies")
        return render_template("allergies.html", rows=rows)

    # User reached route via POST (as by submitting a form via POST)
    name = request.form.get("name")
    allergy = Allergy(name)

    try:
        result = db.write(allergy)
    except:
        result = False

    if result:
        flash("Allergy added successfully!")
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("constructor/allergies")


@app.route("/constructor/ingredient_categories", methods=["GET", "POST"])
@login_required
def constructor_ingredient_categories():
    # <TODO>
    """Show ingredient category constructor page for GET.
    Write new ingredient category to DB for POST.
    """
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        rows = db.get_rows("ingredient_categories")
        return render_template("ingredient_categories.html", rows=rows)

    # User reached route via POST (as by submitting a form via POST)
    name = request.form.get("name")
    ing_category = IngredientCategory(name)
    try:
        result = db.write(ing_category)
    except:
        result = False

    if result:
        flash("Ingredient category added successfully!")
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("constructor/ingredient_categories")


@app.route("/constructor/ingredients", methods=["GET", "POST"])
@login_required
def constructor_ingredients():
    """Show ingredients constructor page for GET.
    Write new ingredients to DB for POST.
    """
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        rows = db.get_rows("ingredients")
        categories = db.get_rows("ingredient_categories")
        allergies = db.get_rows("allergies")

        allergens = db.get_rows("allergens")
        ingredient_allergies = {}
        for a in allergens:
            ingredient_id = a["ingredient_id"]
            allergy_id = a["allergy_id"]
            allergy_name = db.fetch_allergy(allergy_id).name
            try:
                ingredient_allergies[ingredient_id].append(allergy_name)
            except:
                ingredient_allergies[ingredient_id] = [allergy_name]

        return render_template("ingredients.html", rows=rows, categories=categories, allergies=allergies, ingredient_allergies=ingredient_allergies)

    # User reached route via POST (as by submitting a form via POST)
    name = request.form.get("name")
    category_id = request.form.get("category_id")
    category = db.fetch_ingredient_category(category_id)
    allergy_ids = request.form.getlist("allergies")
    allergies = set()
    for db_id in allergy_ids:
        allergies.add(db.fetch_allergy(db_id))

    ingredient = Ingredient(name, category, None, allergies)
    try:
        result = db.write(ingredient)
    except:
        result = False

    if result:
        flash("Ingredient added successfully!")
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("constructor/ingredients")


@app.route("/constructor/recipes", methods=["GET", "POST"])
@login_required
def constructor_recipes():
    """Show recipes constructor page for GET.
    Write new recipes to DB for POST.
    """
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        # get recipe list for the table
        rows = db.get_rows("recipes")
        ingredients = db.get_rows("ingredients")

        # contruct a list of tuple of contents of each recipe for the table
        contents = db.get_rows("recipe_contents")
        recipe_contents = {}
        for c in contents:
            recipe_id = c["recipe_id"]
            ingredient_id = c["ingredient_id"]
            ingredient_name = db.fetch_ingredient(ingredient_id).name

            amount = c["amount"]
            if not amount:
                amount = ""

            units = c["units"]
            if not units:
                units = ""
            content = (ingredient_name, amount, units)
            try:
                recipe_contents[recipe_id].append(content)
            except:
                recipe_contents[recipe_id] = [content]

        return render_template("recipes.html", rows=rows, ingredients=ingredients, recipe_contents=recipe_contents)

    # User reached route via POST (as by submitting a form via POST)
    name = request.form.get("name")
    instructions = request.form.get("instructions")

    contents = set()
    form_contents = json.loads(request.form.get("contents"))
    for fc in form_contents:
        ingredient = db.fetch_ingredient(fc["ingredient_id"])

        try:
            amount = float(fc["amount"])
        except:
            amount = 0

        units = fc["units"]
        if fc["units"] == "":
            units = None

        contents.add(Content(ingredient, amount, units))

    recipe = Recipe(name, None, contents, instructions)
    try:
        result = db.write(recipe)
    except:
        result = False

    if result:
        flash("Recipe added successfully!")
    else:
        flash("Something went wrong :(", category="danger")

    return redirect("constructor/recipes")


@app.route("/login", methods=["GET", "POST"])
def login():
    # <TODO>
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        name = request.form.get("username")
        if not name:
            return apology("must provide username", 403)

        # Ensure password was submitted
        password = request.form.get("password")
        if not password:
            return apology("must provide password", 403)

        # Ensure user exists and querry for credentials
        user = db.fetch_user(name=name)
        if not user:
            return apology("user does not exist", 403)

        # Ensure password is correct
        if not check_password_hash(user.password_hash, password):
            return apology("invalid username or password", 403)

        # Remember which user has logged in
        session["user_id"] = user.db_id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        name = request.form.get("username")
        if not name:
            return apology("must provide username")

        # Querry database and check if the username is already taken
        if db.exists("users", name=name):
            return apology("this username is already taken")

        # Ensure both passwords were submitted
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password or not confirmation:
            return apology("must provide password and its confirmation")

        # Ensure passwords match
        if not password == confirmation:
            return apology("passwords do not match")

        # Store a user entry in the database
        pass_hash = generate_password_hash(password)
        user = User(name, pass_hash)
        user.db_id = db.write(user)

        if not user.db_id:
            return apology("something went wrong :'(")

        # Log the user in
        return login()

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Forget any user_id
        session.clear()

        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

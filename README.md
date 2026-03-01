# AllerEasy

AllerEasy is a free, open-source web application built to help UK and EU catering businesses manage allergen, calorie, and nutritional information in line with current food labelling regulations - including Natasha's Law and EU FIC Regulation No. 1169/2011.

It provides a simple staff dashboard for managing dishes and uploading menus in bulk, alongside a clean customer-facing menu that displays allergen and nutritional information clearly. The app is fully brandable so it matches your business.

This project is offered freely to the hospitality industry. The goal is simply to help businesses stay compliant and keep diners safer.

**Live demo / website:** [www.allereasy.co.uk](https://www.allereasy.co.uk)

---

## What the App Does

- Tracks all 14 EU/UK regulated allergens per dish
- Records calories, carbs, protein, fat, saturated fat, sugar, fibre, and salt
- Allows bulk menu upload via CSV or JSON, with automatic allergen column mapping
- Displays a branded, customer-facing menu showing allergens and dietary information
- Lets you customise colours, fonts, and logos per menu type
- Keeps a full audit trail of every change - who changed what, when, and why
- Manages staff user accounts with different permission levels
- Flags dishes as vegan, vegetarian, active, inactive, or archived

---

## Before You Begin

This guide covers two paths:

- **Option A - Local setup** for testing on your own computer (no cost, no internet required)
- **Option B - Live deployment** to make the app accessible online to your team and customers

You do not need to be a developer to follow these steps, but you will need to be comfortable using a terminal (also called Command Prompt or PowerShell on Windows, Terminal on Mac/Linux).

---

## What You Will Need

- A computer running Windows, Mac, or Linux
- An internet connection (for downloading tools and, if deploying live, for the hosting setup)
- Approximately 30–60 minutes

---

## Step 1 - Install Python

Python is the programming language the app is written in.

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download the latest version for your operating system
3. During installation on Windows, **make sure you tick "Add Python to PATH"** before clicking Install

To check it installed correctly, open your terminal and type:

```
python --version
```

You should see something like `Python 3.12.0`. Any version 3.10 or above is fine.

---

## Step 2 - Download the AllerEasy Code

If you have Git installed:

```
git clone https://github.com/yourusername/allereasy.git
cd allereasy
```

If you do not have Git, click the green **Code** button on the GitHub page and choose **Download ZIP**. Extract the zip file somewhere you can find it, then open your terminal and navigate into that folder:

```
cd path/to/allereasy
```

---

## Step 3 - Create a Virtual Environment

A virtual environment keeps AllerEasy's dependencies separate from anything else on your computer. This prevents conflicts and is good practice.

```
python -m venv venv
```

Now activate it:

- **Mac / Linux:**
  ```
  source venv/bin/activate
  ```
- **Windows:**
  ```
  venv\Scripts\activate
  ```

You should see `(venv)` appear at the start of your terminal prompt. Keep this terminal window open - you will need to activate the virtual environment again any time you come back to work on this.

---

## Step 4 - Install the App's Dependencies

With your virtual environment active, run:

```
pip install -r requirements.txt
```

This downloads all the libraries the app needs. It may take a minute or two.

---

## Step 5 - Create Your Configuration File

The app needs a configuration file to know things like your secret key and which database to use. Create a file called `env.py` in the root of the project folder (the same folder that contains `manage.py`).

Open any text editor, paste the following, and save it as `env.py`:

```python
import os

os.environ["SECRET_KEY"] = "change-this-to-a-long-random-string"
os.environ["DATABASE_URL"] = "sqlite:///db.sqlite3"
```

**Generating a secret key:** The secret key should be a long, random string. You can generate one by running this in your terminal (with the virtual environment active):

```
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Copy the output and replace `change-this-to-a-long-random-string` with it.

> **Important:** Never share your `env.py` file or commit it to GitHub. It is already listed in `.gitignore` so Git will ignore it automatically.

---

## Step 6 - Configure Debug Mode

Open the file `allergens/settings.py` in a text editor (Notepad on Windows is fine).

Find this block near the top of the file:

```python
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
```

**For local testing**, leave `DEBUG = True` as it is - this gives helpful error messages while you are setting things up.

**Before going live**, you must change this line to:

```python
DEBUG = False
```

When `DEBUG = True`, Django shows detailed error pages that contain information about your code. This is useful for development but a security risk on a live site. Always set it to `False` before deploying.

In the same file, find the `ALLOWED_HOSTS` line:

```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.herokuapp.com']
```

Before going live, add your own domain here:

```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.herokuapp.com', 'yourdomain.com', 'www.yourdomain.com']
```

---

## Option A - Running Locally with SQLite

SQLite is a simple database that stores everything in a single file on your computer. It requires no installation and is perfect for testing or small single-machine use.

Your `env.py` is already pointed at SQLite if you used the example above:

```python
os.environ["DATABASE_URL"] = "sqlite:///db.sqlite3"
```

Now open `allergens/settings.py` and find the `DATABASES` section. It looks like this:

```python
DATABASES = {
    #'default': {
    #   'ENGINE': 'django.db.backends.sqlite3',
    #   'NAME': BASE_DIR / 'db.sqlite3',
    #}

    'default': dj_database_url.parse(os.environ.get("DATABASE_URL"))
}
```

To use SQLite explicitly, you can uncomment the SQLite block and comment out the `dj_database_url` line. Change it to look like this:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

    # 'default': dj_database_url.parse(os.environ.get("DATABASE_URL"))
}
```

Alternatively, you can leave it as-is - the `DATABASE_URL` in your `env.py` already points to SQLite and will work without changing `settings.py`.

### A1 - Set Up the Database

Run this command to create the database tables:

```
python manage.py migrate
```

### A2 - Load the Starter Data

This loads the default allergens, categories, and menu types:

```
python manage.py loaddata dash/templates/dash/csv_json/allergens.json
python manage.py loaddata dash/templates/dash/csv_json/categories.json
python manage.py loaddata dash/templates/dash/csv_json/menu_types.json
python manage.py loaddata dash/templates/dash/csv_json/subcategories.json
```

### A3 - Create Your Admin Account

```
python manage.py createsuperuser
```

You will be asked to choose a username, email address, and password.

### A4 - Collect Static Files

```
python manage.py collectstatic
```

Type `yes` if prompted.

### A5 - Start the App

```
python manage.py runserver
```

Open a browser and go to `http://127.0.0.1:8000`. You should see the AllerEasy home page.

- Staff dashboard: `http://127.0.0.1:8000/secure/`
- Django admin panel: `http://127.0.0.1:8000/super-secret-admin/`

---

## Option B - Deploying Live with Heroku and PostgreSQL

Heroku is a hosting platform that lets you run your app on the internet without managing a server. The instructions below use Heroku with a PostgreSQL database - a robust database suited to live production use.

### What You Will Need

- A free [Heroku account](https://signup.heroku.com/)
- The [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed - follow the instructions on that page for your operating system
- [Git](https://git-scm.com/downloads) installed on your computer

### B1 - Update Your Settings for Production

Before deploying, open `allergens/settings.py` and make the following changes:

**1. Set DEBUG to False:**
```python
DEBUG = False
```

**2. Add your Heroku domain to ALLOWED_HOSTS:**
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.herokuapp.com', 'your-app-name.herokuapp.com']
```

**3. Confirm the DATABASES section uses `dj_database_url` (not the SQLite block):**
```python
DATABASES = {
    'default': dj_database_url.parse(os.environ.get("DATABASE_URL"))
}
```

If you had uncommented the SQLite block in Option A, re-comment it out now and uncomment the `dj_database_url` line.

### B2 - Initialise a Git Repository

If you downloaded the code as a ZIP rather than using `git clone`, you need to set up Git now. In your terminal, from the project folder:

```
git init
git add .
git commit -m "Initial commit"
```

If you cloned the repository, your Git history is already in place.

### B3 - Log In to Heroku

```
heroku login
```

A browser window will open. Log in there, then return to your terminal.

### B4 - Create a Heroku App

```
heroku create your-app-name
```

Replace `your-app-name` with something unique - for example `allereasy-smiths-bistro`. Heroku will confirm the URL your app will live at, something like `https://your-app-name.herokuapp.com`.

### B5 - Add a PostgreSQL Database

```
heroku addons:create heroku-postgresql:essential-0
```

This creates a PostgreSQL database and automatically sets the `DATABASE_URL` environment variable in Heroku for you. You do not need to do anything else for the database connection.

> **Note:** The `essential-0` plan has a small monthly cost. Check the current price at [https://www.heroku.com/pricing](https://www.heroku.com/pricing). If you prefer a free database, see the section below on using an external database provider.

### B6 - Set Your Secret Key on Heroku

```
heroku config:set SECRET_KEY="paste-your-secret-key-here"
```

Use the same secret key you generated for your local `env.py`.

### B7 - Deploy the Code

Push your code to Heroku:

```
git push heroku main
```

If your branch is called `master` rather than `main`, use:

```
git push heroku master
```

Heroku will install the dependencies and start the app automatically. This takes a minute or two.

### B8 - Set Up the Live Database

Run migrations on the live database:

```
heroku run python manage.py migrate
```

Load the starter data:

```
heroku run python manage.py loaddata dash/templates/dash/csv_json/allergens.json
heroku run python manage.py loaddata dash/templates/dash/csv_json/categories.json
heroku run python manage.py loaddata dash/templates/dash/csv_json/menu_types.json
heroku run python manage.py loaddata dash/templates/dash/csv_json/subcategories.json
```

Create your admin account:

```
heroku run python manage.py createsuperuser
```

### B9 - Open the App

```
heroku open
```

Your app is now live. The staff dashboard is at `/secure/` and the Django admin panel at `/super-secret-admin/`.

---

## Using a Free Cloud Database (Neon or Supabase)

If you want a free PostgreSQL database instead of Heroku's paid addon, both [Neon](https://neon.tech) and [Supabase](https://supabase.com) offer free tiers that work well with AllerEasy.

1. Sign up for a free account at either provider
2. Create a new project/database
3. Copy the connection string - it will look something like:
   ```
   postgres://username:password@host:5432/dbname
   ```
4. Set it on Heroku instead of using the Heroku addon:
   ```
   heroku config:set DATABASE_URL="postgres://username:password@host:5432/dbname"
   ```

Then continue from step B7 onwards as normal.

---

## Using a Different Cloud Host

AllerEasy is not tied to Heroku and can run on any platform that supports Python and PostgreSQL. Popular alternatives include:

- **Railway** ([railway.app](https://railway.app)) - simple to use, generous free tier
- **Render** ([render.com](https://render.com)) - free tier available, very similar workflow to Heroku
- **PythonAnywhere** ([pythonanywhere.com](https://www.pythonanywhere.com)) - beginner-friendly, good for small apps

For any of these, the general process is the same: set `SECRET_KEY` and `DATABASE_URL` as environment variables, deploy your code, then run `migrate`, `loaddata`, and `createsuperuser` on the remote server.

---

## URL Structure

| URL | What it is |
|-----|------------|
| `/` | Customer-facing menu home |
| `/secure/` | Staff dashboard (login required) |
| `/super-secret-admin/` | Django admin panel (superuser only) |

---

## Importing Menu Data

From the staff dashboard, go to **Import Data**. You can upload a CSV or JSON file of your existing menu.

**CSV:** Include columns for dish name, category, allergens, and kcal. The built-in allergen converter will automatically map common column names (e.g. `wheat`, `barley`, `rye`, `gluten`) to the correct regulated allergen group.

**JSON:** A sample file `dishes_upload.json` is included in the project root showing the expected data structure.

---

## Branding

From the staff dashboard, go to **Branding**. You can configure each menu type independently with:

- Primary, secondary, accent, text, and background colours (as hex codes, e.g. `#ff6600`)
- Font family (as a CSS font stack)
- Logo and background image (via a URL to a hosted image)

Changes apply to the customer-facing menu immediately.

---

## Project Structure

```
allereasy/
├── allergens/        # Project settings, URLs, server config
├── dash/             # Staff dashboard (login, dishes, users, imports, branding, audit log)
├── menus/            # Customer-facing menu views and templates
├── static/           # CSS, JS, and image assets
├── dishes_upload.json  # Sample JSON import file
├── manage.py
├── requirements.txt
└── Procfile          # Tells Heroku how to start the app
```

---

## Compliance Notice

AllerEasy is designed to support compliance with:

- **UK:** The Food Information to Consumers Regulations, including Natasha's Law (October 2021)
- **EU:** EU Food Information for Consumers Regulation (No. 1169/2011)

This app is a management tool to assist with compliance. It does not constitute legal advice. Businesses remain responsible for the accuracy of the allergen and nutritional information they publish.

---

## Contributing

Contributions are very welcome. If you find a bug, have a feature idea, or want to improve the documentation, please open an issue or submit a pull request. For significant changes, it is worth opening an issue first to discuss what you have in mind.

---

## Licence

This project is released under the MIT Licence - you are free to use, modify, and distribute it. See the `LICENSE` file for details.

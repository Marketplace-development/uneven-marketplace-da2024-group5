[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/YzI0i2Iu)

To understand the general concept of our project and our taxonomy/business plan, including the platform ontology, the platform prototype (Figma), our database (using supabase) ... you can find all the details in the marketplace_ideation.txt.

However, there are a few aspects we wanted to clarify further:

We chose not to differentiate between providers and customers on our platform. Doing so would have required developing separate interfaces for the website, which would add complexity. Additionally, we felt it didn’t make sense to make this distinction, as anyone can be both a provider and a customer. Therefore, we opted for a single class: the User class.

We did not implement trust and safety features like ID verification, badges, or in-app reporting, as these were not the core focus of our project. Our priority was to ensure that all other aspects of the platform function smoothly and effectively. We did however implement account safety by allowing users to log in securely with a password

We considered adding a revenue stream through advertisements, but implementing this proved to be quite complex. Instead, we chose to focus solely on generating revenue through commissions, allowing us to keep our platform simple and streamlined.

To make sure our platform runs: we followed the following steps
    # Create and activate virtual environment
    python -m venv venv        # or python3 on macOS
    source venv/bin/activate   # macOS
    venv\Scripts\activate      # Windows

    # Install dependencies
    pip install -r requirements.txt

    # Set Flask environment variables
    export FLASK_APP=run.py    # macOS
    set FLASK_APP=run.py       # Windows (Command Prompt)
    $env:FLASK_APP="run.py"    # Windows (PowerShell)

    # Run the application
    flask run

To develop and ensure the smooth operation of our platform, we rely on a combination of robust tools and technologies, including:
    The use of Flask for...

    The use of Flask-SQLAlchemy for...

    The use of psycopg2-binary for...

    The use of requests for...

    The use of Bootstrap for...

    The use of Geonames for...

    The use of Jinja for...

    The use of chatGPT for...

    -->     we didn't use Flask-Migrate because...

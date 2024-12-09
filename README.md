[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/YzI0i2Iu)

To understand the overall concept of our project, including our taxonomy, business plan, platform ontology, prototype (Figma), and database (using Supabase) ... please refer to the marketplace_ideation.txt file for all the details.

For more details on how everything works and how we developed and programmed the platform (e.g the thought proces of our platform, the algorithm we used, the tools and technologies used ...), please refer to the extra_info.txt file.

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

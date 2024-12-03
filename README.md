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

To power/develop our platform and deliver a seamless user experience/smooth operation of our platform, we rely on a combination of tools and technologies , including:
    
    The use of Flask: Flask is the heart of our platform, providing a lightweight yet powerful framework for developing the website. It handles routing, server-side logic, and the integration of various components, ensuring smooth and efficient operation.

    The use of Flask-SQLAlchemy: Flask-SQLAlchemy is the bridge between our Python code and the database. It simplifies the management of user data, travel itineraries, and reviews with a clean and intuitive way to interact with the database.

    The use of buckets in our database on supabase: Supabase buckets provide a secure and scalable solution for storing and managing files like PDFs on our platform. Each PDF is uploaded to a designated bucket and linked to a specific listing in the database, with the file’s URL securely stored and hidden until a successful purchase is made. Buyers can only access their purchased files through a "Download" button, enabled after transaction verification. Supabase policies and backend validation ensure strict access control, allowing only authenticated and eligible users to retrieve the files. This setup ensures seamless integration, robust security, and a user-friendly experience for both sellers and buyers.

    The use of psycopg2-binary: Psycopg2-binary is the key to our connection with the PostgreSQL database. It ensures secure, reliable, and efficient storage and retrieval of essential platform data, forming the backbone of data-driven features.

    The use of Bootstrap: Bootstrap ensures the platform looks great on all devices with its responsive, modern design components. From buttons to layouts, it provides a polished user interface that enhances navigation and usability.

    The use of flash en flash errors: In our project, Flash messages are used to provide users with instant feedback about their actions, such as successful form submissions, account updates, or errors during interactions. They help enhance the user experience by delivering clear and concise notifications directly on the interface.

    Flash Errors are specifically employed to alert users about issues, such as invalid input, failed authentication, or incomplete forms. This ensures users understand what went wrong and can take corrective action. Together, these tools improve communication and interactivity, making the platform more intuitive and user-friendly.

    The use of Jinja: Jinja powers the dynamic generation of HTML pages by merging server-side logic with templates. It ensures users see customized content like tailored travel suggestions and filtered search results in a visually appealing format.

    The use of HTMl and CSS code: HTML structures the content of our platform, while CSS transforms it into a visually compelling and user-friendly design. Together, they ensure the platform is intuitive, responsive, and engaging.

    The use of requests: The requests library enables seamless communication with external APIs, such as fetching live data like weather updates, currency exchange rates, or travel insights. This enriches the platform with dynamic, real-time content. This Python library enables the platform to send HTTP requests to external APIs (like Geonames --> see further)

    The use of the external GeoNames API: We integrated GeoNames into our platform to enhance location-based features by providing accurate, real-time geographic data. This includes offering location suggestions through an auto-completion feature, which helps users enter valid places easily and without typos. By leveraging GeoNames, we can validate that locations follow the correct format and actually exist, ensuring data integrity. 
    --> however: Since we are working with a free API, GeoNames imposes a limitation of 1,000 requests per hour. This means that every time a user types more than three letters, a request is sent to the GeoNames API to retrieve location suggestions. Thus, with this limitation, you need to be mindful of how often requests are made to avoid exceeding the cap, especially during periods of high user activity. 
    --> Additionally, integrating this could enrich the platform with valuable insights such as coordinates, landmarks, and regional details, enhancing features like itinerary mapping and personalized recommendations. Although the data could be useful in an algorithm, we decided to implement a different one instead. We believed that the alternative algorithm, which filters based on user preferences, would add more value to our platform and better align with its goals.

    The use of chatGPT: We used ChatGPT to assist with the overall programming of our platform, serving as a valuable resource throughout the development process. ChatGPT helped us troubleshoot errors, provided coding solutions, and guided us on how to implement features we envisioned but weren’t sure how to execute.  --> Whether it was debugging complex issues, offering suggestions for optimizing the platform, or explaining how to integrate various technologies, ChatGPT played a key role in enhancing the development workflow. Its ability to generate code snippets, offer explanations, and suggest best practices allowed us to move forward with confidence and streamline the creation of a functional and efficient platform.

    -->     We chose not to use Flask-Migrate during the development of our platform due to concerns about the potential risks associated with unintended mistakes that could negatively impact our database. Flask-Migrate is a powerful tool for handling database migrations, but it also comes with the possibility of making errors, especially when applying changes or rolling back migrations. In a development environment where constant changes were being made to the database schema, we wanted to avoid scenarios where an accidental migration could delete or corrupt important data, or cause other issues that could halt our progress. Instead, we opted for a more manual approach to database management to maintain greater control over the changes we made, minimizing the chance of any serious setbacks. By doing so, we could carefully test each change and ensure the stability and integrity of our data throughout the development process.

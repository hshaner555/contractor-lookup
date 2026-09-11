# QUESTIONS

* The app initializes the database on startup.
    * It shouldn't initialize the database - it should die if it's not setup
* What is the review_queue for?
* What writes to the import_log?
*

# ARCHITECTURE

* REST API (run this on lambda? EC2?)
    * /search
    * /contractors/<id>
* RDBMS (currently sqlite, needs to be a real one)
    * contractors
    * credentials (belongs_to contractors)
* Scrapers of the government sites
    * Python scripts
    * Bexley is a PDF - need downloading on a schedule

# NEEDS

* React app
    * Frontend to REST API
    * Mobile-friendly
* Put data into a real database
* Deployment to a real place
* Development environment
    * Human
    * AI Agent
* Run the importers on a schedule
    * Need to review the review queue regularly
    * This needs a front-end
    * Schedule an export every weekend
        * We will get to know their update schedules
* Admin interface
    * Needs authn/z
    * Can be React-only without needing mobile
    * Can edit any record
    * Work with the review_queue
    * Query the import_log
* Scrapers need:
    * Needs running on a schedule
        * Download Bexley PDF
    * Handling to find out when the target has changed

# IMMEDIATE TODO

* Install:
    * Python3.12
    * gh (github CLI)
* Import this into github under hshaner private org
    * Repo: contractor_lookup
    * Directory: api/
        * This is where:
            * app.py
    * Directory: lib/
        * This is where:
            * models.py
            * normalize.py
            * db.py
            * init_db.py
    * Directory: sources/
        * This is where:
            * ingest.py
            * bexley_pdf.py
            * columbus_acela.py
            * franklin_smartgov.py
            * ohio_oclib.py
    * Directory: docs/
        * This is where all the documentation goes
    * Every directory will have a README.md to explain:
        * What's in that directory
        * Why it's there
        * What
* Export the API spec into a markdown file in docs/
* Create a React app in the same repository
    * Directory: frontend/
    * From the API spec
    * Required to be mobile-first
        * After go-live, put it into app stores
* Identify the first government data to put forward
    * Use one we already have without needing playwright
* DevX setup
    * How does development get done?
    * How can I do development with you and we don't step on each other's feet?
    * How are the work items identified and tracked?
    * How are changes managed so that they are reviewed?
    * How are deployments made?
    * Consider Docker Compose setup
        * Containers for api and database
        * npx start for frontend and admin_frontend
* Write the administrative interface frontend in admin_frontend/
    * Add the necessary elements to the API
        * /login will respond when not logged in
        * All other admin API endpoints return 404 if not logged in
        * Authn initially with username/password
            * Hook in Google instead after go-live
        * This will modify the API spec in docs/
    * Review the import_log
        * This is where we find issues
        * Should imports notify on success/failure? By email?
    * Review the review_queue
        * Ability to edit items, merge them, or reject them
    * Edit existing rows
        * Need a log of edits
* Add throttling with setting cookies
    * This is done in the background when the React app loads
    * First request is 302 with a cookie
    * Every source IP gets 2 live cookies at a time
* Deploy this to a production site
    * We will use Render (render.com)
        * It will handle React, Python, MySQL database, and cronjobs (for updating)
* Purchase and configure domain
    * This is your go-live moment

# AFTER GO-LIVE

* Figure out how to get the word out
* Add easy data sources
* Run it for 2-3 weeks
    * Handle any errors
    * Make sure the imports are happening properly
* Add more difficult data sources

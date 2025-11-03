# Lexsy AI Document Assistant

An intelligent document automation system that uses the Google Gemini AI to help users complete legal documents. It turns static `.docx` files into an interactive, conversational chat interface.

## 🚀 Live Website

**[https://lexsy-assignment-213433359152.europe-west1.run.app](https://lexsy-assignment-213433359152.europe-west1.run.app)**

*(Note: The live site is hosted on Cloud Run and may be scaled down to zero. The first load may take a minute to start.)*

##  workflow

1.  **Upload:** A user visits the homepage and uploads a `.docx` document template.
2.  **Preview & Process:** The app saves the file to Google Cloud Storage (GCS) and immediately generates a text-only preview. In the background, it finds all placeholders (e.g., `[Company Name]`) in both paragraphs and tables.
3.  **AI Generation:** For each placeholder found, the app calls the Google Gemini API, providing the placeholder and its surrounding context. The AI generates a simple, conversational question and an explanation.
4.  **Fill:** The user is taken to a chat interface. The app asks the AI-generated questions one by one, while a live preview of the document highlights the specific placeholder being filled.
5.  **Download:** After all questions are answered, the app generates the final, completed `.docx` file, saves it to GCS, and provides the user with a secure, temporary download link.

## ⚙️ Technology Stack

* **Backend:** Python 3.10, Flask
* **WSGI Server:** Gunicorn
* **AI:** Google Gemini API (`google-generativeai`)
* **Document Processing:** `python-docx`
* **Frontend:** HTML5, CSS3, Vanilla JavaScript (Fetch API)
* **Cloud & Deployment:** Docker, Google Cloud Run, Google Cloud Build
* **Storage & Secrets:** Google Cloud Storage (GCS), Google Secret Manager

## 📋 Prerequisites

Before you can run this project locally, you must have the following:

* **Docker Desktop** (Installed and running)
* **Google Cloud SDK (`gcloud`)** (Installed and authenticated)
* **A Google Cloud Project** (with billing enabled)
* **A Google Cloud Storage (GCS) Bucket**
* **A Google Gemini API Key**
* **A Google Cloud Service Account JSON key file**

### 2. Create Service Account Key

1.  In your Google Cloud Project, go to **"IAM & Admin"** > **"Service Accounts"**.
2.  Find your project's **Compute Engine default service account** (or create a new one).
3.  Go to the **"Keys"** tab > **"Add Key"** > **"Create new key"**.
4.  Select **"JSON"** and click **"Create"**.
5.  A JSON file will download. Rename it to `service-account-key.json` and place it in the root of this project (`D:\LexsyAssignment`).

### 3. Configure Environment Variables

Create a file named `.env` in the root of the project. This file stores your secret keys and is **ignored by Git**.

**`.env` file:**
```
# .env
# Your Gemini API key
GEMINI_API_KEY=your_gemini_api_key_goes_here

# The name of your GCS bucket
GCS_BUCKET_NAME=your-gcs-bucket-name

# This path tells the app to look for the key inside the container
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
```
**Important:** Your `.gitignore` file is already set up to ignore `.env` and `*.json` files to keep your keys safe.

## 🏃 Running the Application (Local)

### 1. Build the Docker Image
From your PowerShell terminal in the project's root folder, run:

```bash
docker build -t lexsy-app .
```

### 2. Run the Docker Container
This command runs the app, maps port 8080, and securely mounts your local `.env` file and `service-account-key.json` into the container.

```powershell
docker run -p 8080:8080 --env-file .env -v "${pwd}\service-account-key.json:/app/service-account-key.json:ro" lexsy-app
```
The app will now be running at `http://localhost:8080`.

## 🚀 Deployment to Google Cloud Run
This project is configured for automated, continuous deployment from GitHub.

1.  **Push to GitHub:** Ensure your repository has all the project files, including `Dockerfile`, `requirements.txt`, `run.py`, `config.py`, and the `app/` folder.
2.  **Create GCS Bucket:** In the Google Cloud console, create a new Google Cloud Storage bucket (e.g., `lexsy-app-storage-chandra`).
3.  **Create API Key Secret:**
    * Go to **"Secret Manager"** in the Google Cloud console.
    * Click **"+ Create Secret"**.
    * **Name:** `lexsy-gemini-key`
    * **Secret value:** Paste your Gemini API key.
    * Click **"Create secret"**.
4.  **Connect Cloud Run to GitHub:**
    * Go to **"Cloud Run"** and click **"Create Service"**.
    * Select **"Continuously deploy new revisions from a source repository"**.
    * Click **"Set up with Cloud Build"** and connect to your `Lexsy_Assignment` GitHub repository.
    * In the "Build Settings" section:
        * **Branch:** `main`
        * **Build Type:** `Dockerfile`
        * **Dockerfile location:** `Dockerfile`
5.  **Configure the Service:**
    * **Service name:** `lexsy-assignment` (or your choice)
    * **Authentication:** Select **"Allow unauthenticated invocations"**.
    * Expand **"Container(s), Volumes, Networking, Security"**.
    * Go to the **"Variables & Secrets"** tab.
    * **Add Variable:**
        * **Name:** `GCS_BUCKET_NAME`
        * **Value:** `your-gcs-bucket-name`
    * **Add Secret:**
        * Click the **"Secret"** sub-tab.
        * **Name:** `GEMINI_API_KEY`
        * **Secret:** `lexsy-gemini-key`
        * **Version:** `latest`
6.  **Set Service Account Permissions (CRITICAL):**
    * Go to the **"Security"** tab and copy the **Service account** email.
    * Click **"Deploy"**. The first build may fail while permissions are set.
    * Go to **"IAM & Admin"** > **"IAM"**.
    * Click **"Grant Access"**.
    * **New principals:** Paste the service account email.
    * **Add Role:** `Secret Manager Secret Accessor`
    * **Add Role:** `Storage Object Admin`
    * Click **Save**.
7.  **Trigger a New Build:** Push any small change to your GitHub repo (e.g., add a space to `README.md`) to trigger a new, successful build.

## 📁 Project Structure

```
Lexsy_Assignment/
├── app/
│   ├── __init__.py         # Initializes the Flask app and Gemini
│   ├── routes.py         # All Flask @app.route endpoints
│   ├── helpers.py        # Gemini API call logic
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── index.html    # Homepage (upload/preview)
│       ├── chat.html     # Chat/Live preview page
│       └── download.html # Download page
│
├── .venv/                # Virtual environment (ignored)
├── completed/            # Completed documents (local, ignored)
├── uploads/              # Uploaded templates (local, ignored)
│
├── .env                  # Local environment keys (ignored)
├── service-account-key.json # GCS credentials (ignored)
│
├── config.py             # Loads configuration from environment
├── run.py                # Entry point to run the application
├── Dockerfile            # Instructions to build the container
├── requirements.txt      # Python dependencies
├── .gitignore
├── .dockerignore
└── README.md             # This file
```

## 📬 Contact
Created by ChandraSekhar Katipalli
* [GitHub](https://github.com/ChandraSekharKatipalli)

### 1. Clone the Repository

```bash
git clone [https://github.com/ChandraSekharKatipalli/Lexsy_Assignment.git](https://github.com/ChandraSekharKatipalli/Lexsy_Assignment.git)
cd Lexsy_Assignment

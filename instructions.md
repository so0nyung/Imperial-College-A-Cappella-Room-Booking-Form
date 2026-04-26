# RoomBook IC

A web UI for automating room bookings at Imperial College London via Selenium.

---

## Project structure

```
roombooking/
├── main.py              ← FastAPI backend + Selenium logic
├── templates/
│   └── index.html       ← Frontend (served by FastAPI)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Install dependencies

```bash
pip install fastapi uvicorn selenium
```

### 2. Install ChromeDriver

Make sure `chromedriver` is installed and matches your Chrome version.

- **Mac (Homebrew):** `brew install --cask chromedriver`
- **Ubuntu/Debian:** `sudo apt install chromium-driver`
- **Windows:** Download from https://chromedriver.chromium.org/downloads

### 3. ⚠️ Adapt the Selenium selectors in `main.py`

Open `main.py` and find the `submit_form()` function. You'll need to:

1. Replace `TARGET_URL` with the actual booking website URL.
2. Replace the `By.ID` selectors (e.g. `"first_name"`, `"venue"`) with the correct
   selectors from the booking form.

   **How to find them:**
   - Open the booking website in Chrome
   - Right-click a field → Inspect
   - Look for `id="..."`, `name="..."`, or a unique CSS class
   - Update each `driver.find_element(By.ID, "...")` accordingly

---

## Running the app

```bash
cd roombooking
uvicorn main:app --reload
```

Then open your browser at: **http://localhost:8000**

---

## How it works

1. Fill in the **date range** and up to **3 booking instances** (group, day, venue, time).
2. Personal details (name, job, email) are set once in the **Settings** page.
3. Hit **Submit bookings** — FastAPI kicks off a background Selenium job.
4. The receipt modal shows **live progress** as each instance is processed.
5. Once done, hit **Download PDF** to save a formatted receipt.

### API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Serves the frontend |
| `/api/submit` | POST | Starts a Selenium booking job, returns `job_id` |
| `/api/status/{job_id}` | GET | Poll for job progress and results |
| `/api/preview-dates` | GET | Returns dates that would be booked for a given range + weekday |

---

## Notes

- The Selenium job runs **headlessly** in the background.
- Jobs are stored in memory — restarting the server clears them.
- To support multiple simultaneous users, swap the background task for a proper
  task queue (e.g. Celery + Redis).

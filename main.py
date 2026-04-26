from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import asyncio
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
from pathlib import Path
BASE_DIR = Path(__file__).parent


app = FastAPI(title="RoomBook IC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ── In-memory job store ─────────────────────────────────────────────────────
jobs: dict[str, dict] = {}


# ── Pydantic models ─────────────────────────────────────────────────────────
class Instance(BaseModel):
    group_name: str
    day: str        # e.g. "Thursday"
    venue: str
    start_time: str # e.g. "14:00"
    end_time: str   # e.g. "16:00"


class BookingRequest(BaseModel):
    start_date: str     # DD/MM/YYYY
    end_date: str       # DD/MM/YYYY
    instances: List[Instance]
    # Submitter details (from Settings page)
    first_name: str
    last_name: str
    job: str
    email: str
    target_url: str


# ── Date helper (mirrors your original get_dates_for_weekday) ───────────────
DAY_MAP = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6
}

def get_dates_for_weekday(start_date, end_date, weekday):
    # Convert strings to date objects
    start = datetime.strptime(start_date, "%d/%m/%Y").date()
    end = datetime.strptime(end_date, "%d/%m/%Y").date()

    # Map weekday name to number (Monday=0, Sunday=6)
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
    }
    target = weekdays[weekday.lower()]

    # Find first matching weekday
    current = start + timedelta((target - start.weekday()) % 7)

    # Collect all matching dates
    dates = []
    while current <= end:
        dates.append(current)
        current += timedelta(days=7)

    formatted_dates = [d.strftime("%d/%m/%Y") for d in dates]
    return(formatted_dates)


# ── Selenium form submission (adapt selectors to match the actual website) ──
def submitForm(driver, info_array, target_url):
    if len(info_array) != 12:
        print("Error: Incorrect information amount submitted. Please Re-Enter")
    else:
        driver.get(target_url)
        time.sleep(20)
        # force focus
        driver.find_element(By.TAG_NAME, "body").click()
        time.sleep(2)
        # Fill in basic information
        driver.switch_to.active_element.send_keys(Keys.TAB)
        driver.switch_to.active_element.send_keys(info_array[0])
        driver.switch_to.active_element.send_keys(Keys.TAB)
        driver.switch_to.active_element.send_keys(info_array[1])
        driver.switch_to.active_element.send_keys(Keys.TAB)
        driver.switch_to.active_element.send_keys(info_array[2])
        driver.switch_to.active_element.send_keys(Keys.TAB)
        driver.switch_to.active_element.send_keys(info_array[3])
        driver.switch_to.active_element.send_keys(Keys.TAB)
        driver.switch_to.active_element.send_keys(info_array[4])
        driver.switch_to.active_element.send_keys(Keys.TAB)
        
        # Select "Room Booking" Option
        for _ in range(4):
            driver.switch_to.active_element.send_keys(Keys.ARROW_DOWN)
        driver.switch_to.active_element.send_keys(Keys.TAB)
        # Fill in room details
        driver.switch_to.active_element.send_keys(info_array[5])
        driver.switch_to.active_element.send_keys(Keys.TAB)
        driver.switch_to.active_element.send_keys(info_array[6])
        driver.switch_to.active_element.send_keys(Keys.TAB)
        driver.switch_to.active_element.send_keys(info_array[7])
        driver.switch_to.active_element.send_keys(Keys.TAB)
        driver.switch_to.active_element.send_keys(info_array[8])
        driver.switch_to.active_element.send_keys(Keys.TAB)
        driver.switch_to.active_element.send_keys(info_array[9])
        driver.switch_to.active_element.send_keys(Keys.TAB)
        driver.switch_to.active_element.send_keys(info_array[10])
        driver.switch_to.active_element.send_keys(Keys.TAB)
        driver.switch_to.active_element.send_keys(info_array[11])
        
        for _ in range(2):
            driver.switch_to.active_element.send_keys(Keys.TAB)
        # Final Enter Button - DO NOT UNCOMMENT UNLESS WE HAVE TO BOOK ROOMS
        driver.switch_to.active_element.send_keys(Keys.ENTER)

        time.sleep(2)


def run_bookings(job_id: str, req: BookingRequest):
    """Runs all Selenium bookings for a job, updating status as it goes."""
    jobs[job_id]["status"] = "running"
    results = []

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=options)

        for inst in req.instances:
            dates = get_dates_for_weekday(req.start_date, req.end_date, inst.day)
            inst_results = []

            for date in dates:
                info_array = [
                    "A Cappella",
                    req.first_name,
                    req.last_name,
                    req.job,
                    req.email,
                    inst.group_name + " Rehearsal",
                    inst.group_name + " Rehearsal",
                    inst.venue,
                    date,
                    inst.start_time,
                    inst.end_time,
                    "14",
                ]
                try:
                    submitForm(driver, info_array, req.target_url)
                    inst_results.append({"date": date, "success": True})
                except Exception as e:
                    inst_results.append({"date": date, "success": False, "error": str(e)})

            results.append({
                "group": inst.group_name,
                "day": inst.day,
                "venue": inst.venue,
                "start_time": inst.start_time,
                "end_time": inst.end_time,
                "dates": inst_results,
            })

            # Update progress after each instance
            jobs[job_id]["results"] = results

        driver.quit()
        jobs[job_id]["status"] = "done"

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


# ── API Routes ───────────────────────────────────────────────────────────────
@app.post("/api/submit")
async def submit_booking(req: BookingRequest, background_tasks: BackgroundTasks):
    """Kicks off Selenium booking job in the background. Returns a job_id."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued", "results": [], "request": req.dict()}
    background_tasks.add_task(run_bookings, job_id, req)
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Poll this endpoint to get job progress."""
    job = jobs.get(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    return job


@app.get("/api/preview-dates")
async def preview_dates(start: str, end: str, day: str):
    """Returns the list of dates that would be booked — useful for UI preview."""
    try:
        dates = get_dates_for_weekday(start, end, day)
        return {"dates": dates, "count": len(dates)}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.get("/", response_class=HTMLResponse)
async def root():
    with open(BASE_DIR / "templates" / "index.html") as f:
        return f.read()

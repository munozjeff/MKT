
import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Paths
BASE_DIR = os.getcwd()
CHROMEDRIVER_PATH = os.path.join(BASE_DIR, "chromedriver.exe")
TEST_PROFILE_DIR = os.path.join(BASE_DIR, "data", "perfiles", "test_debug_profile")

print(f"Driver Path: {CHROMEDRIVER_PATH}")
if not os.path.exists(CHROMEDRIVER_PATH):
    print("ERROR: chromedriver.exe not found!")
    sys.exit(1)

def test_launch(name, options):
    print(f"\n--- Testing: {name} ---")
    driver = None
    try:
        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        print("SUCCESS: Browser launched.")
        driver.get("https://www.google.com")
        print("SUCCESS: Navigated to Google.")
        time.sleep(2)
    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                print("Browser closed.")
            except:
                pass

# 1. Basic Launch
opts1 = Options()
opts1.add_argument("--disable-gpu")
test_launch("Basic (Only disable-gpu)", opts1)

# 2. With Sandbox/DevShm flags (The ones in production)
opts2 = Options()
opts2.add_argument("--disable-gpu")
opts2.add_argument("--no-sandbox")
opts2.add_argument("--disable-dev-shm-usage")
test_launch("Prod Flags (No Sandbox/DevShm)", opts2)

# 3. With Profile (New)
opts3 = Options()
opts3.add_argument("--disable-gpu")
opts3.add_argument(f"user-data-dir={TEST_PROFILE_DIR}")
test_launch("With New Profile", opts3)

# 4. With Automation Exclusion (Stealth)
opts4 = Options()
opts4.add_argument("--disable-gpu")
opts4.add_argument("--disable-blink-features=AutomationControlled")
opts4.add_experimental_option("excludeSwitches", ["enable-automation"])
test_launch("Stealth Mode", opts4)


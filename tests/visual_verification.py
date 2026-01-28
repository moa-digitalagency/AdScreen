import os
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright

def run_verification():
    # Setup Env
    db_path = os.path.abspath("test.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["INIT_DB_MODE"] = "false" # Create superadmin
    env["SUPERADMIN_EMAIL"] = "admin@example.com"
    env["SUPERADMIN_PASSWORD"] = "password123"
    env["SESSION_SECRET"] = "secret"

    # 1. Run init_db.py
    print("Running init_db.py...")
    result = subprocess.run([sys.executable, "init_db.py"], env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print("init_db.py failed:")
        print(result.stdout)
        print(result.stderr)
        return
    print("init_db.py success.")
    print(result.stdout)

    # 2. Start App
    print("Starting app...")
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(10) # Wait for startup

    # 3. Playwright
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            # Check Homepage
            print("Checking Homepage...")
            try:
                response = page.goto("http://localhost:5000/")
                if response:
                    print(f"Homepage status: {response.status}")
                page.screenshot(path="homepage.png")

                if response and response.status != 200:
                    print("Homepage failed!")
            except Exception as e:
                print(f"Homepage access error: {e}")

            # Check Login
            print("Checking Login...")
            page.goto("http://localhost:5000/login")
            page.screenshot(path="login_page.png")

            page.fill("input[name='email']", "admin@example.com")
            page.fill("input[name='password']", "password123")
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")

            print(f"Post-login URL: {page.url}")
            page.screenshot(path="dashboard.png")

            if "/admin" in page.url or "/org" in page.url or "/dashboard" in page.url:
                 print("Login successful.")
            else:
                 print("Login might have failed or redirected elsewhere.")

            browser.close()
    except Exception as e:
        print(f"Verification failed: {e}")
    finally:
        process.terminate()
        try:
            out, err = process.communicate(timeout=5)
            if err:
                print("App stderr:", err.decode())
            # print("App stdout:", out.decode())
        except subprocess.TimeoutExpired:
            process.kill()

if __name__ == "__main__":
    run_verification()

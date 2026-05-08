import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


APP_URL = os.getenv("APP_URL", "http://localhost:9090")


@pytest.fixture
def driver():
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(10)

    yield browser

    browser.quit()


def submit_form(driver, action, fields):
    driver.get(APP_URL + "/signup")

    script = """
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = arguments[0];

    const fields = arguments[1];

    for (const key in fields) {
        const input = document.createElement('input');
        input.name = key;
        input.value = fields[key];
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
    """

    driver.execute_script(script, APP_URL + action, fields)
    time.sleep(1)


def create_user_and_login(driver):
    username = "user_" + str(int(time.time() * 1000))
    password = "Test12345"

    submit_form(driver, "/signup", {
        "username": username,
        "password": password
    })

    submit_form(driver, "/login", {
        "username": username,
        "password": password
    })

    return username, password


def test_01_signup_page_opens(driver):
    driver.get(APP_URL + "/signup")
    assert "signup" in driver.current_url.lower() or "sign" in driver.page_source.lower()


def test_02_login_page_opens(driver):
    driver.get(APP_URL + "/login")
    assert "login" in driver.current_url.lower() or "login" in driver.page_source.lower()


def test_03_home_redirects_to_signup_when_not_logged_in(driver):
    driver.get(APP_URL + "/")
    time.sleep(1)
    assert "signup" in driver.current_url.lower()


def test_04_user_can_signup(driver):
    username = "signup_" + str(int(time.time() * 1000))

    submit_form(driver, "/signup", {
        "username": username,
        "password": "Test12345"
    })

    assert "login" in driver.current_url.lower()


def test_05_valid_user_can_login(driver):
    username, password = create_user_and_login(driver)

    driver.get(APP_URL + "/")
    page = driver.page_source.lower()

    assert "idea" in page or "thought" in page or "logout" in page


def test_06_invalid_login_shows_error_or_stays_on_login(driver):
    submit_form(driver, "/login", {
        "username": "wrong_user",
        "password": "wrong_password"
    })

    page = driver.page_source.lower()
    assert "invalid" in page or "login" in driver.current_url.lower()


def test_07_logged_in_user_can_access_home(driver):
    create_user_and_login(driver)

    driver.get(APP_URL + "/")
    page = driver.page_source.lower()

    assert "idea" in page or "thought" in page


def test_08_user_can_create_idea_post(driver):
    create_user_and_login(driver)

    submit_form(driver, "/post", {
        "type": "Idea",
        "title": "Automation Idea",
        "content": "This idea was created using Selenium."
    })

    page = driver.page_source.lower()
    assert "automation idea" in page or "selenium" in page


def test_09_user_can_create_thought_post(driver):
    create_user_and_login(driver)

    submit_form(driver, "/post", {
        "type": "Thought",
        "title": "Automation Thought",
        "content": "This thought was created using Selenium."
    })

    page = driver.page_source.lower()
    assert "automation thought" in page or "selenium" in page


def test_10_unauthorized_post_redirects_to_login(driver):
    submit_form(driver, "/post", {
        "type": "Idea",
        "title": "Unauthorized Idea",
        "content": "This should not be created."
    })

    assert "login" in driver.current_url.lower()


def test_11_profile_page_opens_for_logged_in_user(driver):
    username, password = create_user_and_login(driver)

    driver.get(APP_URL + f"/profile/{username}")

    page = driver.page_source.lower()
    assert username.lower() in page or "profile" in page


def test_12_user_can_update_profile(driver):
    username, password = create_user_and_login(driver)

    submit_form(driver, f"/profile/{username}", {
        "full_name": "Selenium User",
        "bio": "Profile updated by Selenium test."
    })

    page = driver.page_source.lower()
    assert "selenium user" in page or "profile updated" in page


def test_13_logout_redirects_to_signup(driver):
    create_user_and_login(driver)

    driver.get(APP_URL + "/logout")
    time.sleep(1)

    assert "signup" in driver.current_url.lower()


def test_14_logged_out_user_cannot_access_profile(driver):
    driver.get(APP_URL + "/profile/someuser")
    time.sleep(1)

    assert "login" in driver.current_url.lower()


def test_15_app_does_not_show_server_error(driver):
    driver.get(APP_URL + "/signup")

    page = driver.page_source.lower()

    assert "500 internal server error" not in page
    assert "traceback" not in page
    assert "application error" not in page
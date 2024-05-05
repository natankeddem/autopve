# from nicegui.testing.conftest import *
from collections.abc import Generator
import os
import pytest
from nicegui.testing import Screen
from nicegui.testing.conftest import (
    capabilities,  # noqa: F401
    driver,  # noqa: F401
    remove_all_screenshots,  # noqa: F401
    reset_globals,  # noqa: F401
    DOWNLOAD_DIR,
)
from selenium import webdriver


@pytest.fixture
def chrome_options(chrome_options: webdriver.ChromeOptions) -> webdriver.ChromeOptions:
    """Configure the Chrome driver options."""
    chrome_options.add_argument("disable-dev-shm-using")
    chrome_options.add_argument("no-sandbox")
    chrome_options.add_argument("headless")
    # check if we are running on GitHub Actions
    if "GITHUB_ACTIONS" in os.environ:
        chrome_options.add_argument("disable-gpu")
    else:
        chrome_options.add_argument("--use-gl=angle")
    chrome_options.add_argument("window-size=1920x1080")
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(DOWNLOAD_DIR),
            "download.prompt_for_download": False,  # To auto download the file
            "download.directory_upgrade": True,
        },
    )
    if "CHROME_BINARY_LOCATION" in os.environ:
        chrome_options.binary_location = os.environ["CHROME_BINARY_LOCATION"]
    return chrome_options


@pytest.fixture
def screen(
    driver: webdriver.Chrome,  # noqa: F811
    request: pytest.FixtureRequest,
    caplog: pytest.LogCaptureFixture,
) -> Generator[Screen, None, None]:
    """Create a new Screen instance."""
    screen_ = Screen(driver, caplog)
    yield screen_
    if screen_.is_open:
        screen_.shot(request.node.name)
    screen_.stop_server()

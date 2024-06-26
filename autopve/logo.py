from nicegui import ui  # type: ignore
import logging

logger = logging.getLogger(__name__)

logo = """
<svg width="50px" height="50px" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="24" cy="24" r="9" fill="#666666" stroke="#E97451" stroke-width="4"/>
<circle r="3" transform="matrix(-1 0 0 1 24 24)" fill="white"/>
<path d="M9 14C9 14 16.5 2.49997 29.5 6.99998C42.5 11.5 42 24.5 42 24.5" stroke="#E97451" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M39 34C39 34 33 45 19.5 41.5C6 38 6 24 6 24" stroke="#E97451" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M42 8V24" stroke="#E97451" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M6 24L6 40" stroke="#E97451" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def show():
    ui.html(logo)

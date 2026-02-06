# core/tools/date_time_tools.py
from datetime import datetime
from langchain_core.tools import tool
import logging


@tool
def get_current_datetime() -> str:
    """
    Returns the current date and time.

    USE QUANDO: O usuário perguntar "que dia é hoje", "hora atual", "data de hoje".
    Útil para cálculos relativos de tempo (ex: "há quantos dias...").
    """
    logging.info("Getting current date and time.")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


date_time_tools = [
    get_current_datetime,
]

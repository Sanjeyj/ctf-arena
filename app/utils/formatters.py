# Date and score formatters
def format_datetime(dt_str):
    if not dt_str:
        return "—"
    return dt_str[:19].replace("T", " ")

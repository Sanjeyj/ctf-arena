# Basic validation placeholders for user input and flags
def validate_flag_format(flag):
    return flag.startswith("FLAG{") and flag.endswith("}")

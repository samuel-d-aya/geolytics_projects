import re
from typing import Any, Dict, List


def parse_js_object_to_dict(js_string: str) -> Dict[str, Any]:

    def preprocess_js_string(s: str) -> str:

        # Remove outer braces and whitespace
        s = s.strip()
        if s.startswith("{") and s.endswith("}"):
            s = s[1:-1]

        # Split by commas, but be careful with nested structures and quoted strings
        tokens = []
        current_token = ""
        in_quotes = False
        quote_char = None
        brace_depth = 0
        escape_next = False

        for char in s:
            if escape_next:
                current_token += char
                escape_next = False
                continue

            if char == "\\":
                current_token += char
                escape_next = True
                continue

            if not in_quotes:
                if char in ['"', "'"]:
                    in_quotes = True
                    quote_char = char
                    current_token += char
                elif char == "{":
                    brace_depth += 1
                    current_token += char
                elif char == "}":
                    brace_depth -= 1
                    current_token += char
                elif char == "," and brace_depth == 0:
                    tokens.append(current_token.strip())
                    current_token = ""
                    continue
                else:
                    current_token += char
            else:
                if char == quote_char and not escape_next:
                    in_quotes = False
                    quote_char = None
                current_token += char

        if current_token.strip():
            tokens.append(current_token.strip())

        return tokens

    def parse_value(value: str) -> Any:
        """Parse a JavaScript value into Python equivalent"""
        value = value.strip()

        # Handle null/undefined/variable references
        if value in ["null", "undefined"]:
            return None

        # Handle boolean values
        if value == "true":
            return True
        if value == "false":
            return False

        # Handle numbers
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Handle strings (both single and double quoted)
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            # Remove quotes and handle escape sequences
            unquoted = value[1:-1]
            # Handle Unicode escape sequences
            unquoted = unquoted.encode().decode("unicode_escape")
            return unquoted

        # Handle nested objects
        if value.startswith("{") and value.endswith("}"):
            return parse_js_object_to_dict(value)

        # If all else fails, treat as string
        return value

    try:
        tokens = preprocess_js_string(js_string)
        result = {}

        for token in tokens:
            if ":" not in token:
                continue

            # Split on first colon only
            key_part, value_part = token.split(":", 1)
            key = key_part.strip()
            value = value_part.strip()

            # Remove quotes from key if present
            if (key.startswith('"') and key.endswith('"')) or (
                key.startswith("'") and key.endswith("'")
            ):
                key = key[1:-1]

            result[key] = parse_value(value)

        return result

    except Exception as e:
        raise ValueError(f"Failed to parse JavaScript object: {e}")


def parse_business_hours(hours_list: List[Any]) -> Dict[str, Any]:

    # Day mappings from Spanish to English abbreviations
    spanish_days = {
        "domingo": "Sun",
        "lunes": "Mon",
        "martes": "Tue",
        "miércoles": "Wed",
        "miercoles": "Wed",  # Without accent
        "jueves": "Thu",
        "viernes": "Fri",
        "sábado": "Sat",
        "sabado": "Sat",  # Without accent
    }

    # All days in order
    all_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def convert_to_24h(time_str: str) -> str:
        """Convert 12-hour format to 24-hour format"""
        time_str = time_str.strip()

        # Handle AM/PM
        if "AM" in time_str.upper():
            time_part = time_str.upper().replace("AM", "").strip()
            hour, minute = time_part.split(":")
            hour = int(hour)
            if hour == 12:
                hour = 0
            return f"{hour:02d}:{minute}"

        elif "PM" in time_str.upper():
            time_part = time_str.upper().replace("PM", "").strip()
            hour, minute = time_part.split(":")
            hour = int(hour)
            if hour != 12:
                hour += 12
            return f"{hour:02d}:{minute}"

        # If no AM/PM specified, assume it's already in 24h format
        return time_str

    def parse_time_range(time_range: str) -> str:
        """Parse a time range like '6:00 AM - 11:00 PM' to '06:00-23:00'"""
        # Clean up the string
        time_range = time_range.replace("\xa0", " ").strip()

        # Extract time range pattern
        time_pattern = (
            r"(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*-\s*(\d{1,2}:\d{2}\s*(?:AM|PM)?)"
        )
        match = re.search(time_pattern, time_range, re.IGNORECASE)

        if match:
            start_time = convert_to_24h(match.group(1))
            end_time = convert_to_24h(match.group(2))
            return f"{start_time}-{end_time}"

        return "Closed"

    def get_day_range(day_text: str) -> List[str]:
        """Extract day range from Spanish text"""
        day_text = day_text.lower()
        # Clean up encoding issues
        day_text = day_text.replace("ã¡", "á").replace("ã³", "ó")

        # Handle "domingo a sábado" (Sunday to Saturday - entire week)
        if "domingo a s" in day_text:  # Handles sábado/sabado with encoding issues
            return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        # Handle "domingo a jueves" (Sunday to Thursday)
        if "domingo a jueves" in day_text:
            return ["Sun", "Mon", "Tue", "Wed", "Thu"]

        # Handle "viernes y sábado" (Friday and Saturday)
        if "viernes y s" in day_text:  # Handles sábado/sabado
            return ["Fri", "Sat"]

        # Handle "lunes a viernes" (Monday to Friday)
        if "lunes a viernes" in day_text:
            return ["Mon", "Tue", "Wed", "Thu", "Fri"]

        # Handle individual days
        for spanish_day, english_day in spanish_days.items():
            if spanish_day in day_text:
                return [english_day]

        return []

    # Initialize result dictionary
    result = {}

    # Process each line in the hours list
    for line in hours_list:
        line = line.strip()

        # Skip lines that start with ">" (these are usually service hours)
        if line.startswith(">"):
            continue

        # Parse the line for day information and hours
        days = get_day_range(line)
        hours = parse_time_range(line)

        # Apply hours to all days in the range
        for day in days:
            result[day] = hours

    # Ensure all days are represented (set missing days to "Closed")
    for day in all_days:
        if day not in result:
            result[day] = None

    return {"opening_hours": result}

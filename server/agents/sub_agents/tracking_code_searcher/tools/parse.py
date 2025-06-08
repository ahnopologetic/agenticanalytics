import re
import csv


def parse_tracking_code(input_file: str, output_csv: str) -> None:
    """
    Parses a file with multi-language code snippets to extract tracking event details.
    """
    event_pattern = re.compile(
        r"^(?P<filepath>[^:]+):\d+:\d+:(?P<codeline>.*"
        r'(?:track|log_event|send_event|capture|gtag|logEvent|enqueue|trackEvent|firebase\.analytics\(\)\.logEvent|ga\(\'send\', \'event\'|amplitude\.logEvent|Amplitude\.instance\(\)\.logEvent|mixpanel\.track_pageview|rudderanalytics\.track|Rudder\.sharedInstance\(\)\.track|RudderClient\.getInstance\(\)\.track|mp\.logEvent|MParticle\.sharedInstance\(\)\.logEvent|MParticle\.logEvent|posthog\.capture|PHGPostHog\.shared\(\)\?\.capture|pendo\.track|PendoManager\.shared\(\)\.track|heap\.track|Heap\.track|snowplow|trackUnstructured|SPSnowplow\.track|Snowplow\.track)\s*[\(\{]\s*["\'](?P<event_name>[^"\']+)["\']'
        r"(?:[,\s]*?(?P<properties>\{.*\}|\[.*\]|map\[.*\]|analytics\..*\{|properties:))?"  # More flexible properties capture
        r".*)"
    )

    with open(input_file, "r") as f_in, open(output_csv, "w", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(
            [
                "Event Name",
                "Property Key",
                "Property Description",
                "Property Type",
                "Location",
                "Context (Raw Code Line)",
            ]
        )

        processed_locations = set()  # Avoid duplicate entries for the same event call

        for line in f_in:
            match = event_pattern.match(line.strip())
            if not match:
                continue

            data = match.groupdict()
            location_key = f"{data.get('filepath')}:{data.get('codeline')}"
            if location_key in processed_locations:
                continue
            processed_locations.add(location_key)

            filepath = data.get("filepath")
            event_name = data.get("event_name")
            properties_str = data.get("properties")
            full_code_context = data.get("codeline", "").strip()

            if not properties_str:
                writer.writerow(
                    [event_name, "N/A", "N/A", "N/A", filepath, full_code_context]
                )
                continue

            # Try to parse flat JS/Python-style objects: {key: value, ...} or {"key": value, ...}
            # This is a best-effort and will not handle nested/complex objects.
            prop_pattern = re.compile(r'([\w\'\"]+)\s*:\s*([\w\'\"\.\-\[\]\{\}\(\)]+)')
            # Remove wrapping braces if present
            prop_str = properties_str.strip()
            if prop_str.startswith("{") and prop_str.endswith("}"):
                prop_str = prop_str[1:-1]
            parsed_any = False
            for m in prop_pattern.finditer(prop_str):
                key = m.group(1).strip('"\'')
                value = m.group(2).strip()
                # Infer type
                if value.startswith('"') or value.startswith("'"):
                    prop_type = "string"
                elif value in ["true", "false", "True", "False"]:
                    prop_type = "bool"
                elif re.match(r'^-?\d+(\.\d+)?$', value):
                    prop_type = "number"
                else:
                    prop_type = "unknown"
                writer.writerow([
                    event_name,
                    key,
                    "N/A",  # No description available
                    prop_type,
                    filepath,
                    full_code_context,
                ])
                parsed_any = True
            if not parsed_any:
                # Fallback: could not parse properties
                writer.writerow(
                    [
                        event_name,
                        "NEEDS_MANUAL_REVIEW",
                        "Properties detected but could not be parsed automatically. Please review the code.",
                        "object/struct/dict",
                        filepath,
                        full_code_context,
                    ]
                )


if __name__ == "__main__":
    parse_tracking_code("potential_tracking_calls.txt", "tracking_events.csv")
    print("Parsing complete. Results ready for review in tracking_events.csv")

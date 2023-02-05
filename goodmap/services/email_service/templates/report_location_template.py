def report_location_email_template(location_data):
    return f"""
    Hi there,
    A location has been reported: "{location_data["name"]}" of type "{location_data["type"]}" at coordinates {location_data["location"]}
    """
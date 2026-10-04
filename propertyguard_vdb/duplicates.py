def check_duplicates(title: str, location: str, owner: str) -> dict:
    sample_registry = [
        {"id": "PG-1042", "title": "3-Bedroom House, Block C", "location": "Gulberg, Lahore", "owner": "Ahmed Raza"},
        {"id": "PG-2098", "title": "Commercial Plot 500 Sq Yd", "location": "Clifton, Karachi", "owner": "Tariq Khan"},
        {"id": "PG-3310", "title": "1 Kanal Luxury Villa", "location": "DHA Phase 6, Lahore", "owner": "Suleman Butt"}
    ]
    for item in sample_registry:
        if item["title"].lower() in title.lower() or item["location"].lower() in location.lower():
            return {
                "found_duplicate": True,
                "similarity_score": 87.5,
                "matched_id": item["id"],
                "note": f"High similarity (87.5%) with listing {item['id']} in {item['location']}."
            }
    return {
        "found_duplicate": False,
        "similarity_score": 12.0,
        "matched_id": None,
        "note": "No duplicate listing found in registry archive."
    }
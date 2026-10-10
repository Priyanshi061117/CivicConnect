
def assign_priority(description: str) -> dict:
    """Assign an explainable priority based on complaint keywords."""

    text = " ".join(description.lower().split())

    critical_keywords = [
        "gas leak",
        "live wire",
        "electric shock",
        "building collapse",
        "open manhole",
        "exposed electrical wire",
    ]

    high_keywords = [
        "fire",
        "flooding",
        "burst water pipe",
        "sewage overflow",
        "fallen electric pole",
        "major road accident",
        "water contamination",
    ]

    medium_keywords = [
        "water leakage",
        "pothole",
        "streetlight",
        "garbage",
        "drain blockage",
        "broken road",
        "overflowing dustbin",
    ]

    for keyword in critical_keywords:
        if keyword in text:
            return {
                "priority": "CRITICAL",
                "priority_reason": (
                    "Matched the critical-risk keyword: "
                    + keyword
                ),
            }

    for keyword in high_keywords:
        if keyword in text:
            return {
                "priority": "HIGH",
                "priority_reason": (
                    "Matched the high-priority keyword: "
                    + keyword
                ),
            }

    for keyword in medium_keywords:
        if keyword in text:
            return {
                "priority": "MEDIUM",
                "priority_reason": (
                    "Matched the medium-priority keyword: "
                    + keyword
                ),
            }

    return {
        "priority": "LOW",
        "priority_reason": (
            "No configured high-risk or medium-priority "
            "keywords were found."
        ),
    }

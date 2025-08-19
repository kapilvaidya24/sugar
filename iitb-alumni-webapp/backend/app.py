from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import re
from typing import Dict, List, Any

app = Flask(__name__)
CORS(app)

# Load the alumni data
with open("structured_careers.json", "r", encoding="utf-8") as f:
    alumni_data = json.load(f)


def search_alumni(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Search alumni by keywords in name, company, title, location, skills etc."""

    # Filter out alumni with no job information
    alumni_with_jobs = {
        name: person
        for name, person in alumni_data.items()
        if person.get("jobs") and len(person["jobs"]) > 0
    }

    if not query:
        # Return first 50 alumni with job data if no query
        return list(alumni_with_jobs.values())[:limit]

    query_lower = query.lower()
    results = []

    for name, person in alumni_with_jobs.items():
        # Search in name
        if query_lower in person["name"].lower():
            results.append(person)
            continue

        # Search in jobs
        match_found = False
        for job in person.get("jobs", []):
            # Search in company name
            if job.get("comp") and query_lower in job["comp"].lower():
                match_found = True
                break

            # Search in job title
            if job.get("title") and query_lower in job["title"].lower():
                match_found = True
                break

            # Search in location
            if job.get("loc") and query_lower in job["loc"].lower():
                match_found = True
                break

            # Search in sector/sub_sector
            if job.get("sector") and query_lower in job["sector"].lower():
                match_found = True
                break

            if job.get("sub_sector") and query_lower in job["sub_sector"].lower():
                match_found = True
                break

            # Search in skill tags
            if job.get("skill_tags"):
                for tag in job["skill_tags"]:
                    if query_lower in tag.lower():
                        match_found = True
                        break

        if match_found:
            results.append(person)

        # Limit results to prevent too many matches
        if len(results) >= limit:
            break

    return results


@app.route("/api/search")
def search():
    """Search endpoint for alumni data"""
    query = request.args.get("q", "")
    limit = int(request.args.get("limit", 50))

    results = search_alumni(query, limit)

    return jsonify({"query": query, "count": len(results), "results": results})


@app.route("/api/stats")
def get_stats():
    """Get basic statistics about the alumni data (only those with job information)"""
    # Only count alumni with job information
    alumni_with_jobs = {
        name: person
        for name, person in alumni_data.items()
        if person.get("jobs") and len(person["jobs"]) > 0
    }

    total_alumni = len(alumni_with_jobs)
    total_jobs = sum(len(person["jobs"]) for person in alumni_with_jobs.values())

    # Count unique companies, graduation years, locations
    companies = set()
    graduation_years = set()
    locations = set()

    for person in alumni_with_jobs.values():
        if person.get("grad_yr"):
            graduation_years.add(person["grad_yr"])

        for job in person["jobs"]:
            if job.get("comp"):
                companies.add(job["comp"])
            if job.get("loc"):
                locations.add(job["loc"])

    return jsonify(
        {
            "total_alumni": total_alumni,
            "alumni_with_jobs": total_alumni,  # Same as total_alumni now since we filter
            "total_jobs": total_jobs,
            "unique_companies": len(companies),
            "graduation_years": sorted(list(graduation_years)),
            "unique_locations": len(locations),
        }
    )


@app.route("/api/alumni/<person_id>")
def get_alumni(person_id):
    """Get detailed information for a specific alumni"""
    for person in alumni_data.values():
        if person["id"] == person_id:
            return jsonify(person)

    return jsonify({"error": "Alumni not found"}), 404


if __name__ == "__main__":
    print(f"Loaded data for {len(alumni_data)} alumni")
    app.run(debug=True, port=5000)

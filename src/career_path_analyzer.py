#!/usr/bin/env python3
"""
Simple Career Path Analyzer
"""

import json
import random
from collections import Counter


def get_sector_transitions():
    """Get all sector transitions from the data with people details"""

    # Load data
    with open("results/structured_careers.json", "r") as f:
        data = json.load(f)

    transitions = []
    career_paths = []

    # Track people for each transition/path
    transition_people = {}
    path_people = {}

    for person_name, person_data in data.items():
        if not person_data or not isinstance(person_data, dict):
            continue

        jobs = person_data.get("jobs", [])
        if len(jobs) < 2:
            continue

        # Get LinkedIn profile
        linkedin = person_data.get("link_ln", "")

        # Sort jobs chronologically by start_year (oldest first), fallback to job_i
        def sort_key(job):
            start_year = job.get("start_year")
            if start_year and isinstance(start_year, (int, float)):
                return start_year
            else:
                # Fallback: job_i=1 is most recent, so higher job_i = older
                job_i = job.get("job_i", 0)
                return 9999 - job_i  # Reverse job_i so oldest comes first

        chronological_jobs = sorted(jobs, key=sort_key)

        # Get sector path
        sectors = []
        for job in chronological_jobs:
            sector = job.get("sector")
            if sector:
                sectors.append(sector)

        # Get transitions (consecutive sector changes)
        for i in range(len(sectors) - 1):
            from_sector = sectors[i]
            to_sector = sectors[i + 1]
            if from_sector != to_sector:
                transition = f"{from_sector} → {to_sector}"
                transitions.append(transition)

                # Track people who made this transition
                if transition not in transition_people:
                    transition_people[transition] = []
                transition_people[transition].append(
                    {"name": person_name, "linkedin": linkedin}
                )

        # Get full career path (remove consecutive duplicates)
        unique_sectors = []
        for sector in sectors:
            if not unique_sectors or sector != unique_sectors[-1]:
                unique_sectors.append(sector)

        if len(unique_sectors) >= 2:
            path = " → ".join(unique_sectors)
            career_paths.append(path)

            # Track people who followed this path
            if path not in path_people:
                path_people[path] = []
            path_people[path].append({"name": person_name, "linkedin": linkedin})

    return transitions, career_paths, transition_people, path_people


def main():
    transitions, career_paths, transition_people, path_people = get_sector_transitions()

    # Count transitions
    transition_counts = Counter(transitions)
    path_counts = Counter(career_paths)

    print(f"Total transitions: {len(transitions)}")
    print(f"Total career paths: {len(career_paths)}")
    print(
        f"Total people with multi-job careers: {len(set(person['name'] for people_list in transition_people.values() for person in people_list))}"
    )
    print()

    print("=" * 80)
    print("TOP 10 SECTOR TRANSITIONS (with proportions and examples)")
    print("=" * 80)

    for i, (transition, count) in enumerate(transition_counts.most_common(10), 1):
        percentage = (count / len(transitions)) * 100
        print(f"\n{i}. {transition}")
        print(f"   Count: {count} people ({percentage:.1f}% of all transitions)")

        # Show 5 random examples
        people = transition_people.get(transition, [])
        examples = random.sample(people, min(5, len(people)))  # Random 5 or all if less
        print(f"   Examples:")

        for person in examples:
            name = person["name"]
            linkedin = person["linkedin"] if person["linkedin"] else "No LinkedIn found"
            print(f"     • {name}")
            print(f"       LinkedIn: {linkedin}")

    print("\n" + "=" * 80)
    print("TOP 10 CAREER PATHS (with proportions and examples)")
    print("=" * 80)

    for i, (path, count) in enumerate(path_counts.most_common(10), 1):
        percentage = (count / len(career_paths)) * 100
        print(f"\n{i}. {path}")
        print(f"   Count: {count} people ({percentage:.1f}% of all career paths)")

        # Show 5 random examples
        people = path_people.get(path, [])
        examples = random.sample(people, min(5, len(people)))  # Random 5 or all if less
        print(f"   Examples:")

        for person in examples:
            name = person["name"]
            linkedin = person["linkedin"] if person["linkedin"] else "No LinkedIn found"
            print(f"     • {name}")
            print(f"       LinkedIn: {linkedin}")


if __name__ == "__main__":
    main()

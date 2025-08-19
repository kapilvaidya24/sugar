#!/usr/bin/env python3
"""
Career Data Structurer
Converts unstructured career information into structured format using OpenAI GPT-3.5
"""

import json
import os
import time
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI


class CareerStructurer:
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the structurer with OpenAI API key"""
        # Try API key from: parameter -> config file -> environment
        self.openai_api_key = (
            openai_api_key or self._load_api_key() or os.getenv("OPENAI_API_KEY")
        )
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found")

        self.client = OpenAI(api_key=self.openai_api_key)

        # File paths
        self.input_file = "results/person_info_results.json"
        self.output_file = "results/structured_careers.json"

        # Create output file if it doesn't exist
        os.makedirs("results", exist_ok=True)
        if not os.path.exists(self.output_file):
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)

    def _load_api_key(self) -> Optional[str]:
        """Load API key from config file"""
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                return config.get("openai_api_key")
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def load_input_data(self) -> Dict:
        """Load the unstructured person info data"""
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def load_existing_results(self) -> Dict:
        """Load existing structured results"""
        try:
            with open(self.output_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_single_result(self, person_name: str, structured_data: Dict):
        """Save a single person's structured result immediately"""
        all_results = self.load_existing_results()
        all_results[person_name] = structured_data

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        print(f"  → Saved structured result for {person_name}")

    def create_structure_prompt(self, raw_career_info: str, person_name: str) -> str:
        """Create the prompt for OpenAI to structure the career data"""
        return f"""
You are a career data analyst. Convert the following unstructured career information into a structured JSON format.

Person Name: {person_name}

Raw Career Information:
{raw_career_info}

Please structure this into the following JSON format:
{{
  "id": "p{hash(person_name) % 10000:04d}",
  "name": "{person_name}",
  "grad_yr": <estimated_graduation_year_from_education_or_context>,
  "email": "<extract_if_found_else_null>",
  "link_ln": "<linkedin_url_if_found>",
  "jobs": [
    {{
      "job_i": 1,
      "comp": "<company_name>",
      "title": "<job_title>",
      "start_year": <year>,
      "end_year": <year_or_null_if_present>,
      "loc": "<location>",
      "source": "<source_from_brackets>",
      "sector": "<one_of: Tech/Product, Finance, Consulting, Research/Academia, Government, Startup, Other>",
      "sub_sector": "<one_of: AI/ML, Cloud, E-Commerce, FinTech, EdTech, Healthcare Tech, Social Impact, Other>",
      "seniority": "<one_of: Intern, Junior/Associate/IC1, Senior/Staff/Lead, Manager/Director, VP/C-Level, Founder/Executive>",
      "level_code": "<one_of: IC1, IC2, Senior, Manager+, Exec, Founder>",
      "employment_type": "<one_of: Full-time, Part-time, Contract, Internship, Fellowship, Consulting>",
      "founder_flag": <true_if_founder_cofounder_else_false>,
      "company_size": "<one_of: Small (<50), Medium (50-500), Large (500+), Unknown>",
      "company_stage": "<one_of: Startup, Scale-up, Public/Corporate, Non-Profit>",
      "country": "<two_letter_code: IN, US, UK, SG, DE, Other>",
      "region": "<one_of: India, US, Europe, SEA, Other>",
      "remote_type": "<one_of: Onsite, Hybrid, Remote>",
      "duration_years": <calculated_duration_in_years>,
      "industry_change": <true_if_different_sector_from_previous_job>,
      "company_switch": <true_if_different_company_from_previous_job>,
      "promotion_flag": <true_if_promoted_within_same_company>,
      "first_manager_flag": <true_if_first_management_role>,
      "first_founder_flag": <true_if_first_founder_role>,
      "skill_tags": [<relevant_skills_from_context>],
      "notes": "<any_additional_notes>"
    }}
  ]
}}

Rules:
1. Extract graduation year from education info (e.g., "2014–2018" means grad_yr: 2018)
2. Order jobs in REVERSE chronological order (most recent/current job first, oldest job last):
ORDER BY START YEAR DESC, NOT BY END YEAR
   - job_i: 1 → Current or most recent job
   - job_i: 2 → Previous job  
   - job_i: 3 → Job before that
   - job_i: N → Oldest job
3. Use "present" in raw data as null for end_year
4. Classify companies appropriately (Google/Microsoft = Large Public/Corporate, startups = Small/Startup)
5. Infer skills from job titles and companies
6. Calculate duration_years as decimal (e.g., 2.5 years)
7. Set flags based on career progression logic
8. Use null for missing data, don't make up information
9. Extract location country codes (Bangalore/Mumbai = IN, New York = US, etc.)

Return only the JSON, no additional text.
"""

    def structure_career_data(
        self, raw_career_info: str, person_name: str
    ) -> Optional[Dict]:
        """Use OpenAI to structure the raw career data"""
        if not raw_career_info or raw_career_info.strip() == "":
            return None

        prompt = self.create_structure_prompt(raw_career_info, person_name)

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise career data analyst. Always return valid JSON only, no additional text.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4000,
                temperature=0,
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            structured_data = json.loads(result_text)
            return structured_data

        except json.JSONDecodeError as e:
            print(f"    ✗ JSON parse error for {person_name}: {e}")
            return None
        except Exception as e:
            print(f"    ✗ OpenAI error for {person_name}: {e}")
            return None

    def process_single_person(
        self, person_name: str, raw_career_info: str
    ) -> Tuple[str, Optional[Dict]]:
        """Process a single person and return the result"""
        if not raw_career_info or raw_career_info.strip() == "":
            print(f"  ⚠️ No career info found for {person_name}")
            return person_name, None

        # Structure the career data
        structured_data = self.structure_career_data(raw_career_info, person_name)

        if structured_data:
            job_count = len(structured_data.get("jobs", []))
            print(f"  ✓ Structured {job_count} jobs for {person_name}")
            return person_name, structured_data
        else:
            print(f"  ✗ Failed to structure data for {person_name}")
            return person_name, None

    def process_batch(self, batch: List[Tuple[str, str]], batch_num: int) -> None:
        """Process a batch of people using ThreadPoolExecutor"""
        print(f"\n{'=' * 60}")
        print(f"BATCH {batch_num}: Processing {len(batch)} people in parallel")
        print(f"{'=' * 60}")

        with ThreadPoolExecutor(max_workers=100) as executor:
            # Submit all tasks
            future_to_person = {
                executor.submit(
                    self.process_single_person, person_name, raw_info
                ): person_name
                for person_name, raw_info in batch
            }

            # Collect results as they complete
            for future in as_completed(future_to_person):
                person_name = future_to_person[future]
                try:
                    result_name, structured_data = future.result()
                    # Save immediately when each task completes
                    self.save_single_result(result_name, structured_data)
                except Exception as e:
                    print(f"  ✗ Error processing {person_name}: {e}")
                    self.save_single_result(person_name, None)

        print(f"✅ Batch {batch_num} completed!")

    def process_all_people(
        self, max_people: Optional[int] = None, batch_size: int = 25
    ):
        """Process all people in batches, skipping those already done"""
        input_data = self.load_input_data()
        existing_results = self.load_existing_results()

        # Filter out already processed people
        people_to_process = [
            name for name in input_data.keys() if name not in existing_results
        ]

        if not people_to_process:
            print("All people have already been processed!")
            return

        if max_people:
            people_to_process = people_to_process[:max_people]

        print(
            f"Processing {len(people_to_process)} people in batches of {batch_size}..."
        )
        print(f"Skipping {len(existing_results)} already processed")

        # Create batches
        batches = []
        for i in range(0, len(people_to_process), batch_size):
            batch_people = people_to_process[i : i + batch_size]
            batch_data = [(name, input_data.get(name, "")) for name in batch_people]
            batches.append(batch_data)

        # Process each batch
        for batch_num, batch in enumerate(batches, 1):
            self.process_batch(batch, batch_num)

            # Small delay between batches to be nice to the API
            if batch_num < len(batches):
                print("⏳ Waiting 2 seconds before next batch...")
                time.sleep(2)

        print("\n✅ All processing completed!")

    def print_summary(self):
        """Print summary of processed results"""
        results = self.load_existing_results()
        successful = sum(1 for r in results.values() if r is not None)
        failed = sum(1 for r in results.values() if r is None)

        total_jobs = 0
        for result in results.values():
            if result and isinstance(result, dict):
                total_jobs += len(result.get("jobs", []))

        print(f"\n{'=' * 50}")
        print("SUMMARY")
        print("=" * 50)
        print(f"Total people processed: {len(results)}")
        print(f"Successfully structured: {successful}")
        print(f"Failed to structure: {failed}")
        print(f"Total jobs extracted: {total_jobs}")
        print(f"Results saved to: {self.output_file}")


def main():
    """Main function"""
    try:
        structurer = CareerStructurer()
    except ValueError as e:
        print(f"Error: {e}")
        print(
            "Please set your OPENAI_API_KEY environment variable or add it to config.json"
        )
        return

    # Process people in batches of 10
    print("Starting career data structuring...")
    structurer.process_all_people(max_people=1000, batch_size=100)

    # Print summary
    structurer.print_summary()

    # Show a sample result
    results = structurer.load_existing_results()
    if results:
        print("\nSample structured result:")
        sample_name = list(results.keys())[0]
        sample_data = results[sample_name]
        if sample_data:
            print(f"{sample_name}:")
            print(json.dumps(sample_data, indent=2)[:500] + "...")


if __name__ == "__main__":
    main()

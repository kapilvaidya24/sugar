#!/usr/bin/env python3
"""
Person Information Finder using Parallel Task API
Finds LinkedIn profiles and job information for people from name scraper results
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
import requests
import glob


def load_names_from_results() -> List[str]:
    """Load names from existing name scraper results"""
    names = []
    results_dir = "results"

    if not os.path.exists(results_dir):
        print(f"No {results_dir} directory found")
        return names

    # Find all JSON result files
    json_files = glob.glob(os.path.join(results_dir, "*names_extracted*.json"))

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                file_results = json.load(f)

                for url, data in file_results.items():
                    if isinstance(data, list):
                        # Old format - names are directly in the list
                        names.extend(data)
                    else:
                        # New format - names are in the 'names' field
                        names.extend(data.get("names", []))

            print(f"Loaded names from {os.path.basename(json_file)}")
        except Exception as e:
            print(f"Error loading {json_file}: {e}")

    # Remove duplicates and empty names
    unique_names = list(set(name.strip() for name in names if name.strip()))
    print(f"Total unique names found: {len(unique_names)}")
    return unique_names


class PersonInfoFinder:
    def __init__(
        self, api_key: Optional[str] = None, output_file: Optional[str] = None
    ):
        """Initialize with Parallel API key and output file"""
        # Try API key from: parameter -> config file -> environment
        self.api_key = api_key or self._load_api_key() or os.getenv("PARALLEL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Parallel API key not found. Please set it in config.json, environment variable PARALLEL_API_KEY, or pass as parameter"
            )

        self.base_url = "https://api.parallel.ai/v1"
        self.headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

        # Set up output file
        if output_file is None:
            self.output_file = f"results/person_info_results.json"
        else:
            self.output_file = output_file

        # Create results directory if needed
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        # Initialize empty results file if it doesn't exist
        if not os.path.exists(self.output_file):
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)

        print(f"Results will be saved to: {self.output_file}")

    def _load_api_key(self) -> Optional[str]:
        """Load API key from config file"""
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                return config.get("parallel_api_key")
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def load_existing_results(self) -> Dict:
        """Load existing results from output file"""
        try:
            with open(self.output_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_single_result(self, person_name: str, person_info: Optional[Dict]):
        """Save a single person's result immediately to the JSON file"""
        # Load existing results
        all_results = self.load_existing_results()

        # Add/update this person's info
        all_results[person_name] = person_info

        # Save back to file
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        print(
            f"  → Saved result for {person_name} to {os.path.basename(self.output_file)}"
        )

    def create_task_spec(self):
        """Create task specification for finding person information"""
        return {
            "input_schema": {
                "type": "json",
                "json_schema": {
                    "type": "object",
                    "properties": {
                        "person_name": {
                            "type": "string",
                            "description": "Full name of the person to research",
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context about the person (e.g., university, graduation year)",
                        },
                    },
                    "required": ["person_name"],
                },
            },
            "output_schema": {
                "type": "text",
                "description": "Person's professional information as a formatted string. Include LinkedIn profile URL if found, followed by job history with company, title, dates, and location. Examples:\n\nExample 1:\nLinkedIn: https://linkedin.com/in/john-doe\nJobs:\n1. Google - Software Engineer (2020-01-15 to present) - Mountain View, CA [source: linkedin]\n2. Microsoft - Junior Developer (2018-06-01 to 2019-12-31) - Seattle, WA [source: linkedin]\n\nExample 2:\nLinkedIn: Not found\nJobs:\n1. Apple - Product Manager (2021-03-01 to present) - Cupertino, CA [source: company-site]\n2. Startup Inc - Co-founder (2019-01-01 to 2020-12-31) - San Francisco, CA [source: linkedin]\n\nExample 3:\nLinkedIn: https://linkedin.com/in/jane-smith\nNo job information found",
            },
        }

    def create_task_run(self, person_name: str) -> Optional[str]:
        """Create a task run for finding person information"""
        task_spec = self.create_task_spec()

        payload = {
            "input": {
                "person_name": person_name,
                "context": "IIT Bombay Computer Science graduate",
            },
            "processor": "core",
            "task_spec": task_spec,
        }

        try:
            response = requests.post(
                f"{self.base_url}/tasks/runs",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            return result.get("run_id")

        except Exception as e:
            print(f"Error creating task for {person_name}: {e}")
            return None

    def get_task_status(self, run_id: str) -> Optional[str]:
        """Get status of a task run"""
        try:
            response = requests.get(
                f"{self.base_url}/tasks/runs/{run_id}",
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            return result.get("status")

        except Exception as e:
            print(f"Error getting status for run {run_id}: {e}")
            return None

    def get_task_result(self, run_id: str) -> Optional[Dict]:
        """Get result of a task run"""
        try:
            response = requests.get(
                f"{self.base_url}/tasks/runs/{run_id}/result",
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()

            # Handle both potential response structures
            if "result" in result and "content" in result.get("result", {}):
                # Structure: result.result.content
                return {"status": "completed", "content": result["result"]["content"]}
            elif "output" in result:
                # Structure: result.output.content or result.output
                output = result["output"]
                if isinstance(output, dict) and "content" in output:
                    return {"status": "completed", "content": output["content"]}
                else:
                    return {"status": "completed", "content": output}
            else:
                # Fallback - return the whole result
                return {"status": "completed", "content": result}

        except Exception as e:
            print(f"Error getting result for run {run_id}: {e}")
            return {"status": "failed", "error": str(e)}

    def schedule_all_tasks(self, names: List[str]) -> Dict[str, str]:
        """Schedule all tasks at once and return mapping of name -> run_id"""
        existing_results = self.load_existing_results()

        # Filter out names that are already processed
        names_to_process = [name for name in names if name not in existing_results]

        if not names_to_process:
            print("All names have already been processed!")
            return {}

        print(f"Scheduling {len(names_to_process)} tasks...")
        if len(existing_results) > 0:
            print(f"Skipping {len(existing_results)} already processed names")

        task_mapping = {}  # name -> run_id

        for i, name in enumerate(names_to_process, 1):
            print(f"  Scheduling task {i}/{len(names_to_process)}: {name}")

            run_id = self.create_task_run(name)
            if run_id:
                task_mapping[name] = run_id
                print(f"    ✓ Task created: {run_id}")
            else:
                print(f"    ✗ Failed to create task for {name}")
                # Save failed scheduling immediately
                self.save_single_result(name, None)

            # Small delay between scheduling requests
            time.sleep(0.5)

        print(f"\n🚀 Successfully scheduled {len(task_mapping)} tasks!")
        return task_mapping

    def poll_all_tasks(self, task_mapping: Dict[str, str], max_wait_time: int = 7200):
        """Poll all running tasks and save results as they complete"""
        if not task_mapping:
            print("No tasks to poll")
            return

        print(f"\n📊 Polling {len(task_mapping)} running tasks...")
        print(f"Maximum wait time: {max_wait_time / 60:.1f} minutes")

        start_time = time.time()
        completed_tasks = set()

        while (
            len(completed_tasks) < len(task_mapping)
            and time.time() - start_time < max_wait_time
        ):
            newly_completed = 0
            status_counts = {}

            for name, run_id in task_mapping.items():
                if name in completed_tasks:
                    continue

                # First check if task is completed
                status = self.get_task_status(run_id) or "unknown"
                status_counts[status] = status_counts.get(status, 0) + 1

                if status in ["completed", "failed"]:
                    if status == "completed":
                        # Get the actual result content
                        result = self.get_task_result(run_id)
                        if result and result.get("status") == "completed":
                            output = result.get("content", "")
                            print(f"  ✓ Completed: {name}")
                            self.save_single_result(name, output)
                        else:
                            print(f"  ✗ Failed to get result: {name}")
                            self.save_single_result(name, None)
                    else:
                        print(f"  ✗ Failed: {name}")
                        self.save_single_result(name, None)

                    completed_tasks.add(name)
                    newly_completed += 1

            if newly_completed > 0:
                remaining = len(task_mapping) - len(completed_tasks)
                elapsed = time.time() - start_time
                print(
                    f"    📈 Progress: {len(completed_tasks)}/{len(task_mapping)} completed, {remaining} remaining ({elapsed / 60:.1f}min elapsed)"
                )

            # Print actual task status counts
            status_str = ", ".join(
                [f"{status}: {count}" for status, count in status_counts.items()]
            )
            print(f"    Task statuses - {status_str}")

            if len(completed_tasks) < len(task_mapping):
                print("    ⏳ Waiting 60 seconds before next check...")
                time.sleep(60)

        # Handle timeouts
        timed_out_tasks = set(task_mapping.keys()) - completed_tasks
        if timed_out_tasks:
            print(f"\n⏰ {len(timed_out_tasks)} tasks timed out:")
            for name in timed_out_tasks:
                print(f"  - {name}")
                self.save_single_result(name, None)

    def process_all_names(
        self, names: List[str], batch_size: int = 10, max_names: Optional[int] = None
    ) -> None:
        """Process names in batches and save results incrementally"""
        if max_names:
            names = names[:max_names]

        print(f"Processing {len(names)} people in batches of {batch_size}...")
        print(f"Results will be saved incrementally to: {self.output_file}")

        # Process in batches
        for batch_start in range(0, len(names), batch_size):
            batch_end = min(batch_start + batch_size, len(names))
            batch = names[batch_start:batch_end]

            print(f"\n{'=' * 60}")
            print(
                f"BATCH {batch_start // batch_size + 1}: Processing people {batch_start + 1}-{batch_end}"
            )
            print(f"{'=' * 60}")

            try:
                # Schedule all tasks in this batch
                task_mapping = self.schedule_all_tasks(batch)

                # Poll for results
                if task_mapping:
                    self.poll_all_tasks(task_mapping)

                print(f"✅ Batch {batch_start // batch_size + 1} completed!")

            except Exception as e:
                print(f"❌ Error processing batch {batch_start // batch_size + 1}: {e}")
                # Save error results for this batch
                for name in batch:
                    self.save_single_result(name, None)

    def print_status_stats(self):
        """Print current status statistics"""
        results = self.load_existing_results()
        successful = sum(1 for r in results.values() if r is not None)
        failed = sum(1 for r in results.values() if r is None)

        print(
            f"Status counts - Successful: {successful}, Failed: {failed}, Total: {len(results)}"
        )
        return {"successful": successful, "failed": failed, "total": len(results)}

    def get_final_summary(self):
        """Get final summary of processing results"""
        results = self.load_existing_results()
        total_processed = len(results)
        successful = sum(1 for r in results.values() if r is not None)

        return {
            "total_processed": total_processed,
            "successful": successful,
            "failed": total_processed - successful,
            "output_file": self.output_file,
        }


def main():
    """Main function"""
    # Initialize finder
    try:
        finder = PersonInfoFinder()
    except ValueError as e:
        print(f"Error: {e}")
        print(
            "Please set your PARALLEL_API_KEY environment variable or add it to config.json"
        )
        return

    # Load names from existing results
    names = load_names_from_results()

    if not names:
        print("No names found in results directory")
        return

    # Show current status before processing
    finder.print_status_stats()

    # Process a small batch first (you can increase this)
    max_names = 1000
    batch_size = 1000  # Process 3 people at once for testing
    print(f"Processing first {max_names} names as test in batches of {batch_size}...")

    # Process names (results are saved incrementally)
    finder.process_all_names(names, batch_size=batch_size, max_names=max_names)

    # Get final summary
    summary = finder.get_final_summary()

    print(f"\n{'=' * 50}")
    print("PROCESSING COMPLETED")
    print("=" * 50)
    finder.print_status_stats()
    print(f"Results saved to: {summary['output_file']}")

    # Show sample results
    if summary["total_processed"] > 0:
        results = finder.load_existing_results()
        print("\nSample results:")
        for i, (name, info) in enumerate(list(results.items())[:3]):
            if info:
                # Display first few lines of the string result
                info_preview = str(info)[:200] + ("..." if len(str(info)) > 200 else "")
                print(f"  {name}:")
                print(f"    {info_preview}")
            else:
                print(f"  {name}: No information found")


if __name__ == "__main__":
    main()

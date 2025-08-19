#!/usr/bin/env python3
"""
University Website Name Scraper
Scrapes webpages and uses AI to extract people's names
"""

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
import json
from typing import List, Optional, Dict, Set, Union
import time
from datetime import datetime
import glob
import re


class NameScraper:
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the scraper with OpenAI API key"""
        # Try API key from: parameter -> config file -> environment
        self.openai_api_key = (
            openai_api_key or self._load_api_key() or os.getenv("OPENAI_API_KEY")
        )
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None

    def _load_api_key(self) -> Optional[str]:
        """Load API key from config file"""
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                return config.get("openai_api_key")
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def extract_year_from_url(self, url: str) -> Optional[str]:
        """Extract year from URL, especially Web Archive URLs"""
        # Pattern for Web Archive URLs: web.archive.org/web/YYYYMMDDHHMMSS/...
        archive_pattern = r"web\.archive\.org/web/(\d{4})\d{10}"
        match = re.search(archive_pattern, url)
        if match:
            return match.group(1)

        # Pattern for general year in URL: /YYYY/ or ?year=YYYY etc.
        year_pattern = r"[/=](\d{4})[/&?\s]"
        match = re.search(year_pattern, url)
        if match:
            year = int(match.group(1))
            # Only consider reasonable years (e.g., 1990-2030)
            if 1990 <= year <= 2030:
                return str(year)

        # Pattern for year at end of URL
        end_year_pattern = r"(\d{4})/?$"
        match = re.search(end_year_pattern, url)
        if match:
            year = int(match.group(1))
            if 1990 <= year <= 2030:
                return str(year)

        return None

    def load_existing_results(self) -> Dict[str, Union[List[str], Dict]]:
        """Load previously extracted results from existing JSON files"""
        existing_results = {}
        results_dir = "results"

        if not os.path.exists(results_dir):
            return existing_results

        # Find all existing JSON result files
        json_files = glob.glob(os.path.join(results_dir, "names_extracted.json"))

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    file_results = json.load(f)
                    # Handle both old format (list) and new format (dict with metadata)
                    for url, data in file_results.items():
                        if isinstance(data, list):
                            # Convert old format to new format
                            year = self.extract_year_from_url(url)
                            existing_results[url] = {
                                "names": data,
                                "year": year,
                                "scraped_date": "unknown",
                            }
                        else:
                            # New format already has metadata
                            existing_results[url] = data

                    print(
                        f"Loaded {len(file_results)} URLs from {os.path.basename(json_file)}"
                    )
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error loading {json_file}: {e}")

        return existing_results

    def filter_new_urls(self, urls: List[str]) -> List[str]:
        """Filter out URLs that have already been processed"""
        existing_results = self.load_existing_results()
        processed_urls = set(existing_results.keys())

        new_urls = [url for url in urls if url not in processed_urls]

        if processed_urls:
            print(f"Found {len(processed_urls)} previously processed URLs")
            print(f"Skipping {len(urls) - len(new_urls)} already processed URLs")
            print(f"Processing {len(new_urls)} new URLs")

        return new_urls

    def find_urls_with_empty_names(self) -> List[str]:
        """Find URLs that have been processed but returned empty names"""
        existing_results = self.load_existing_results()
        empty_urls = []

        for url, data in existing_results.items():
            # Handle both old format (list) and new format (dict with metadata)
            if isinstance(data, list):
                names = data
            else:
                names = data.get("names", [])

            # Check if names list is empty
            if not names:
                empty_urls.append(url)

        return empty_urls

    def process_empty_name_urls_only(self) -> dict:
        """Process only URLs that currently have empty names in the results"""
        empty_urls = self.find_urls_with_empty_names()

        if not empty_urls:
            print("No URLs found with empty names!")
            return self.load_existing_results()

        print(f"Found {len(empty_urls)} URLs with empty names:")
        for i, url in enumerate(empty_urls, 1):
            year = self.extract_year_from_url(url)
            year_info = f" (Year: {year})" if year else ""
            print(f"  {i}. {url[:80]}{'...' if len(url) > 80 else ''}{year_info}")

        print(f"\nReprocessing these {len(empty_urls)} URLs...")

        # Process these specific URLs (don't skip existing since we want to retry them)
        return self.process_urls_individually(empty_urls, skip_existing=False)

    def scrape_webpage(self, url: str) -> str:
        """Scrape text content from a webpage"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return ""

    def extract_names_with_openai(self, text: str) -> List[str]:
        """Extract names using OpenAI API"""
        if not self.client:
            raise ValueError("OpenAI API key not provided")

        # Truncate text if too long (GPT has token limits)
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts people's names from text. Return only the names, one per line, without titles or positions. Return all the names in the text below",
                    },
                    {
                        "role": "user",
                        "content": f"Extract all people's names from this text:\n\n{text}",
                    },
                ],
                max_tokens=4096,
                temperature=0,
            )

            names_text = response.choices[0].message.content.strip()
            names = [name.strip() for name in names_text.split("\n") if name.strip()]
            return names

        except Exception as e:
            print(f"Error with OpenAI API: {e}")
            return []

    def process_single_url(self, url: str) -> Dict:
        """Process a single URL and return the result with metadata"""
        print(f"Processing: {url}")

        # Extract year from URL
        year = self.extract_year_from_url(url)
        if year:
            print(f"Detected year: {year}")

        # Scrape webpage
        text = self.scrape_webpage(url)
        if not text:
            result = {
                "names": [],
                "year": year,
                "scraped_date": datetime.now().strftime("%Y-%m-%d"),
            }
            print("No content found for this URL")
            return result

        # Extract names
        names = self.extract_names_with_openai(text)

        # Store results with metadata
        result = {
            "names": names,
            "year": year,
            "scraped_date": datetime.now().strftime("%Y-%m-%d"),
        }

        print(f"Found {len(names)} names: {names[:5]}{'...' if len(names) > 5 else ''}")

        return result

    def process_urls_individually(
        self, urls: List[str], skip_existing: bool = True
    ) -> dict:
        """Process URLs one by one, saving after each"""
        # Load existing results if available
        all_results = self.load_existing_results() if skip_existing else {}

        # Filter out already processed URLs
        urls_to_process = self.filter_new_urls(urls) if skip_existing else urls

        if not urls_to_process:
            print("No new URLs to process!")
            return all_results

        print(f"Processing {len(urls_to_process)} URLs individually...")

        # Create a single filename for this session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        session_json_file = os.path.join(results_dir, f"names_extracted.json")

        print(f"Will save all results to: {session_json_file}")

        for i, url in enumerate(urls_to_process, 1):
            print(f"\n--- URL {i}/{len(urls_to_process)} ---")

            try:
                # Process single URL
                result = self.process_single_url(url)

                # Add to results
                all_results[url] = result

                # Save results immediately to the same file (overwrite)
                self.save_results(all_results, "json", filename=session_json_file)
                print(f"✓ Results updated in: {os.path.basename(session_json_file)}")

                # Be nice to the API
                time.sleep(1)

            except Exception as e:
                print(f"✗ Error processing {url}: {e}")
                # Still save what we have so far
                all_results[url] = {
                    "names": [],
                    "year": self.extract_year_from_url(url),
                    "scraped_date": datetime.now().strftime("%Y-%m-%d"),
                    "error": str(e),
                }
                self.save_results(all_results, "json", filename=session_json_file)
                print(
                    f"✓ Results updated (with error) in: {os.path.basename(session_json_file)}"
                )

        return all_results

    def process_urls(self, urls: List[str], skip_existing: bool = True) -> dict:
        """Legacy method - now calls the individual processing method"""
        return self.process_urls_individually(urls, skip_existing)

    def save_results(
        self, results: dict, output_format: str = "json", filename: Optional[str] = None
    ) -> str:
        """Save results to file"""
        # Create results directory if it doesn't exist
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if output_format.lower() == "json":
                filename = os.path.join(results_dir, f"names_extracted.json")
            elif output_format.lower() == "txt":
                filename = os.path.join(results_dir, f"names_extracted.txt")

        if output_format.lower() == "json":
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

        elif output_format.lower() == "txt":
            with open(filename, "w", encoding="utf-8") as f:
                f.write("EXTRACTED NAMES FROM UNIVERSITY WEBSITES\n")
                f.write("=" * 50 + "\n")
                f.write(
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                for url, data in results.items():
                    # Handle both old and new data formats
                    if isinstance(data, list):
                        names = data
                        year = self.extract_year_from_url(url)
                        scraped_date = "unknown"
                    else:
                        names = data.get("names", [])
                        year = data.get("year")
                        scraped_date = data.get("scraped_date", "unknown")

                    f.write(f"URL: {url}\n")
                    if year:
                        f.write(f"Year: {year}\n")
                    f.write(f"Scraped: {scraped_date}\n")
                    f.write(f"Names found ({len(names)}):\n")
                    for name in names:
                        f.write(f"  - {name}\n")
                    f.write("\n")

        else:
            raise ValueError("Output format must be 'json' or 'txt'")

        return filename

    def clear_all_results(self) -> None:
        """Clear all existing result files (use with caution!)"""
        results_dir = "results"

        if not os.path.exists(results_dir):
            print("No results directory found")
            return

        json_files = glob.glob(os.path.join(results_dir, "names_extracted.json"))
        txt_files = glob.glob(os.path.join(results_dir, "names_extracted.txt"))

        all_files = json_files + txt_files

        if not all_files:
            print("No result files found to clear")
            return

        print(f"Found {len(all_files)} result files to delete")
        for file_path in all_files:
            try:
                os.remove(file_path)
                print(f"Deleted: {os.path.basename(file_path)}")
            except OSError as e:
                print(f"Error deleting {file_path}: {e}")

        print("Result files cleared!")


def main():
    """Main function to run the scraper"""
    # Example URLs - replace with your actual URLs
    urls = [
        "https://web.archive.org/web/20030202171422/http://www.cse.iitb.ac.in/students-btech2.html",
        "https://web.archive.org/web/20030409142027/http://www.cse.iitb.ac.in/students-btech3.html",
        "https://web.archive.org/web/20030202171534/http://www.cse.iitb.ac.in/students-btech4.html",
        "https://web.archive.org/web/20050724235951/http://www.cse.iitb.ac.in/page80",
        "https://web.archive.org/web/20060614190128/http://www.cse.iitb.ac.in/page102?year=2&pgm=b",
        "https://web.archive.org/web/20070706071629/http://www.cse.iitb.ac.in/page102?year=2&pgm=b",
        "https://web.archive.org/web/20080702190016/http://www.cse.iitb.ac.in/page102?year=2&pgm=b",
        "https://web.archive.org/web/20090225135617/http://www.cse.iitb.ac.in/page15?year=2&pgm=b",
        "https://web.archive.org/web/20100426141314/http://www.cse.iitb.ac.in/page15?year=2&pgm=b",
        "https://web.archive.org/web/20110624101029/http://www.cse.iitb.ac.in/page15?year=2&pgm=b",
        "https://web.archive.org/web/20120201201118/http://www.cse.iitb.ac.in/page222?batch=BTech2",
        "https://web.archive.org/web/20130214162121/http://www.cse.iitb.ac.in/page222?batch=BTech2",
        "https://web.archive.org/web/20140306162711/http://www.cse.iitb.ac.in/page222?batch=BTech2",
        "https://web.archive.org/web/20150618184038/http://www.cse.iitb.ac.in/page222?batch=BTech2",
        "https://web.archive.org/web/20160808235532/https://www.cse.iitb.ac.in/page222?batch=BTech2",
        "https://web.archive.org/web/20160808235532/https://www.cse.iitb.ac.in/page222?batch=BTech2",
        "https://web.archive.org/web/20160808235532/https://www.cse.iitb.ac.in/page222?batch=BTech2",
        # Add your URLs here
    ]

    # Initialize scraper
    scraper = NameScraper()

    # Option 1: Process only URLs that currently have empty names
    print("OPTION: Processing only URLs with empty names from existing results...")
    results = scraper.process_empty_name_urls_only()

    # Option 2: Process URLs individually (automatically skips already processed ones and saves after each)
    # Uncomment the lines below and comment the one above to use this option instead:
    # print("OPTION: Processing new URLs only...")
    # results = scraper.process_urls_individually(urls, skip_existing=True)

    # Option 3: Force reprocess all URLs
    # Uncomment the lines below and comment the one above to use this option instead:
    # print("OPTION: Force reprocessing all URLs...")
    # results = scraper.process_urls_individually(urls, skip_existing=False)

    # Generate final text report
    if results:
        txt_file = scraper.save_results(results, "txt")
        print(f"\n✓ Final text report saved to: {txt_file}")
        json_file = "Saved after each URL"
    else:
        txt_file = "No new results"
        json_file = "No new results"

    # Print summary
    print("\n" + "=" * 50)
    print("SCRAPING COMPLETED")
    print("=" * 50)

    # Calculate total names handling both data formats
    total_names = 0
    urls_with_errors = 0
    for data in results.values():
        if isinstance(data, list):
            total_names += len(data)
        else:
            total_names += len(data.get("names", []))
            if data.get("error"):
                urls_with_errors += 1

    print(f"Total URLs in results: {len(results)}")
    print(f"Total names extracted: {total_names}")
    if urls_with_errors > 0:
        print(f"URLs with errors: {urls_with_errors}")

    if results:
        print(f"\nResults were saved incrementally during processing")
        print(f"Final text report: {txt_file}")

    # Also print a brief summary with years
    print("\nDetailed Summary:")
    for i, (url, data) in enumerate(results.items(), 1):
        if isinstance(data, list):
            names = data
            year = scraper.extract_year_from_url(url)
            error = None
        else:
            names = data.get("names", [])
            year = data.get("year")
            error = data.get("error")

        year_info = f" (Year: {year})" if year else ""
        error_info = f" [ERROR: {error}]" if error else ""
        print(f"  {i}. {len(names)} names{year_info}{error_info}")
        print(f"     {url[:80]}{'...' if len(url) > 80 else ''}")


if __name__ == "__main__":
    main()

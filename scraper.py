# Main script for NCERT book scraping.
# This file will contain the full implementation for browsing the website,
# downloading books, processing files, and generating manifests.
import os
import time
import argparse
import json
import hashlib
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import zipfile

# URL of the NCERT textbook page
BASE_URL = "https://ncert.nic.in/textbook.php?ln=en"

# Mapping from class number to the value in the dropdown
CLASS_MAP = {
    '1': 'Class I', '2': 'Class II', '3': 'Class III', '4': 'Class IV', '5': 'Class V',
    '6': 'Class VI', '7': 'Class VII', '8': 'Class VIII', '9': 'Class IX', '10': 'Class X',
    '11': 'Class XI', '12': 'Class XII'
}

def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Download NCERT books for a specific class.")
    parser.add_argument('--class', dest='class_number', required=True,
                        choices=CLASS_MAP.keys(),
                        help=f"The class number to scrape (e.g., 1, 2, ..., 12).")
    return parser.parse_args()

def main():
    """Main function to orchestrate the scraping process."""
    args = parse_arguments()
    class_number = args.class_number
    class_name = CLASS_MAP[class_number]

    print(f"Starting scraper for {class_name}...")

    # Initialize WebDriver
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.get(BASE_URL)

    try:
        books_to_process = []
        wait = WebDriverWait(driver, 10)

        # --- Step 1: Gather all book combinations ---
        print("Gathering book information...")

        # Select class
        select_class_element = wait.until(EC.presence_of_element_located((By.NAME, 'tclass')))
        select_class = Select(select_class_element)
        select_class.select_by_visible_text(class_name)
        wait.until(EC.presence_of_element_located((By.XPATH, "//select[@name='tsubject']/option[2]")))

        # Get subject options
        select_subject_element = driver.find_element(By.NAME, 'tsubject')
        select_subject = Select(select_subject_element)
        subject_options = [opt.text for opt in select_subject.options if opt.get_attribute('value')]

        for subject_name in subject_options:
            select_subject.select_by_visible_text(subject_name)
            wait.until(EC.presence_of_element_located((By.XPATH, "//select[@name='tbook']/option[2]")))

            select_book_element = driver.find_element(By.NAME, 'tbook')
            select_book = Select(select_book_element)
            book_options = [opt.text for opt in select_book.options if opt.get_attribute('value')]

            for book_title in book_options:
                books_to_process.append({'subject': subject_name, 'title': book_title})

        print(f"Found {len(books_to_process)} books to download.")

        # --- Step 2: Process each book ---
        books_to_track = []
        hashes_data = {}

        for book in books_to_process:
            subject_name = book['subject']
            book_title = book['title']

            print(f"Processing: Subject: {subject_name}, Book: {book_title}")
            driver.get(BASE_URL)

            # Select Class, Subject, and Book
            select_class_element = wait.until(EC.presence_of_element_located((By.NAME, 'tclass')))
            Select(select_class_element).select_by_visible_text(class_name)
            wait.until(EC.presence_of_element_located((By.XPATH, "//select[@name='tsubject']/option[2]")))

            select_subject_element = driver.find_element(By.NAME, 'tsubject')
            Select(select_subject_element).select_by_visible_text(subject_name)
            wait.until(EC.presence_of_element_located((By.XPATH, f"//select[@name='tbook']/option[2]")))

            select_book_element = driver.find_element(By.NAME, 'tbook')
            Select(select_book_element).select_by_visible_text(book_title)

            driver.find_element(By.NAME, 'button').click()
            wait.until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, 'Download complete book')))

            # --- Download and Process Logic ---
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            download_link_tag = soup.find('a', string=re.compile('Download complete book'))

            if not download_link_tag:
                print(f"  > Could not find download link for {book_title}. Skipping.")
                continue

            relative_url = download_link_tag['href']
            download_url = f"https://ncert.nic.in/{relative_url}"

            metadata = download_and_extract(download_url, class_number, subject_name, book_title)

            if metadata:
                book_entry = {
                    "id": metadata["id"],
                    "class": int(class_number),
                    "subject": subject_name,
                    "title": book_title,
                    "pdf_path": metadata["pdf_path"],
                    "download_url": download_url
                }
                books_to_track.append(book_entry)
                hashes_data[metadata["id"]] = metadata["sha256"]

        # --- Step 3: Write Manifest Files ---
        write_manifests(books_to_track, hashes_data)

    finally:
        driver.quit()
        print("Scraping finished.")

def sanitize_filename(name):
    """Cleans a string to be a valid filename."""
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', name).lower()

def download_and_extract(url, class_num, subject, title):
    """Downloads the zip, extracts the PDF, and saves it. Returns metadata on success."""
    output_dir = os.path.join('downloads', f'class_{class_num}')
    os.makedirs(output_dir, exist_ok=True)

    clean_subject = sanitize_filename(subject)
    clean_title = sanitize_filename(title)

    book_id = f"c{class_num}_{clean_subject}_{clean_title}"
    pdf_filename = f"{clean_subject}_{clean_title}.pdf"
    pdf_path = os.path.join(output_dir, pdf_filename)
    zip_path = os.path.join(output_dir, 'temp.zip')

    try:
        print(f"  > Downloading {url}...")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"  > Extracting PDF from {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            pdf_files = [f for f in zip_ref.namelist() if f.lower().endswith('.pdf')]
            if not pdf_files:
                print(f"  > No PDF found in {zip_path}. Skipping.")
                return None

            main_pdf_name = max(pdf_files, key=lambda f: zip_ref.getinfo(f).file_size)

            with zip_ref.open(main_pdf_name) as source, open(pdf_path, 'wb') as target:
                pdf_content = source.read()
                target.write(pdf_content)

            # Calculate SHA256 hash
            sha256_hash = hashlib.sha256(pdf_content).hexdigest()
            print(f"  > Saved PDF to {pdf_path}")

            return {
                "id": book_id,
                "pdf_path": pdf_path,
                "sha256": sha256_hash
            }

    except requests.exceptions.RequestException as e:
        print(f"  > Failed to download {url}. Error: {e}")
        return None
    except zipfile.BadZipFile:
        print(f"  > Failed to open zip file. It may be corrupt.")
        return None
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

def write_manifests(books_to_track, hashes_data):
    """Writes the collected data to JSON manifest files."""
    print("Writing manifest files...")
    with open('books_to_track.json', 'w') as f:
        json.dump(books_to_track, f, indent=2)

    with open('hashes.json', 'w') as f:
        json.dump(hashes_data, f, indent=2)

    print("Manifest files created successfully.")

if __name__ == "__main__":
    main()

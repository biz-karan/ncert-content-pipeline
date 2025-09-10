# NCERT Content Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An automated data pipeline that scrapes, organizes, and maintains a fresh collection of NCERT textbooks. This repository serves as the foundational data source for educational tools, offline-first applications, and AI/ML projects.

## Why This Project Exists

Access to structured, up-to-date educational content is a significant challenge for developers and researchers. This project was created to solve that problem by providing a reliable, automated pipeline for sourcing NCERT textbooks.

The primary goal is to power the **NCERT Assistant**, an offline-first, AI-powered mobile application designed to help students on low-end devices with limited internet access. By making the data pipeline open-source, we hope to enable other non-profit educational projects as well.

## Features

-   **Automated Scraping:** Uses Selenium to navigate the official NCERT website and download books.
-   **Structured Organization:** Saves and organizes PDFs into a clean, predictable directory structure (`downloads/class_*/book_title.pdf`).
-   **Content Freshness:** Employs a hash-based system to detect when a book has been updated on the NCERT website.
-   **Continuous Integration:** A **GitHub Actions workflow** runs on a weekly schedule to automatically check for updates, process new books, and create a new data release.
-   **Metadata Generation:** Automatically creates manifest files (`books_to_track.json` and `hashes.json`) required for downstream applications.

## How The Automation Works

This repository is designed to be a "set it and forget it" data source. A GitHub Actions workflow automates the entire process:

1.  **Scheduled Run:** The workflow triggers automatically every week.
2.  **Scrape & Compare:** The `scraper.py` script visits the NCERT website, downloads the latest version of each tracked book, and compares its file hash to the last known hash stored in `hashes.json`.
3.  **Process Changes:** If a hash mismatch is detected (meaning the book was updated), the pipeline triggers.
4.  **Build Database:** The new PDF is converted to a clean text format, which is then used to build a compact RAG (Retrieval-Augmented Generation) database file (`.db`).
5.  **Commit & Release:** The updated manifest files are committed back to the repo, and the new `.db` files are automatically uploaded to a new **GitHub Release**, making them publicly accessible via a stable URL.

## Repository Structure
<img width="950" height="502" alt="image" src="https://github.com/user-attachments/assets/19f31824-2fec-41fc-8fb5-81051f0128a8" />


## Getting Started (Running the Scraper Manually)

To run the scraper on your local machine:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/ncert-content-pipeline.git
    cd ncert-content-pipeline
    ```

2.  **Install dependencies:**
    First, ensure you have [Poetry](https://python-poetry.org/docs/#installation) installed. Then, run:
    ```bash
    poetry install
    ```
    *Note: This will install Selenium and other dependencies into a virtual environment managed by Poetry. It also requires a compatible WebDriver (e.g., chromedriver) for your browser.*

3.  **Run the script:**
    To scrape all books for Class 1, for example, run the script within the Poetry environment:
    ```bash
    poetry run python scraper.py --class 1
    ```

## Use Cases

The data and tools in this repository can be used for:
-   **Powering Offline Educational Apps:** Provide students with curriculum access without needing an internet connection.
-   **Fine-tuning AI Models:** Create specialized AI tutors by training them on this structured data.
-   **Building RAG Systems:** The generated `.db` files are perfect for creating factual, citation-based AI assistants.
-   **Educational Research & Data Analysis:** Analyze curriculum content, complexity, and evolution over time.

## ⚖️ Legal and Ethical Disclaimer

**This is an unofficial, non-profit, open-source project intended for educational purposes only.**

-   **Source of Content:** All textbook content is sourced directly from the official NCERT website ([ncert.nic.in](https://ncert.nic.in/)) and is the copyright of NCERT.
-   **No Affiliation:** This project is not affiliated with, endorsed by, or sponsored by NCERT.
-   **Non-Commercial Use:** Any use of the data or tools provided in this repository must be for non-commercial purposes.
-   **Attribution:** Any application or service built using this data pipeline **must** provide clear attribution to NCERT as the original source of the content.

## Contributing

Contributions are welcome! If you'd like to help, please feel free to open an issue or submit a pull request. Areas for improvement include:
-   Making the scraper more resilient to website changes.
-   Adding support for more classes and subjects.
-   Optimizing the PDF processing and database creation steps.

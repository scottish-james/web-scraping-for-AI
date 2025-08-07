"""
NatWest Page to Markdown Test Script - 30 Random URLs Version

This script tests the conversion of 30 randomly selected NatWest pages to Markdown.
URLs are selected randomly from a sitemap CSV file.

It uses Selenium with headless Chrome to capture dynamic content, then
converts it to Markdown using Microsoft's MarkItDown library.
The script filters out header, footer, navigation and cookie notices.
All Markdown files are saved to a single output folder with the URL as a header.
"""

import os
import time
import json
import random  # Added for random selection
from concurrent.futures import ThreadPoolExecutor, as_completed  # Added for parallel processing
import threading  # Added for thread-local storage
from markitdown import MarkItDown  # Microsoft's MarkItDown library
from bs4 import BeautifulSoup  # Added for HTML cleaning


def create_chrome_driver():
    """
    Create a new Chrome WebDriver instance

    Returns:
        WebDriver instance or None if creation fails
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        # Set up headless Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")

        # Create a new Chrome browser instance
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Set page load timeout
        driver.set_page_load_timeout(30)

        return driver
    except Exception as e:
        print(f"Failed to create Chrome driver: {str(e)}")
        return None


def fetch_url_content_parallel(url):
    """
    Fetch content from a URL using Selenium with Chrome (parallel version)
    Each thread gets its own WebDriver instance

    Args:
        url: URL to fetch

    Returns:
        Tuple of (URL, content as string) or (URL, None) if failed
    """
    driver = None
    thread_id = threading.current_thread().ident

    try:
        print(f"[Thread {thread_id}] Processing: {url}")

        # Create a new driver for this thread
        driver = create_chrome_driver()
        if not driver:
            print(f"[Thread {thread_id}] Failed to create Chrome driver for: {url}")
            return url, None

        try:
            # Navigate to the URL
            driver.get(url)

            # Wait for JavaScript to load
            time.sleep(5)

            # Scroll down the page to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for any lazy-loaded content

            # Scroll back to top
            driver.execute_script("window.scrollTo(0, 0);")

            # Capture the fully rendered page source
            page_source = driver.page_source

            # Clean the HTML to remove headers and footers
            cleaned_html = clean_html_content(page_source)

            print(f"[Thread {thread_id}] Successfully processed: {url}")
            return url, cleaned_html

        except Exception as e:
            print(f"[Thread {thread_id}] SELENIUM FAILED for {url}: {str(e)}")
            return url, None

    except Exception as outer_e:
        print(f"[Thread {thread_id}] SELENIUM SETUP FAILED for {url}: {str(outer_e)}")
        return url, None

    finally:
        # Always clean up the driver
        if driver:
            try:
                driver.quit()
                print(f"[Thread {thread_id}] Driver closed for: {url}")
            except Exception as cleanup_e:
                print(f"[Thread {thread_id}] Error closing driver: {cleanup_e}")


def process_url_parallel(url_and_index):
    """
    Process a single URL in parallel - fetch content, convert to markdown, and save results

    Args:
        url_and_index: Tuple of (url, index) where index is for filename generation

    Returns:
        Tuple of (url, success_boolean)
    """
    url, index = url_and_index
    thread_id = threading.current_thread().ident

    try:
        print(f"[Thread {thread_id}] Starting processing for URL ({index}): {url}")

        # Fetch the URL content
        _, html_content = fetch_url_content_parallel(url)

        if not html_content:
            print(f"[Thread {thread_id}] Failed to fetch content from URL: {url}")
            return url, False

        # Convert to Markdown
        print(f"[Thread {thread_id}] Converting to Markdown: {url}")
        _, markdown_content = convert_to_markdown(url, html_content)

        # Generate a filename based on the URL (making it filesystem-safe)
        filename = f"page_{index}_{url.replace('://', '_').replace('/', '_').replace('?', '_').replace('&', '_')}.md"

        # Save the Markdown content to the output directory
        output_dir = "natwest_markdown"  # Use the same output directory
        md_file = os.path.join(output_dir, filename)

        # Thread-safe file writing
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"[Thread {thread_id}] Markdown content saved to {md_file}")
        return url, True

    except Exception as e:
        print(f"[Thread {thread_id}] Error processing URL {url}: {str(e)}")
        return url, False
    """
    Fetch content from a URL using Selenium with Chrome to render JavaScript

    This captures the fully rendered DOM after JavaScript execution,
    including dynamically loaded content that wouldn't be in the raw HTML.

    Args:
        url: URL to fetch
        driver: Optional existing Chrome WebDriver instance to reuse

    Returns:
        Tuple of (URL, content as string, driver) or (URL, None, driver) if failed
    """
    should_close_driver = False

    try:
        # If no driver is provided, create a new one
        if driver is None:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager

            print(f"Creating new Chrome instance for: {url}")

            # Set up headless Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")

            # Create a new Chrome browser instance
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Set page load timeout
            driver.set_page_load_timeout(30)

            # Flag to close the driver when done if we created it here
            should_close_driver = True
        else:
            print(f"Reusing existing Chrome instance for: {url}")

        try:
            # Navigate to the URL
            driver.get(url)

            # Wait for JavaScript to load (adjust time as needed)
            time.sleep(5)

            # Scroll down the page to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for any lazy-loaded content

            # Scroll back to top
            driver.execute_script("window.scrollTo(0, 0);")

            # Capture the fully rendered page source (HTML after JavaScript execution)
            page_source = driver.page_source

            # Clean the HTML to remove headers and footers
            cleaned_html = clean_html_content(page_source)

            return url, cleaned_html, driver

        except Exception as e:
            print(f"SELENIUM FAILED for {url}: {str(e)}")
            # If there was an error with the driver, close it if we created it
            if should_close_driver and driver:
                try:
                    driver.quit()
                    driver = None
                except:
                    pass
            # Return failure - no fallback to requests
            return url, None, driver

    except Exception as outer_e:
        print(f"SELENIUM SETUP FAILED for {url}: {str(outer_e)}")
        # Only close the driver if we created it here
        if should_close_driver and driver:
            try:
                driver.quit()
                driver = None
            except:
                pass
        # Return failure - no fallback to requests
        return url, None, driver


def clean_html_content(html_content):
    """
    Clean HTML by removing headers, footers, navigation, and other unwanted elements
    Also fixes relative links to use absolute URLs

    Args:
        html_content: Raw HTML content

    Returns:
        Cleaned HTML content
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove header navigation
        for header in soup.select('header, .header, nav, .nav, .navigation'):
            header.decompose()

        # Remove footer elements
        for footer in soup.select('footer, .footer'):
            footer.decompose()

        # Remove cookie notices and banners
        for cookie_element in soup.select(
                '#onetrust-banner-sdk, #onetrust-consent-sdk, .cookie-banner, .cookie-notice'):
            cookie_element.decompose()

        # Remove login elements
        for login in soup.select('.login, .log-in, .signin, .sign-in'):
            login.decompose()

        # Remove specific NatWest elements (based on the provided HTML)
        for natwest_element in soup.select(
                '.ot-sdk-container, .ot-floating-button__front, #onetrust-pc-sdk, .ot-pc-footer-logo'):
            if natwest_element:
                natwest_element.decompose()

        # Fix all relative links to be absolute
        base_domain = "https://www.natwest.com"
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Check if it's a relative link
            if href and not href.startswith(('http://', 'https://', 'mailto:', 'tel:', '#', 'javascript:')):
                # Remove leading slash if present
                if href.startswith('/'):
                    href = href[1:]
                # Update with absolute URL
                link['href'] = f"{base_domain}/{href}"

        # Keep only the main content (modify selectors as needed based on NatWest's page structure)
        main_content = soup.select_one('#main-content-wrapper, .main-content, main, article, .article')

        if main_content:
            # Create a new minimal HTML document with just the main content
            clean_soup = BeautifulSoup('<html><head><title>Cleaned NatWest Content</title></head><body></body></html>',
                                       'html.parser')
            clean_soup.body.append(main_content)
            return str(clean_soup)
        else:
            # If no main content found, return cleaned but complete document
            return str(soup)
    except Exception as e:
        print(f"Error cleaning HTML: {str(e)}")
        return html_content


def convert_to_markdown(url, html_content):
    """
    Convert HTML content to Markdown using Microsoft's MarkItDown
    Adds the URL as a header at the beginning of the markdown
    Also post-processes the markdown to fix any remaining relative links

    Args:
        url: URL of the page (for reference)
        html_content: HTML content as string

    Returns:
        Tuple of (URL, markdown content) or (URL, error message)
    """
    if html_content is None:
        return url, "Failed to fetch content"

    try:
        # Create a MarkItDown instance
        md_converter = MarkItDown()

        # Save the HTML content to a temporary file
        temp_html_file = f"temp_{hash(url)}.html"
        with open(temp_html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Convert the HTML content to Markdown
        result = md_converter.convert(temp_html_file)
        markdown_content = result.text_content

        # Post-process the markdown to fix any remaining relative links
        # This handles Markdown links in the format [text](link)
        import re
        base_domain = "https://www.natwest.com"

        def fix_link(match):
            link_text = match.group(1)
            link_url = match.group(2)

            # Skip if it's already an absolute URL or special link
            if link_url.startswith(('http://', 'https://', 'mailto:', 'tel:', '#')):
                return f"[{link_text}]({link_url})"

            # Fix relative URL
            if link_url.startswith('/'):
                link_url = link_url[1:]
            fixed_url = f"{base_domain}/{link_url}"
            return f"[{link_text}]({fixed_url})"

        # Find and replace markdown links
        markdown_content = re.sub(r'\[(.*?)\]\((.*?)\)', fix_link, markdown_content)

        # Add the URL as a header at the beginning of the markdown
        markdown_content = f"# Source: {url}\n\n{markdown_content}"

        # Try to extract document structure data if available
        try:
            if hasattr(result, 'document_structure'):
                structure_info = "\n\n## Document Structure Information\n"
                structure_info += "```json\n"
                structure_info += json.dumps(result.document_structure, indent=2)
                structure_info += "\n```\n"
                markdown_content += structure_info
        except:
            pass

        # Clean up the temporary file
        if os.path.exists(temp_html_file):
            os.remove(temp_html_file)

        return url, markdown_content
    except Exception as e:
        return url, f"Conversion error: {str(e)}"


def check_selenium_install():
    """Check if Selenium and necessary drivers are installed"""
    try:
        from selenium import webdriver
        from webdriver_manager.chrome import ChromeDriverManager
        return True
    except ImportError:
        print(
            "\nSelenium or webdriver-manager is not installed. You'll need to install them to use the enhanced page rendering:")
        print("pip install selenium webdriver-manager beautifulsoup4")
        return False


def read_sitemap_csv(csv_file):
    """
    Read all URLs from a CSV sitemap file
    Ensures all URLs are absolute by adding the domain if needed

    Args:
        csv_file: Path to the CSV sitemap file

    Returns:
        List of all URLs in the sitemap
    """
    import csv

    # Base domain to use for relative URLs
    base_domain = "https://www.natwest.com"

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Process URLs to ensure they're absolute
            urls = []
            for row in reader:
                if 'url' in row:
                    url = row['url'].strip()
                    # Check if URL is relative (doesn't start with http:// or https://)
                    if not url.startswith(('http://', 'https://')):
                        # Remove leading slash if present
                        if url.startswith('/'):
                            url = url[1:]
                        # Combine with base domain
                        url = f"{base_domain}/{url}"
                    urls.append(url)

        print(f"Found {len(urls)} URLs in the sitemap")
        return urls
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        # Return a default URL if there's an error
        return ["https://www.natwest.com/corporates/insights/authors/john-stevenson-hamilton.html"]


def select_random_urls(all_urls, num_urls=30):
    """
    Select a random sample of URLs from the full list

    Args:
        all_urls: List of all available URLs
        num_urls: Number of random URLs to select (default: 30)

    Returns:
        List of randomly selected URLs
    """
    if len(all_urls) <= num_urls:
        print(f"Sitemap contains only {len(all_urls)} URLs, using all of them")
        return all_urls

    selected_urls = random.sample(all_urls, num_urls)
    print(f"Randomly selected {num_urls} URLs from {len(all_urls)} total URLs")
    return selected_urls


def process_url(url, output_dir, index, driver=None):
    """
    Process a single URL - fetch content, convert to markdown, and save results

    Args:
        url: The URL to process
        output_dir: Directory to save output files
        index: Index number for this URL (used in filenames)
        driver: Optional Chrome WebDriver instance to reuse

    Returns:
        Tuple containing (success_boolean, driver_instance)
    """
    try:
        print(f"\nProcessing URL ({index}): {url}")

        # Fetch the URL content
        print(f"Fetching content...")
        _, html_content, driver = fetch_url_content(url, driver)

        if not html_content:
            print(f"Failed to fetch content from URL: {url}")
            return False, driver

        # Convert to Markdown
        print(f"Converting to Markdown...")
        _, markdown_content = convert_to_markdown(url, html_content)

        # Generate a filename based on the URL (making it filesystem-safe)
        filename = f"page_{index}_{url.replace('://', '_').replace('/', '_').replace('?', '_').replace('&', '_')}.md"

        # Save the Markdown content to the output directory
        md_file = os.path.join(output_dir, filename)
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"Markdown content saved to {md_file}")

        return True, driver

    except Exception as e:
        print(f"Error processing URL {url}: {str(e)}")
        return False, driver


def create_summary_file(output_dir, processed_urls, successful_urls):
    """
    Create a summary markdown file with links to all processed URLs

    Args:
        output_dir: Directory where markdown files are stored
        processed_urls: List of all URLs that were processed
        successful_urls: List of URLs that were successfully processed
    """
    summary_md = "# NatWest URL to Markdown Processing Summary (30 Random URLs)\n\n"
    summary_md += f"Total URLs processed: {len(processed_urls)}\n\n"
    summary_md += f"Successfully processed: {len(successful_urls)}\n\n"
    summary_md += f"Failed: {len(processed_urls) - len(successful_urls)}\n\n"

    summary_md += "## Processed URLs\n\n"

    for i, url in enumerate(processed_urls):
        status = "✅ Success" if url in successful_urls else "❌ Failed"
        summary_md += f"{i + 1}. [{url}]({url}) - {status}\n"

    summary_file = os.path.join(output_dir, "summary.md")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary_md)

    print(f"\nSummary file created: {summary_file}")


def main():
    try:
        # Check if Selenium is installed
        selenium_available = check_selenium_install()
        if not selenium_available:
            print("\nERROR: Selenium is required for this script!")
            print("Please install: pip install selenium webdriver-manager beautifulsoup4")
            return

        # Create output directory for markdown files
        output_dir = "natwest_markdown"
        os.makedirs(output_dir, exist_ok=True)

        # CSV sitemap file path
        csv_file = "natwest_sitemap.csv"

        # Read all URLs from sitemap
        print(f"Reading all URLs from {csv_file}...")
        all_urls = read_sitemap_csv(csv_file)

        # Randomly select 30 URLs from the full list
        urls = select_random_urls(all_urls, 30)
        print(f"Processing {len(urls)} randomly selected URLs")

        # Prepare URL-index pairs for parallel processing
        url_index_pairs = [(url, i + 1) for i, url in enumerate(urls)]

        # Process URLs in parallel
        successful_urls = []
        max_workers = min(5, len(urls))  # Limit concurrent threads to avoid overwhelming the server

        print(f"\nStarting parallel processing with {max_workers} workers...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(process_url_parallel, url_pair): url_pair[0]
                for url_pair in url_index_pairs
            }

            # Process completed tasks
            completed = 0
            total = len(future_to_url)

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result_url, success = future.result()
                    if success:
                        successful_urls.append(result_url)

                    completed += 1
                    print(f"Progress: {completed}/{total} URLs processed ({len(successful_urls)} successful)")

                except Exception as exc:
                    print(f'URL {url} generated an exception: {exc}')
                    completed += 1

        # Create a summary file
        create_summary_file(output_dir, urls, successful_urls)

        print("\nProcessing complete!")
        print(f"Successfully processed {len(successful_urls)} out of {len(urls)} URLs")
        print(f"All Markdown files saved to: {os.path.abspath(output_dir)}")

    except Exception as e:
        print(f"An error occurred in main execution: {e}")


if __name__ == "__main__":
    main()
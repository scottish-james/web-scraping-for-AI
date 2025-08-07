import xml.etree.ElementTree as ET
import pandas as pd
import requests
from tqdm import tqdm  # For progress bar


def get_sitemap_from_url(url):
    """
    Fetch sitemap content from a URL

    Args:
        url: URL of the sitemap

    Returns:
        Sitemap content as string
    """
    print(f"Fetching sitemap from {url}...")
    response = requests.get(url)
    if response.status_code == 200:
        print("Sitemap successfully retrieved!")
        return response.text
    else:
        raise Exception(f"Failed to fetch sitemap: HTTP {response.status_code}")


def parse_sitemap(sitemap_content):
    """
    Parse sitemap XML content and extract URL information into a pandas DataFrame

    Args:
        sitemap_content: XML content of the sitemap as string

    Returns:
        pandas DataFrame with columns for URL, last modified date, change frequency, and priority
    """
    print("Parsing sitemap XML...")
    # Define the namespace
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    # Parse the XML from the string content
    root = ET.fromstring(sitemap_content)

    # Lists to store the data
    urls = []
    lastmods = []
    changefreqs = []
    priorities = []

    # Count the total number of URLs
    url_elements = root.findall('.//ns:url', namespace)
    total_urls = len(url_elements)
    print(f"Found {total_urls} URLs in the sitemap")

    # Extract data from each URL element with a progress bar
    for url in tqdm(url_elements, desc="Processing URLs"):
        # Get the location (URL)
        loc_elem = url.find('./ns:loc', namespace)
        loc = loc_elem.text if loc_elem is not None else None
        urls.append(loc)

        # Get the last modified date
        lastmod_elem = url.find('./ns:lastmod', namespace)
        lastmod = lastmod_elem.text if lastmod_elem is not None else None
        lastmods.append(lastmod)

        # Get the change frequency
        changefreq_elem = url.find('./ns:changefreq', namespace)
        changefreq = changefreq_elem.text if changefreq_elem is not None else None
        changefreqs.append(changefreq)

        # Get the priority
        priority_elem = url.find('./ns:priority', namespace)
        priority = priority_elem.text if priority_elem is not None else None
        priorities.append(priority)

    # Create a DataFrame from the extracted data
    data = {
        'url': urls,
        'last_modified': lastmods,
        'change_frequency': changefreqs,
        'priority': priorities
    }

    return pd.DataFrame(data)


def main():
    try:
        # Fetch the sitemap from NatWest's website
        sitemap_url = "https://www.natwest.com/sitemap.xml"
        sitemap_content = get_sitemap_from_url(sitemap_url)

        # Parse the sitemap
        df = parse_sitemap(sitemap_content)

        # Display a sample of the DataFrame (first 5 rows)
        print("\nSample of the data:")
        print(df.head())

        # Display summary statistics
        print("\nSummary statistics:")
        print(f"Total URLs: {len(df)}")
        print(f"Unique domains: {df['url'].apply(lambda x: x.split('/')[2] if x and '/' in x else '').nunique()}")

        if 'priority' in df.columns and df['priority'].notna().any():
            print(f"Priority distribution:")
            print(df['priority'].value_counts().sort_index(ascending=False))

        if 'change_frequency' in df.columns and df['change_frequency'].notna().any():
            print(f"Change frequency distribution:")
            print(df['change_frequency'].value_counts())

        # Export to CSV
        csv_filename = 'natwest_sitemap.csv'
        df.to_csv(csv_filename, index=False)
        print(f"\nData exported to {csv_filename}")

        # Export to Excel
        excel_filename = 'natwest_sitemap.xlsx'
        df.to_excel(excel_filename, index=False)
        print(f"Data exported to {excel_filename}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
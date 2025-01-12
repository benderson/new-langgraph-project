import os
import re
import requests
from markitdown import MarkItDown
from dotenv import load_dotenv

load_dotenv()

from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from collections import deque
from openai import OpenAI

def is_same_domain(base_domain: str, test_url: str) -> bool:
    """
    Check if test_url has the same domain as base_domain.
    """
    parsed_test = urlparse(test_url)
    return parsed_test.netloc == base_domain


def is_subdirectory(base_url: str, test_url: str) -> bool:
    """
    Check if test_url is within the same directory path as base_url.
    This allows nested subdirectories (recursive).
    
    E.g. base_url = 'https://example.com/foo/bar/'
         test_url = 'https://example.com/foo/bar/baz/page.html'
         -> True, because the path starts with '/foo/bar'
    """
    parsed_base = urlparse(base_url)
    parsed_test = urlparse(test_url)
    
    # Must be the same domain
    if parsed_base.netloc != parsed_test.netloc:
        return False
    
    # Check path prefix for recursion
    return parsed_test.path.startswith(parsed_base.path)


def is_same_directory(base_url: str, test_url: str) -> bool:
    """
    Check if test_url is in the exact same directory (non-recursive).
    For example, if base_url = 'https://example.com/foo/bar/',
    we'll allow:
      - 'https://example.com/foo/bar/'
      - 'https://example.com/foo/bar/page.html'
    ...but NOT:
      - 'https://example.com/foo/bar/baz/page.html' (this is a subdirectory)
    """
    parsed_base = urlparse(base_url)
    parsed_test = urlparse(test_url)

    if parsed_base.netloc != parsed_test.netloc:
        return False

    # Strip trailing '/' to normalize
    base_path = parsed_base.path.rstrip('/')
    test_path = parsed_test.path.rstrip('/')

    # test_path must start with base_path
    if not test_path.startswith(base_path):
        return False

    # Count path segments
    base_segments = base_path.split('/')
    test_segments = test_path.split('/')

    # If the path is exactly the same or just one additional segment (like a file), it's the same directory.
    if len(test_segments) == len(base_segments):  
        # exact match: e.g. /foo/bar == /foo/bar
        return True
    elif len(test_segments) == len(base_segments) + 1:
        # one more segment: e.g. /foo/bar/page.html
        return True
    else:
        return False

def convert_html_to_markdown(url: str) -> str:
    """
    Convert HTML to Markdown using html2text.
    """
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    client = OpenAI()
    if not OPENAI_API_KEY:
        raise ValueError("API_KEY is not set in the environment variables.")
    md = MarkItDown(llm_client=client, llm_model="gpt-4o")
    result = md.convert(url)
    return result.text_content

def sanitize_filename(url: str) -> str:
    """
    Convert a URL into a safe filename by removing or replacing invalid characters.
    """
    return re.sub(r'[\\/*?:"<>|]+', '_', url)


def scrape_and_store(url: str, output_dir: str, base_domain: str, parsed_path: str) -> None:
    """
    Scrape a single page (url) and store its content in Markdown format.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        #html_content = response.text

        markdown_content = convert_html_to_markdown(url)

        # Create output directory if it doesn't exist
        this_output_dir = os.path.join(output_dir, sanitize_filename(base_domain), sanitize_filename(parsed_path))
        os.makedirs(this_output_dir, exist_ok=True)

        # Generate a file name
        filename = sanitize_filename(url) + ".md"
        filepath = os.path.join(this_output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# URL: {url}\n\n")  # Optionally store the origin URL at the top
            f.write(markdown_content)
        
        print(f"Scraped and stored: {url} -> {filepath}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve {url}: {e}")


def scrape_website(start_url: str, mode: str = "auto", output_dir: str = "scraped_output"):
    """
    Main entry-point for scraping. 
    mode can be:
        'auto'               -> auto-detect single page vs domain vs directory
        'domain'             -> force domain-level
        'directory'          -> only that directory, non-recursive
        'recursive_directory'-> directory plus any subdirectories
        'single'             -> single page only
    """
    parsed = urlparse(start_url)
    base_domain = parsed.netloc
    path = parsed.path if parsed.path else "/"

    # Determine if single page, directory, or domain, etc.
    if mode == "auto":
        # Guess based on path: "/" -> domain; file-like -> single; else directory
        if path == "/":
            mode = "domain"
        elif any(path.endswith(ext) for ext in [".html", ".htm", ".php", ".aspx"]):
            mode = "single"
        else:
            # By default, let's assume user wants recursive subdirectories
            mode = "recursive_directory"

    print(f"Scraping mode: {mode}")

    if mode == "single":
        # Just scrape the page
        scrape_and_store(start_url, output_dir, base_domain)
        return
    else:
        # BFS or DFS approach
        visited = set()
        queue = deque([start_url])

        while queue:
            current_url = queue.popleft()
            if current_url in visited:
                continue

            visited.add(current_url)

            # Scrape and store current page
            scrape_and_store(current_url, output_dir, base_domain, path)

            # If domain/directory/recursive_directory, let's collect more links
            if mode in ("domain", "directory", "recursive_directory"):
                try:
                    response = requests.get(current_url)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        # Create absolute URL
                        new_url = urljoin(current_url, href)
                        # Remove any fragment (#)
                        new_url = new_url.split('#')[0]

                        if new_url not in visited:
                            if mode == "domain":
                                if is_same_domain(base_domain, new_url):
                                    queue.append(new_url)
                            elif mode == "directory":
                                # Only scrape the exact directory (non-recursive)
                                if is_same_directory(start_url, new_url):
                                    queue.append(new_url)
                            elif mode == "recursive_directory":
                                # Scrape directory + all subdirectories
                                if is_subdirectory(start_url, new_url):
                                    queue.append(new_url)

                except requests.exceptions.RequestException as e:
                    print(f"Failed to retrieve links from {current_url}: {e}")

# Example usage
if __name__ == "__main__":
    # Single Page Example
    #scrape_website("https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/", mode="single")

    # Directory Example
    #scrape_website("https://python.langchain.com/api_reference/langchain/", mode="recursive_directory")

    # Domain Example
    # scrape_website("https://example.com", mode="domain")

    # Auto Example
    # scrape_website("https://example.com/some/directory/", mode="auto")

    pass
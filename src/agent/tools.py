from typing import Any, Callable, List, Optional, cast
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated
import scrapy
from scrapy import Spider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from markitdown import MarkItDown
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, urljoin
import asyncio
import tempfile
import shutil
import re

from agent.configuration import Configuration

class DocsSpider(Spider):
    name = 'docs_spider'
    
    def __init__(self, url=None, output_dir=None, page_limit=1, *args, **kwargs):
        super(DocsSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url]
        parsed_url = urlparse(url)
        self.allowed_domains = [parsed_url.netloc]
        self.base_path = parsed_url.path
        if not self.base_path.endswith('/'):
            self.base_path += '/'
        self.md_converter = MarkItDown()
        self.visited_urls = set()
        self.output_dir = output_dir
        self.results = []
        self.page_limit = page_limit
        self.pages_scraped = 0

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, dont_filter=True)

    def extract_content(self, soup):
        """Extract and clean content from HTML"""
        # Remove script and style elements
        for element in soup(['script', 'style']):
            element.decompose()
            
        # Extract quotes
        quotes = []
        for quote in soup.find_all('div', class_='quote'):
            text = quote.find('span', class_='text')
            author = quote.find('small', class_='author')
            tags = quote.find_all('a', class_='tag')
            
            if text and author:
                quote_md = f"## {text.get_text()}\n\n"
                quote_md += f"By {author.get_text()}\n\n"
                if tags:
                    quote_md += "Tags: " + ", ".join(tag.get_text() for tag in tags) + "\n\n"
                quotes.append(quote_md)
                
        # Extract title
        title = soup.title.string if soup.title else 'Untitled'
        title = title.replace(' | Quotes to Scrape', '').strip()
        
        # Build markdown
        markdown = f"# {title}\n\n"
        markdown += "\n".join(quotes)
        
        return markdown

    def parse(self, response):
        # Check if we've reached the page limit before processing
        if self.page_limit is not None and self.pages_scraped >= self.page_limit:
            self.logger.info(f"Reached page limit of {self.page_limit}")
            raise scrapy.exceptions.CloseSpider(reason=f'Reached page limit of {self.page_limit}')

        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Convert to markdown
            markdown_content = self.extract_content(soup)
            
            # Create relative path for file storage
            parsed_url = urlparse(response.url)
            relative_path = parsed_url.path.strip('/')
            if relative_path == '':
                relative_path = 'index'
            # Clean path
            relative_path = re.sub(r'[^\w\-_\.]', '_', relative_path)
            
            # Store result
            result = {
                'url': response.url,
                'path': f"{relative_path}.md",
                'content': markdown_content
            }
            self.results.append(result)
            
            # Save markdown file
            if self.output_dir:
                file_path = os.path.join(self.output_dir, f"{relative_path}.md")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
            
            # Increment page count after successful processing
            self.pages_scraped += 1
            
            # Follow links in docs directory if we haven't reached the limit
            if self.page_limit is None or self.pages_scraped < self.page_limit:
                for href in response.css('a::attr(href)').getall():
                    url = response.urljoin(href)
                    parsed = urlparse(url)
                    
                    # Only follow links in same domain and docs path
                    if (parsed.netloc in self.allowed_domains and 
                        parsed.path.startswith(self.base_path) and
                        url not in self.visited_urls and
                        not parsed.path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif'))):
                        
                        self.visited_urls.add(url)
                        yield scrapy.Request(url)
                    
        except scrapy.exceptions.CloseSpider:
            raise  # Re-raise CloseSpider exception
        except Exception as e:
            self.logger.error(f"Error processing {response.url}: {str(e)}")
            return None

class ScrapingTool:
    def __init__(self):
        self.settings = get_project_settings()
        self.settings.update({
            'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'ROBOTSTXT_OBEY': True,
            'CONCURRENT_REQUESTS': 1,
            'DOWNLOAD_DELAY': 1,
            'LOG_ENABLED': True,
            'LOG_LEVEL': 'INFO'
        })

    async def ainvoke(self, url: str = None, page_limit: Optional[int] = 1) -> List[dict]:
        if not url:
            return []
            
        # Validate URL
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return []
        except:
            return []

        # Create temporary directory for output
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create a list to store results
            results = []
            
            def spider_closed(spider):
                nonlocal results
                results = spider.results

            # Run spider synchronously
            process = CrawlerProcess(self.settings)
            crawler = process.create_crawler(DocsSpider)
            crawler.signals.connect(spider_closed, signal=scrapy.signals.spider_closed)
            process.crawl(crawler, url=url, output_dir=temp_dir, page_limit=page_limit)
            process.start()
            
            # Move files to final location
            for result in results:
                temp_path = os.path.join(temp_dir, result['path'])
                if os.path.exists(temp_path):
                    # Create final directory
                    os.makedirs('src/data', exist_ok=True)
                    final_path = os.path.join('src/data', result['path'])
                    os.makedirs(os.path.dirname(final_path), exist_ok=True)
                    
                    # Move file
                    shutil.move(temp_path, final_path)
            
            return results
            
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

async def scrape(
    query: str,
    page_limit: Optional[int] = 1,
    *, 
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[List[dict[str, Any]]]:
    """
    Scrape documentation pages from a website and convert them to markdown.
    
    Args:
        query: URL of the documentation site to scrape (e.g. https://domain.com/docs/)
        page_limit: Maximum number of pages to scrape. Set to None for unlimited pages. Defaults to 1.
        config: Tool configuration
        
    Returns:
        List of dictionaries containing scraped page data:
        - url: Original page URL
        - path: Local file path where markdown was saved
        - content: Markdown content
    """
    configuration = Configuration.from_runnable_config(config)
    
    # Initialize and run scraping tool
    output = ScrapingTool()
    result = await output.ainvoke(url=query, page_limit=page_limit)

    return result

TOOLS: List[Callable[..., Any]] = [scrape]

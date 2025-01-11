from typing import Any, Callable, List, Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated
import scrapy
from scrapy import Spider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from markitdown import MarkItDown
import os
from urllib.parse import urlparse
import asyncio

from agent.configuration import Configuration

class SimpleSpider(Spider):
    name = 'simple_spider'
    
    def __init__(self, url=None, page_limit=1, *args, **kwargs):
        super(SimpleSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url]
        parsed_url = urlparse(url)
        self.allowed_domains = [parsed_url.netloc]
        self.base_path = parsed_url.path
        if not self.base_path.endswith('/'):
            self.base_path += '/'
        self.visited_urls = set()
        self.discovered_urls = []
        self.page_limit = page_limit
        self.pages_discovered = 0

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, dont_filter=True)

    def parse(self, response):
        # Check if we've reached the page limit
        if self.page_limit is not None and self.pages_discovered >= self.page_limit:
            return

        # Store the URL
        self.discovered_urls.append(response.url)
        self.pages_discovered += 1
            
        # Follow links if we haven't reached the limit
        if self.page_limit is None or self.pages_discovered < self.page_limit:
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
        self.md_converter = MarkItDown()

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

        # Create base output directory
        os.makedirs('src/data', exist_ok=True)
        
        # Create website-specific directory
        site_title = urlparse(url).netloc.replace('.', '_')
        output_dir = os.path.join('src/data', site_title)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Convert URL to markdown using markitdown
            result = self.md_converter.convert(url)
            content = result.text_content
            
            # Add title if not present
            if not content.startswith('# '):
                title = url.split('/')[-1].replace('-', ' ').title() or 'Home'
                markdown_content = f"# {title}\n\n{content}"
            else:
                markdown_content = content
            
            # Create filename from URL
            parsed_url = urlparse(url)
            path = parsed_url.path.strip('/').replace('/', '_') or 'index'
            filename = f"{path}.md"
            
            # Save markdown file
            file_path = os.path.join(output_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Return result
            return [{
                'url': url,
                'path': filename,
                'content': markdown_content
            }]
            
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return []

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

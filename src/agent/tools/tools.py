from typing import Any, Callable, List, Optional, cast, Literal
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated
from agent.tools.scraper import scrape_website
from agent.configuration import Configuration

async def scrape_docs(
    url: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[str]:
    """
    Scrape documentation pages from a website and store them as markdown files.
    
    Args:
        url: URL of the website to scrape
        config: Tool configuration
        
    Returns:
        String describing the scraping results
    """
    configuration = Configuration.from_runnable_config(config)
    
    try:
        # Call the scraper with default mode
        scrape_website(url)
        return f"Successfully scraped {url}"
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"

TOOLS: List[Callable[..., Any]] = [scrape, scrape_docs]

import json
import aiohttp
from typing import Any, Callable, List, Optional, cast, Literal
from typing_extensions import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import InjectedState

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

async def search(
    query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[list[dict[str, Any]]]:
    """Search for general web results.

    This function performs a search using the Tavily search engine, which is designed
    to provide comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events.
    """
    configuration = Configuration.from_runnable_config(config)
    wrapped = TavilySearchResults(max_results=configuration.max_search_results)
    result = await wrapped.ainvoke({"query": query})
    return cast(list[dict[str, Any]], result)

TOOLS: List[Callable[..., Any]] = [scrape_docs]

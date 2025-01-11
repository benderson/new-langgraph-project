import asyncio
import shutil
import os
from agent.tools import scrape
from agent.configuration import Configuration

async def test_scrape():
    # Clear the data directory
    data_dir = "src/data"
    if os.path.exists(data_dir):
        print(f"Clearing {data_dir}...")
        shutil.rmtree(data_dir)
        os.makedirs(data_dir)

    try:
        print("Testing scrape with 5-page limit...")
        config = {}
        result = await scrape("http://quotes.toscrape.com", page_limit=5, config=config)
        
        if not result:
            print("Error: No results returned")
            return
            
        print(f"\nSuccessfully scraped {len(result)} pages:")
        for page in result:
            print(f"- {page['url']} -> {page['path']}")
            
        # Verify files were created
        files = os.listdir(data_dir)
        print(f"\nFiles in {data_dir}:")
        for file in files:
            print(f"- {file}")
            
    except Exception as e:
        print(f"Error during scraping: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_scrape())

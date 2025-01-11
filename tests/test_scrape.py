import asyncio
import shutil
import os
from agent.tools import scrape, ScrapingTool
from agent.configuration import Configuration

async def test_markdown_conversion():
    """Test the markdown conversion functionality"""
    tool = ScrapingTool()
    url = "http://quotes.toscrape.com"
    
    try:
        print(f"\nTesting markdown conversion for {url}...")
        results = await tool.ainvoke(url=url, page_limit=1)
        
        # Verify results
        assert results, "No results returned"
        assert len(results) == 1, "Expected exactly one result"
        result = results[0]
        
        # Verify result structure
        assert 'url' in result, "Result missing 'url' field"
        assert 'path' in result, "Result missing 'path' field"
        assert 'content' in result, "Result missing 'content' field"
        
        # Verify content
        assert result['content'].strip(), "Markdown content is empty"
        assert result['content'].startswith('# '), "Markdown content doesn't start with title"
        
        print(f"Successfully converted {url} to markdown")
        return result
    except Exception as e:
        print(f"Error converting {url} to markdown: {str(e)}")
        raise

async def test_scrape():
    """Integration test for the complete scraping functionality"""
    # Clear the data directory
    data_dir = "src/data"
    if os.path.exists(data_dir):
        print(f"Clearing {data_dir}...")
        shutil.rmtree(data_dir)
        os.makedirs(data_dir)

    try:
        print("\nTesting scrape functionality...")
        config = {}
        result = await scrape("http://quotes.toscrape.com", page_limit=1, config=config)
        
        # Verify results
        assert result, "No results returned"
        assert len(result) == 1, "Expected exactly one result"
        
        page = result[0]
        print(f"\nSuccessfully scraped page:")
        print(f"- {page['url']} -> {page['path']}")
            
        # Verify result has required fields
        assert all(key in page for key in ['url', 'path', 'content']), \
            "Missing required fields in result"
        
        # Verify content was converted to markdown
        assert page['content'].strip(), "Empty content in result"
        assert page['content'].startswith('# '), "Content not in markdown format"
            
        # Verify directory structure
        site_dirs = os.listdir(data_dir)
        assert len(site_dirs) == 1, "Expected exactly one website directory"
        site_dir = site_dirs[0]
        assert site_dir == "quotes_toscrape_com", "Incorrect website directory name"
        
        # Verify files in website directory
        site_path = os.path.join(data_dir, site_dir)
        files = os.listdir(site_path)
        print(f"\nFiles in {site_path}:")
        for file in files:
            print(f"- {file}")
            assert file.endswith('.md'), f"Non-markdown file created: {file}"
            
        # Verify file count matches result count
        assert len(files) == len(result), \
            f"Mismatch between results ({len(result)}) and files ({len(files)})"
            
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        raise

async def run_tests():
    """Run all tests"""
    print("\nTesting markdown conversion...")
    await test_markdown_conversion()
    
    print("\nRunning integration test...")
    await test_scrape()
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_tests())

# Web Scraping Implementation

## Overview
The web scraping functionality has been simplified to use a two-step process:
1. URL Discovery using Scrapy
2. Markdown Conversion using MarkItDown

## Implementation Details

### URL Discovery
- SimpleSpider class uses Scrapy to discover and collect URLs within the target domain
- Follows links while respecting:
  - Domain boundaries
  - Base path restrictions
  - Page limits
  - File type filtering (ignores .css, .js, images)

### Markdown Conversion
- Uses MarkItDown library directly for HTML to markdown conversion
- Each discovered URL is processed independently
- Markdown files are saved to src/data directory
- Simple filename generation from URL paths

## Benefits of New Implementation
- Separation of concerns: URL discovery separate from content conversion
- Simplified error handling and recovery
- Direct use of MarkItDown's conversion capabilities
- Reduced complexity in file handling and storage
- More maintainable codebase with fewer moving parts

## Usage
```python
result = await scrape(
    query="https://domain.com/docs/",
    page_limit=1  # Optional, defaults to 1. Set to None for unlimited pages
)
```

## Output
The tool returns a list of dictionaries containing:
- url: Original page URL
- path: Local file path where markdown was saved
- content: Markdown content

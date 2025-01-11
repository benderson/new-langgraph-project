# System Architecture

## Overview

This project implements a LangGraph-based agent system designed for web research and data extraction. The system utilizes LangGraph (>0.2.62) and LangChain (>0.3) to create flexible, configurable agent workflows.

## Core Components

### Graph System (`src/agent/graph.py`)
- Implements a `StateGraph` based workflow system
- Defines the core agent behavior through node functions
- Supports asynchronous operations
- Integrates with LangSmith for monitoring and tracking
- Current implementation includes a basic node (`my_node`) that demonstrates the graph structure

### Tools System (`src/agent/tools.py`)
- Implements web scraping capabilities using Scrapy
- Features a custom `DocsSpider` for documentation site crawling
- Includes markdown conversion functionality
- Components:
  - `DocsSpider`: Custom Scrapy spider for web crawling
    - Configurable page limits
    - HTML to Markdown conversion
    - Content extraction and cleaning
    - Navigation within allowed domains
  - `ScrapingTool`: Management class for scraping operations
    - Configurable crawler settings
    - Temporary file handling
    - Asynchronous operation
  - `scrape` function: Main tool interface
    - Async implementation
    - Configurable page limits
    - Structured output with URLs and content
- Output Management:
  - Stores scraped content in `src/data` directory
  - Maintains original URL structure in file paths
  - Converts content to Markdown format

### Configuration System (`src/agent/configuration.py`)
- Implements a flexible configuration management system using dataclasses
- Supports runtime configuration through `RunnableConfig`
- Allows for configurable parameters that can be:
  - Pre-set when creating assistants
  - Modified during graph invocation
- Configuration values are type-safe and validated
- Extensible design allows for easy addition of new configuration parameters

### State Management (`src/agent/state.py`)
- Implements a dataclass-based state management system
- Defines the input/output interface for the agent
- Provides a structured approach to managing agent state
- Follows LangGraph's state management patterns
- Enables type-safe state transitions

## Workflow Architecture

### Graph Structure
```
[__start__] → [my_node]
```

The current graph implementation follows a simple linear flow:
1. Entry point (`__start__`)
2. Processing node (`my_node`)
3. Result output

### Node Implementation
- Nodes are implemented as async functions
- Each node receives:
  - Current state (`State`)
  - Runtime configuration (`RunnableConfig`)
- Nodes return dictionaries containing their output
- Supports integration with LangChain components

## Testing Strategy

### Unit Tests (`tests/unit_tests/`)
- Tests individual components in isolation
- Focuses on configuration validation
- Ensures component-level functionality

### Integration Tests (`tests/integration_tests/`)
- Tests full graph execution
- Validates end-to-end workflows
- Uses LangSmith's unit testing utilities
- Ensures proper state management and transitions

### Scraping Tests (`tests/test_scrape.py`)
- Tests web scraping functionality
- Validates:
  - Page limit enforcement
  - File creation and storage
  - Data directory management
  - URL to file path conversion
- Includes cleanup procedures
- Provides detailed logging of:
  - Pages scraped
  - File creation
  - Error handling

## Data Management

### Scraping Output
- Scraped content is stored in `src/data` directory
- File naming preserves original URL structure
- Content is stored in Markdown format
- Metadata includes:
  - Original URL
  - Local file path
  - Converted content

## Future Considerations

### Extensibility Points
1. Additional graph nodes for specific tasks
2. Enhanced configuration parameters
3. Extended state management for complex workflows
4. Integration with external services

### Recommended Practices
1. Use type hints consistently
2. Implement comprehensive tests for new components
3. Document configuration parameters
4. Maintain backward compatibility in state structures

## Development Guidelines

### Adding New Features
1. Define new configuration parameters in `Configuration` class
2. Implement new state attributes in `State` class
3. Create new node functions in the graph
4. Add corresponding test coverage

### Configuration Management
1. Use the `Configuration` class for all configurable parameters
2. Document default values and acceptable ranges
3. Implement validation where necessary
4. Consider runtime performance implications

### Testing Requirements
1. Unit tests for new components
2. Integration tests for workflow changes
3. Use LangSmith's testing utilities
4. Validate configuration edge cases

## Deployment Considerations

### LangSmith Integration
- Graph name is set for LangSmith tracking
- Supports monitoring and debugging
- Enables performance analysis

### Runtime Configuration
- Supports dynamic configuration through `RunnableConfig`
- Allows for environment-specific settings
- Enables A/B testing and experimentation

## Documentation Standards

### Code Documentation
- Use docstrings for all public functions
- Include type hints
- Document configuration parameters
- Explain state transitions

### Architecture Updates
- Keep this document updated with new components
- Document major architectural decisions
- Include diagrams for complex workflows
- Maintain version compatibility notes

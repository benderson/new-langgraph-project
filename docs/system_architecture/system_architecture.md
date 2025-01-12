# System Architecture

## Overview

This project implements a LangGraph-based agent system designed for web research and data extraction. The system utilizes LangGraph (>0.2.62) and LangChain (>0.3) to create flexible, configurable agent workflows.

## Core Components

### Tools System (`src/agent/tools/`)
- Implements reusable tools for agent operations
- Includes a powerful web scraping tool with multiple modes:
  - Single page scraping
  - Directory-level scraping (recursive and non-recursive)
  - Domain-level scraping
  - Auto-detection mode
- Tools are integrated with LangChain's tool system
- Supports configuration injection through RunnableConfig

### Graph System (`src/agent/graph.py`)
- Implements a `StateGraph` based workflow system
- Defines the core agent behavior through node functions
- Supports asynchronous operations
- Integrates with LangSmith for monitoring and tracking
- Current implementation includes a basic node (`my_node`) that demonstrates the graph structure

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
[__start__] → [my_node] → [tool_nodes]
```

The current graph implementation supports:
1. Entry point (`__start__`)
2. Processing node (`my_node`)
3. Tool execution nodes
   - Web scraping operations
   - Data extraction tasks
4. Result output

### Tool Integration
- Tools are injected into the graph via RunnableConfig
- Supports async execution for network operations
- Maintains state consistency during tool execution
- Provides error handling and recovery mechanisms

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
5. Test tool functionality with various inputs
6. Validate scraping behavior across different modes

### Data Management

#### Scraping Output
- Scraped content is stored in markdown format
- Organized by domain and path structure
- Supports HTML to Markdown conversion
- Maintains URL references for traceability

## Deployment Considerations

### LangSmith Integration
- Graph name is set for LangSmith tracking
- Supports monitoring and debugging
- Enables performance analysis

### Runtime Configuration
- Supports dynamic configuration through `RunnableConfig`
- Allows for environment-specific settings
- Enables A/B testing and experimentation

## Tool Development Guidelines

### Adding New Tools
1. Implement tool logic in dedicated modules
2. Create async function wrappers in tools.py
3. Add configuration parameters as needed
4. Include comprehensive error handling
5. Document input/output specifications

### Scraping Tool Best Practices
1. Respect website terms of service
2. Implement rate limiting
3. Handle network errors gracefully
4. Validate input URLs
5. Monitor storage usage

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

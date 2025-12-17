# Mercury Error Handling

This module provides standardized error handling for Mercury components, including custom exception types, error codes, and utility functions.

## Overview

The Mercury Error Handling module provides a consistent way to handle errors across the Mercury codebase. It includes a set of custom exception types, error codes, and utility functions for formatting errors for API responses.

## Key Components

- **ErrorCode**: Enum defining standard error codes for Mercury components.
- **MercuryError**: Base exception class for all Mercury errors.
- **ConnectionError**: Error related to connection handling.
- **MCPError**: Error related to MCP operations.
- **AgentError**: Error related to agent operations.
- **format_error_for_response**: Utility function to format an exception for API response.
- **collect_validation_errors**: Utility function to collect validation errors into a standardized format.

## Usage

The recommended way to use this module is through the high-level classes and functions exposed in the `__init__.py` file:

```python
from mercury.errors import MercuryError, ErrorCode, format_error_for_response

# Create a custom error
error = MercuryError(
    code=ErrorCode.INVALID_ARGUMENT,
    message="Invalid parameter value",
    details={"param": "value", "expected": "string"}
)

# Format an error for API response
response_data = format_error_for_response(error)
```

## Error Handling Best Practices

1. **Use Specific Error Types**: Use the most specific error type for the situation (e.g., `ConnectionError` for connection issues, `MCPError` for MCP-related issues).

2. **Include Detailed Information**: When creating errors, include detailed information in the message and details dictionary to help with debugging.

3. **Preserve Original Exceptions**: When catching and re-raising exceptions, include the original exception as the `cause` parameter to preserve the full error context.

4. **Consistent Error Formatting**: Use the `format_error_for_response` function to ensure consistent error formatting in API responses.

5. **Error Codes**: Use the `ErrorCode` enum to ensure consistent error codes across the codebase.

## Example

```python
from mercury.errors import AgentError, ErrorCode

try:
    # Some code that might fail
    result = await run_agent(config, prompt)
    return result
except Exception as e:
    # Wrap the exception in a Mercury error
    raise AgentError(
        message=f"Failed to run agent: {str(e)}",
        code=ErrorCode.AGENT_EXECUTION_ERROR,
        details={"prompt": prompt[:100] + "..."},
        cause=e
    )

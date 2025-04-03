# ServiceNow Browser Use

A Python library for automating ServiceNow browser interactions using Selenium and AI-powered agents.

## Features

- 🤖 AI-powered browser automation
- 🔄 Selenium-based browser control
- 🎯 ServiceNow-specific DOM handling
- 📝 Action recording and playback
- 🔍 Telemetry and logging support

## Installation

```bash
pip install servicenow-browser-use
```

## Quick Start

```python
from servicenow_browser_use import Browser, BrowserConfig, Agent

# Configure the browser
config = BrowserConfig(
    headless=False,  # Set to True for headless mode
    implicit_wait=10
)

# Initialize the browser
browser = Browser(config)

# Create an agent
agent = Agent(browser)

# Navigate to ServiceNow
browser.get("https://your-instance.service-now.com")

# Let the agent perform actions
agent.execute_task("Navigate to incident list and create a new incident")
```

## Configuration

Create a `.env` file in your project root:

```env
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_KEY=your_key
SERVICENOW_URL=your_instance_url
ANONYMIZED_TELEMETRY=false
```

## Documentation

For detailed documentation, please visit [documentation link].

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Codebase Structure

> The code structure inspired by https://github.com/Netflix/dispatch.

Very good structure on how to make a scalable codebase is also in [this repo](https://github.com/zhanymkanov/fastapi-best-practices).

Just a brief document about how we should structure our backend codebase.

## Code Structure

```markdown
src/
/<service name>/
models.py
services.py
prompts.py
views.py
utils.py
routers.py

    	/_<subservice name>/
```

### Service.py

Always a single file, except if it becomes too long - more than ~500 lines, split it into \_subservices

### Views.py

Always split the views into two parts

```python
# All
...

# Requests
...

# Responses
...
```

If too long → split into multiple files

### Prompts.py

Single file; if too long → split into multiple files (one prompt per file or so)

### Routers.py

Never split into more than one file

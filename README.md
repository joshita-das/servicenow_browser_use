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

## Components

### Agent Module (`agent/`)
The agent module provides AI-powered automation capabilities:
- `service.py`: Core agent service implementing AI-driven browser automation
- `prompts.py`: System prompts and templates for AI interactions
- `views.py`: Data models for agent actions and responses
- `message_manager/`: Handles communication between agent and browser

### Browser Module (`browser/`)
Handles browser automation and recording:
- `browser.py`: Main browser controller with Selenium integration
- `context.py`: Browser context management and state tracking
- `selenium_recorder.py`: Records browser actions for replay
- `streamlined_recorder.py`: Optimized recording functionality
- `shadow_dom.py`: Handles shadow DOM elements in ServiceNow
- `recording_manager.py`: Manages browser action recordings

### Controller Module (`controller/`)
Coordinates between different components:
- `service.py`: Main controller service orchestrating automation
- `registry/`: Component registration and management
- `views.py`: Controller data models and interfaces

### DOM Module (`dom/`)
Handles DOM manipulation and analysis:
- `service.py`: DOM manipulation service
- `history_tree_processor/`: Processes DOM history
- `buildDomTree.js`: JavaScript for DOM tree construction
- `views.py`: DOM-related data models

### Utils Module (`utils/`)
Common utility functions and helpers:
- Various helper functions for the entire library
- Shared functionality across modules

### Selenium Generator
Converts agent recordings to Selenium scripts:
- `selenium_generator.py`: Generates Java Selenium scripts from recordings
- Supports common actions: clicks, inputs, scrolling, keyboard events

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

## Advanced Usage

### Recording Browser Actions
```python
from servicenow_browser_use import SeleniumRecorder

recorder = SeleniumRecorder(browser)
recorder.start_recording()
# Perform actions
recording = recorder.stop_recording()
```

### Converting Recordings to Selenium
```python
from servicenow_browser_use import convert_agent_recording_to_selenium

selenium_script = convert_agent_recording_to_selenium("recording.json")
```

### DOM Manipulation
```python
from servicenow_browser_use import DomService

dom = DomService(browser)
element = dom.find_element("css_selector", "#incident_number")
```

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

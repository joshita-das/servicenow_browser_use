# ServiceNow Browser Use

A Python library for automating ServiceNow browser interactions using Selenium and AI-powered agents.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Citation](#citation)
- [Components](#components)
  - [Agent Module](#agent-module-agent)
  - [Browser Module](#browser-module-browser)
  - [Controller Module](#controller-module-controller)
  - [DOM Module](#dom-module-dom)
  - [Utils Module](#utils-module-utils)
  - [Selenium Generator](#selenium-generator)
- [Quick Start](#quick-start)
- [Example Usage](#example-usage)
- [Configuration](#configuration)
- [Advanced Usage](#advanced-usage)
  - [Recording Browser Actions](#recording-browser-actions)
  - [Converting Recordings to Selenium](#converting-recordings-to-selenium)
  - [DOM Manipulation](#dom-manipulation)
- [Contributing](#contributing)
- [License](#license)
- [Codebase Structure](#codebase-structure)

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

## Citation

If you use this library in your research, please cite:

```bibtex
@software{browser_use2024,
  author = {Müller, Magnus and Žunič, Gregor},
  title = {Browser Use: Enable AI to control your browser},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/browser-use/browser-use}
}
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

## Example Usage

Here's a complete example of how to use the library with advanced features:

```python
import sys
import asyncio
from langchain_openai import AzureChatOpenAI
from servicenow_browser_use import Agent
from dotenv import load_dotenv
from pydantic import SecretStr
from servicenow_browser_use import BrowserConfig
from servicenow_browser_use.browser.browser import Browser
from servicenow_browser_use.browser.context import BrowserContextConfig
from servicenow_browser_use.browser.streamlined_recorder import StreamlinedRecorder
import os
import logging
import subprocess
from datetime import datetime
import time
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main(task, llm_model):
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    os.makedirs("logs/conversation", exist_ok=True)
    
    # Clean up any existing Chrome instances
    subprocess.run(["pkill", "Chrome"], capture_output=True)
    await asyncio.sleep(2)
    
    # Configure browser with advanced settings
    config = BrowserConfig(
        chrome_instance_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        disable_security=True,
        extra_chromium_args=[
            '--remote-debugging-port=9222',
            '--disable-web-security',
            '--disable-site-isolation-trials',
            '--enable-logging',
            '--v=1',
            '--no-sandbox',
            '--disable-dev-shm-usage'
        ],
        new_context_config=BrowserContextConfig(
            save_recording_path='output',
            browser_window_size={'width': 1280, 'height': 720},
            wait_for_network_idle_page_load_time=2.0,
            minimum_wait_page_load_time=1.0
        )
    )

    # Initialize browser
    browser = Browser(config=config)
    
    try:
        # Initialize the browser and get the Playwright browser instance
        playwright_browser = await browser.get_playwright_browser()
        if not playwright_browser:
            raise Exception("Failed to initialize browser")
        
        # Wait for browser to initialize
        await asyncio.sleep(3)
        
        # Initialize LLM
        llm = AzureChatOpenAI(
            model=llm_model,
            api_version="2024-10-21",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=SecretStr(os.getenv("AZURE_OPENAI_KEY", "")),
        )
        
        # Initialize agent with browser
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            save_conversation_path="logs/conversation",
        )

        # Run the agent and get results
        result = await agent.run()
        
        if result:
            print("Task completed successfully!")
            print("Final state:", result)
        else:
            print("Task failed or returned no results")
            
    except Exception as e:
        logger.error(f"Error during agent execution: {str(e)}")
        raise
    finally:
        # Clean up
        try:
            if browser:
                await browser.close()
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
        
        try:
            subprocess.run(["pkill", "Chrome"], capture_output=True)
        except Exception as e:
            logger.error(f"Error during Chrome cleanup: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    
    task = "login with username: admin, password: admin, click on 'New' button and check if 'Flow' tab is present"
    llm_model = "gpt-4"
    asyncio.run(main(task, llm_model))

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

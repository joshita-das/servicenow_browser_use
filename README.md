# ServiceNow Browser Use

A Python library for automating ServiceNow browser interactions using AI-powered agents and Selenium.

## Table of Contents
- [Installation](#installation)
- [Inspiration](#inspiration)
- [Quick Start](#quick-start)
- [Example Explanation](#example-explanation)
- [Configuration](#configuration)
- [Features](#features)
  - [Browser Automation](#browser-automation)
  - [Agent Capabilities](#agent-capabilities)
  - [Recording Features](#recording-features)
- [License](#license)

## Installation

```bash
pip install servicenow-browser-use
```

## Inspiration

This project is inspired by the work of Müller and Žunič in their Browser Use project. If you use this library in your research, please cite:

```bibtex
@software{browser_use2024,
  author = {Müller, Magnus and Žunič, Gregor},
  title = {Browser Use: Enable AI to control your browser},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/browser-use/browser-use}
}
```

## Quick Start

Here's a complete example of how to use the library:

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
import os
import logging
import subprocess
import time
import requests

logger = logging.getLogger(__name__)

def wait_for_chrome_debugger(port=9222, max_retries=10, retry_interval=1):
    """Wait for Chrome debugger to be available on the specified port."""
    for i in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{port}/json/version")
            if response.status_code == 200:
                logger.info("Chrome debugger is available")
                return True
        except requests.exceptions.ConnectionError:
            logger.debug(f"Chrome debugger not available yet (attempt {i+1}/{max_retries})")
            time.sleep(retry_interval)
    return False

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
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=SecretStr(os.getenv("AZURE_OPENAI_KEY", "")),
            deployment_name="gpt-4",
            temperature=0.0,
            model_kwargs={
                "messages": [{"role": "system", "content": "You are a helpful assistant."}]
            }
        )
        
        # Format task as a string and wrap it in a message format
        task_str = str(task)
        task_message = [{"role": "user", "content": task_str}]
        
        # Initialize agent with browser
        agent = Agent(
            task=task_message,
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    task = "login with username: admin, password: admin, click on 'New' button and check if 'Flow' tab is present"
    llm_model = "gpt-4"
    asyncio.run(main(task, llm_model))
```

### Example Explanation

This example demonstrates how to automate a ServiceNow workflow using AI. Here's what the script does:

1. **Initialization and Setup**
   - Creates necessary directories for output and logs
   - Cleans up any existing Chrome instances
   - Sets up logging configuration

2. **Browser Configuration**
   - Configures Chrome with specific settings for ServiceNow automation
   - Enables remote debugging for browser control
   - Sets up security and performance parameters
   - Configures window size and network wait times

3. **AI Agent Setup**
   - Initializes Azure OpenAI with GPT-4
   - Configures the model with specific parameters
   - Sets up proper message formatting for the AI agent

4. **Task Execution**
   - The example task: "login with username: admin, password: admin, click on 'New' button and check if 'Flow' tab is present"
   - The agent will:
     - Navigate to the ServiceNow instance
     - Log in with provided credentials
     - Click the 'New' button
     - Verify the presence of the 'Flow' tab
     - Record all actions for potential Selenium script generation

5. **Cleanup and Error Handling**
   - Properly closes the browser
   - Cleans up Chrome processes
   - Handles and logs any errors that occur

The script demonstrates key features:
- AI-powered browser automation
- Natural language task execution
- Action recording
- Error handling and logging
- Browser state management

## Configuration

Create a `.env` file in your project root:

```
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_KEY=your_key
SERVICENOW_URL=your_instance_url
ANONYMIZED_TELEMETRY=false
```

## Features

### Browser Automation
- AI-powered browser control
- Shadow DOM support
- Action recording and playback
- Selenium script generation

### Agent Capabilities
- Natural language task execution
- Context-aware decision making
- Automated form filling
- Element interaction

### Recording Features
- Streamlined action recording
- Selenium code generation
- Browser state tracking
- Network activity monitoring

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


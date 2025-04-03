import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

logger = logging.getLogger(__name__)

class SeleniumRecorder:
    def __init__(self, recording_path: str = "output", browser_instance=None):
        self.recording_path = recording_path
        self.start_time = datetime.now()
        self.actions: List[Dict] = []
        self.screenshots: List[Dict] = []
        self.driver = None
        self.browser_instance = browser_instance
        self.setup_driver()

    def setup_driver(self):
        try:
            if self.browser_instance:
                # Get the debugging port from the browser instance
                port = 9222  # Default port used by servicenow_browser_use
                
                # Connect to the existing Chrome instance
                options = Options()
                options.add_experimental_option("debuggerAddress", f"localhost:{port}")
                options.add_argument("--disable-web-security")
                options.add_argument("--disable-site-isolation-trials")
                
                # Create Chrome service
                service = Service()
                
                # Connect to the existing Chrome instance
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info("Successfully connected to existing Chrome instance")
                
                # Switch to the first tab (should be the one used by the agent)
                self.driver.switch_to.window(self.driver.window_handles[0])
            else:
                # Fallback to creating a new Chrome instance (for standalone usage)
                options = Options()
                options.add_argument("--remote-debugging-port=9223")  # Different port from Playwright
                options.add_argument("--disable-web-security")
                options.add_argument("--disable-site-isolation-trials")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1280,720")
                
                service = Service()
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info("Created new Chrome instance for standalone recording")
            
            # Take initial screenshot
            self.take_screenshot()
            
        except WebDriverException as e:
            logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise

    def take_screenshot(self) -> str:
        try:
            # Ensure we're on the correct tab
            if self.browser_instance:
                self.driver.switch_to.window(self.driver.window_handles[0])
                
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshots/screenshot_{timestamp}.png"
            self.driver.save_screenshot(filename)
            self.screenshots.append({
                "timestamp": datetime.now().isoformat(),
                "path": filename
            })
            logger.info(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            return ""

    def record_action(self, action_type: str, element: Optional[Dict] = None, **kwargs):
        try:
            # Ensure we're on the correct tab
            if self.browser_instance:
                self.driver.switch_to.window(self.driver.window_handles[0])
            
            # Create action record
            action = {
                "type": action_type,
                "timestamp": datetime.now().isoformat(),
                **kwargs
            }
            
            # Add element info if available
            if element:
                action["element"] = element
            
            self.actions.append(action)
            logger.info(f"Recorded action: {action_type}")
            
            # Take screenshot after action
            self.take_screenshot()
            
        except Exception as e:
            logger.error(f"Failed to record action: {str(e)}")

    def get_element_info(self, element) -> Dict:
        try:
            # Get element attributes using JavaScript
            element_info = self.driver.execute_script("""
                function getElementInfo(element) {
                    return {
                        tagName: element.tagName,
                        id: element.id || '',
                        className: element.className || '',
                        value: element.value || '',
                        role: element.getAttribute('role'),
                        'aria-label': element.getAttribute('aria-label')
                    };
                }
                return getElementInfo(arguments[0]);
            """, element)

            # Get XPath
            xpath = self.driver.execute_script("""
                function getXPath(element) {
                    if (!element) return '';
                    const idx = (sib, name) => sib 
                        ? idx(sib.previousElementSibling, name||sib.tagName) + (sib.tagName == name)
                        : 1;
                    const segs = elm => !elm || elm.nodeType !== 1 
                        ? ['']
                        : elm.id && document.getElementById(elm.id) === elm
                            ? [`//*[@id="${elm.id}"]`]
                            : [...segs(elm.parentNode), `${elm.tagName}[${idx(elm)}]`];
                    return segs(element).join('/').toLowerCase();
                }
                return getXPath(arguments[0]);
            """, element)

            # Get shadow DOM path
            shadow_path = self.driver.execute_script("""
                function getShadowPath(element) {
                    let path = [];
                    let currentElement = element;
                    
                    while (currentElement && currentElement !== document.documentElement) {
                        let host = {
                            tagName: currentElement.tagName,
                            id: currentElement.id || '',
                            className: currentElement.className || ''
                        };
                        
                        let hasShadowRoot = Boolean(currentElement.shadowRoot);
                        path.unshift({
                            host: host,
                            shadowRoot: hasShadowRoot
                        });
                        
                        if (currentElement.assignedSlot) {
                            currentElement = currentElement.assignedSlot;
                        } else if (currentElement.parentNode && currentElement.parentNode.host) {
                            currentElement = currentElement.parentNode.host;
                        } else {
                            currentElement = currentElement.parentNode;
                        }
                    }
                    
                    return path;
                }
                return getShadowPath(arguments[0]);
            """, element)

            return {
                **element_info,
                "xpath": xpath,
                "shadowPath": shadow_path
            }
        except Exception as e:
            logger.error(f"Failed to get element info: {str(e)}")
            return {}

    def get_element_xpath(self, element) -> str:
        try:
            script = """
            function getXPath(element) {
                if (!element) return '';
                const idx = (sib, name) => sib 
                    ? idx(sib.previousElementSibling, name||sib.tagName) + (sib.tagName == name)
                    : 1;
                const segs = elm => !elm || elm.nodeType !== 1 
                    ? ['']
                    : elm.id && document.getElementById(elm.id) === elm
                        ? [`//*[@id="${elm.id}"]`]
                        : [...segs(elm.parentNode), `${elm.tagName}[${idx(elm)}]`];
                return segs(element).join('/').toLowerCase();
            }
            return getXPath(arguments[0]);
            """
            return self.driver.execute_script(script, element)
        except Exception as e:
            logger.error(f"Failed to get element XPath: {str(e)}")
            return ""

    def save_recording(self):
        try:
            recording = {
                "browser_type": "chrome",
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "commands": self.actions,  # Use actions as commands
                "screenshots": self.screenshots,
                "elements": [],  # We'll populate this with unique elements from actions
                "actions": self.actions
            }
            
            # Extract unique elements from actions
            unique_elements = {}
            for action in self.actions:
                if action.get("element"):
                    element_key = f"{action['element'].get('tagName', '')}_{action['element'].get('id', '')}_{action['element'].get('className', '')}"
                    if element_key not in unique_elements:
                        unique_elements[element_key] = action["element"]
            
            recording["elements"] = list(unique_elements.values())
            
            # Create output directory if it doesn't exist
            os.makedirs(self.recording_path, exist_ok=True)
            
            # Save recording to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.recording_path, f"selenium_recording_{timestamp}.json")
            
            with open(filename, "w") as f:
                json.dump(recording, f, indent=2)
            
            logger.info(f"Recording saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save recording: {str(e)}")
            return None

    def close(self):
        try:
            if self.driver and not self.browser_instance:
                # Only close if we created our own instance
                self.driver.quit()
                logger.info("Chrome driver closed successfully")
        except Exception as e:
            logger.error(f"Failed to close Chrome driver: {str(e)}") 
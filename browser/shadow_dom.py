"""
Shadow DOM and Selenium script generation functionality.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional

from playwright.async_api import Page, ConsoleMessage

logger = logging.getLogger(__name__)

async def setup_shadow_dom_listeners(page: Page):
    """Set up event listeners for shadow DOM elements."""
    await page.evaluate("""() => {
        function addEventListeners(root) {
            // Click listener
            root.addEventListener('click', (event) => {
                const element = event.target;
                const rect = element.getBoundingClientRect();
                
                // Get XPath
                function getXPath(element) {
                    if (element.id) {
                        return `//*[@id='${element.id}']`;
                    }
                    if (element === document.body) {
                        return '/html/body';
                    }
                    let path = '';
                    let current = element;
                    while (current && current.nodeType === 1) {
                        let index = 1;
                        let sibling = current.previousSibling;
                        while (sibling) {
                            if (sibling.nodeType === 1 && sibling.tagName === current.tagName) {
                                index++;
                            }
                            sibling = sibling.previousSibling;
                        }
                        const tagName = current.tagName.toLowerCase();
                        path = `/${tagName}[${index}]${path}`;
                        current = current.parentNode;
                    }
                    return path;
                }
                
                // Get Shadow DOM path
                function getShadowPath(element) {
                    let path = [];
                    let current = element;
                    while (current) {
                        if (current.nodeType === 1) {
                            path.unshift({
                                host: {
                                    tagName: current.tagName,
                                    id: current.id,
                                    className: current.className
                                },
                                shadowRoot: current.shadowRoot ? true : false
                            });
                        }
                        current = current.parentNode || current.host;
                    }
                    return path;
                }
                
                console.log('__pw_click', JSON.stringify({
                    type: 'click',
                    timestamp: new Date().toISOString(),
                    element: {
                        tagName: element.tagName,
                        id: element.id,
                        className: element.className,
                        name: element.name,
                        type: element.type,
                        value: element.value || '',
                        role: element.getAttribute('role'),
                        'aria-label': element.getAttribute('aria-label'),
                        xpath: getXPath(element),
                        shadowPath: getShadowPath(element),
                        rect: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        }
                    },
                    coordinates: {
                        x: event.clientX,
                        y: event.clientY
                    }
                }));
            }, true);
            
            // Input listener
            root.addEventListener('input', (event) => {
                const element = event.target;
                const rect = element.getBoundingClientRect();
                
                console.log('__pw_input', JSON.stringify({
                    type: 'input',
                    timestamp: new Date().toISOString(),
                    element: {
                        tagName: element.tagName,
                        id: element.id,
                        className: element.className,
                        name: element.name,
                        type: element.type,
                        value: element.value || '',
                        role: element.getAttribute('role'),
                        'aria-label': element.getAttribute('aria-label'),
                        xpath: getXPath(element),
                        shadowPath: getShadowPath(element),
                        rect: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        }
                    },
                    value: element.value
                }));
            }, true);
        }
        
        // Add listeners to main document
        addEventListeners(document);
        
        // Add listeners to all shadow roots
        function addShadowRootListeners(root) {
            if (root.shadowRoot) {
                addEventListeners(root.shadowRoot);
                root.shadowRoot.querySelectorAll('*').forEach(element => {
                    if (element.shadowRoot) {
                        addShadowRootListeners(element);
                    }
                });
            }
        }
        
        // Initial scan for shadow roots
        document.querySelectorAll('*').forEach(element => {
            addShadowRootListeners(element);
        });
        
        // Observe for new shadow roots
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {
                        addShadowRootListeners(node);
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }""")

async def handle_console(msg: ConsoleMessage):
    """Handle console messages to capture events."""
    try:
        if msg.type == 'log':
            text = msg.text
            if text.startswith('__pw_click'):
                event_data = json.loads(text.replace('__pw_click ', ''))
                logger.info(f"Captured click event at coordinates: ({event_data.get('coordinates', {}).get('x')}, {event_data.get('coordinates', {}).get('y')})")
                if event_data.get('element'):
                    element = event_data['element']
                    logger.info(f"  Element: {element.get('tagName')}, XPath: {element.get('xpath')}, ShadowPath: {element.get('shadowPath')}")
            elif text.startswith('__pw_input'):
                event_data = json.loads(text.replace('__pw_input ', ''))
                logger.info(f"Captured input event with value: {event_data.get('value')}")
                if event_data.get('element'):
                    element = event_data['element']
                    logger.info(f"  Element: {element.get('tagName')}, XPath: {element.get('xpath')}, ShadowPath: {element.get('shadowPath')}")
    except Exception as e:
        logger.error(f"Error handling console message: {str(e)}")

def process_event(event: dict) -> Optional[Dict]:
    """Process an event into an action with element details."""
    event_type = event.get("type", "").replace("recorded-", "")
    event_data = event.get("detail", {})
    
    if not event_type or not event_data:
        return None
        
    element_data = event_data.get("element", {})
    
    # Check for shadow DOM elements
    has_shadow_dom = element_data.get("hasShadowDOM", False)
    elements_with_shadow = element_data.get("elementsWithShadowDOM", [])
    
    # If element has shadow DOM or is within a shadow DOM context
    if has_shadow_dom or elements_with_shadow:
        # Get the shadow root path
        shadow_path = element_data.get("shadowPath", [])
        if shadow_path:
            # Find the first shadow root in the path
            shadow_root = next((item for item in shadow_path if item.get("shadowRoot")), None)
            if shadow_root:
                # Update element data with shadow root information
                element_data["shadowRoot"] = shadow_root
                element_data["hasShadowDOM"] = True
    
    action = {
        "type": event_type,
        "timestamp": event_data.get("timestamp"),
        "element": {
            "tagName": element_data.get("tagName"),
            "id": element_data.get("id"),
            "className": element_data.get("className"),
            "name": element_data.get("name"),
            "type": element_data.get("type"),
            "role": element_data.get("role"),
            "aria-label": element_data.get("aria-label"),
            "xpath": element_data.get("xpath"),
            "shadowPath": element_data.get("shadowPath"),
            "hasShadowDOM": element_data.get("hasShadowDOM", False),
            "shadowRoot": element_data.get("shadowRoot"),
            "elementsWithShadowDOM": element_data.get("elementsWithShadowDOM", []),
            "rect": element_data.get("rect")
        } if element_data else None,
        "coordinates": {
            "x": event_data.get("x"),
            "y": event_data.get("y")
        } if event_type in ["click", "mouse_click"] else None,
        "value": event_data.get("value") if event_type in ["input", "input_text"] else None,
        "url": event_data.get("url") if event_type == "load" else None,
        "title": event_data.get("title") if event_type == "load" else None
    }
    
    return action

def generate_selenium_script(recording_data: list[Dict], output_file: str):
    """Generate Selenium Java script from recording data."""
    script = """package com.example.selenium;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.JavascriptExecutor;
import java.time.Duration;

public class GeneratedSeleniumScript {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        JavascriptExecutor js = (JavascriptExecutor) driver;
        
        try {
"""
    
    for action in recording_data:
        if action["type"] == "load":
            script += f'            driver.get("{action["url"]}");\n'
        elif action["type"] == "click":
            element = action["element"]
            if not element:
                continue
                
            # Handle shadow DOM elements
            if element.get("hasShadowDOM", False):
                script += '            // Handle shadow DOM element\n'
                if element.get("shadowRoot"):
                    shadow_root = element["shadowRoot"]
                    host = shadow_root.get("host", {})
                    script += f'            WebElement shadowHost = wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("{host.get("tagName", "")}{"#" + host.get("id", "") if host.get("id") else ""}{"." + host.get("className", "").replace(" ", ".") if host.get("className") else ""}"));\n'
                    script += '            WebElement element = (WebElement) js.executeScript("return arguments[0].shadowRoot", shadowHost);\n'
                else:
                    # Use XPath for shadow DOM elements
                    script += f'            WebElement element = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("{element["xpath"]}")));\n'
            else:
                # Regular element handling
                if element.get("id"):
                    script += f'            WebElement element = wait.until(ExpectedConditions.elementToBeClickable(By.id("{element["id"]}")));\n'
                elif element.get("xpath"):
                    script += f'            WebElement element = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("{element["xpath"]}")));\n'
                else:
                    continue
            script += '            element.click();\n'
        elif action["type"] == "input":
            element = action["element"]
            if not element:
                continue
                
            # Handle shadow DOM elements
            if element.get("hasShadowDOM", False):
                script += '            // Handle shadow DOM element\n'
                if element.get("shadowRoot"):
                    shadow_root = element["shadowRoot"]
                    host = shadow_root.get("host", {})
                    script += f'            WebElement shadowHost = wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("{host.get("tagName", "")}{"#" + host.get("id", "") if host.get("id") else ""}{"." + host.get("className", "").replace(" ", ".") if host.get("className") else ""}"));\n'
                    script += '            WebElement element = (WebElement) js.executeScript("return arguments[0].shadowRoot", shadowHost);\n'
                else:
                    # Use XPath for shadow DOM elements
                    script += f'            WebElement element = wait.until(ExpectedConditions.presenceOfElementLocated(By.xpath("{element["xpath"]}")));\n'
            else:
                # Regular element handling
                if element.get("id"):
                    script += f'            WebElement element = wait.until(ExpectedConditions.presenceOfElementLocated(By.id("{element["id"]}")));\n'
                elif element.get("xpath"):
                    script += f'            WebElement element = wait.until(ExpectedConditions.presenceOfElementLocated(By.xpath("{element["xpath"]}")));\n'
                else:
                    continue
            script += f'            element.sendKeys("{action["value"]}");\n'
    
    script += """        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            driver.quit();
        }
    }
}"""
    
    with open(output_file, "w") as f:
        f.write(script) 
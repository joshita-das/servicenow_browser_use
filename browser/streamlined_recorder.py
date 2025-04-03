"""
A streamlined recorder that captures essential information about browser actions.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from playwright.async_api import Browser, Page, ElementHandle

logger = logging.getLogger(__name__)

class StreamlinedRecorder:
    def __init__(self, browser: Browser, output_dir: str):
        """Initialize the streamlined recorder.
        
        Args:
            browser: The Playwright browser instance (should be the same instance used by the agent)
            output_dir: Directory to save recordings
        """
        self.browser = browser  # This should be the same browser instance used by the agent
        self.output_dir = output_dir
        self.recording_file = None
        self.actions = []
        self._page = None  # Will be set by BrowserContext
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

    async def start_recording(self):
        """Start recording browser actions"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recording_file = os.path.join(self.output_dir, f"streamlined_recording_{timestamp}.json")
        logger.info(f"Starting streamlined recording to {self.recording_file}")

    async def stop_recording(self) -> str:
        """Stop recording and save the actions to a JSON file"""
        if not self.recording_file:
            return None
        try:
            with open(self.recording_file, 'w') as f:
                json.dump(self.actions, f, indent=2)
            logger.info(f"Recording saved to {self.recording_file}")
            return self.recording_file
        except Exception as e:
            logger.error(f"Error saving recording: {e}")
            return None

    async def close(self):
        """Clean up resources"""
        await self.stop_recording()
        self._page = None  # Clear the page reference

    def set_page(self, page: Page):
        """Set the current page for recording"""
        self._page = page

    async def get_element_info(self, element: ElementHandle):
        """Get detailed information about an element."""
        try:
            if not self._page:
                logger.error("No page available for element info extraction")
                return None

            # Get basic element properties using JavaScript evaluation
            properties = await element.evaluate("""
                (el) => {
                    const computedStyle = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    
                    // Get XPath
                    function getXPath(element) {
                        if (element.id !== '')
                            return `//*[@id="${element.id}"]`;
                        if (element === document.body)
                            return '/html/body';
                            
                        let ix = 0;
                        const siblings = element.parentNode.childNodes;
                        for (let sibling of siblings) {
                            if (sibling === element)
                                return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                            if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                                ix++;
                        }
                    }

                    // Function to get element details
                    function getElementDetails(element) {
                        return {
                            tagName: element.tagName.toLowerCase(),
                            id: element.id,
                            classes: Array.from(element.classList),
                            attributes: Object.fromEntries(
                                Array.from(element.attributes).map(attr => [attr.name, attr.value])
                            ),
                            text: element.textContent?.trim(),
                            value: element.value,
                            type: element.type,
                            name: element.name,
                            role: element.getAttribute('role'),
                            ariaLabel: element.getAttribute('aria-label'),
                            ariaDescribedBy: element.getAttribute('aria-describedby'),
                            ariaLabelledBy: element.getAttribute('aria-labelledby'),
                            isVisible: computedStyle.display !== 'none' && 
                                     computedStyle.visibility !== 'hidden' && 
                                     computedStyle.opacity !== '0',
                            isInteractive: element.clickable || 
                                         element.typeable || 
                                         element.selectable ||
                                         element.tagName.toLowerCase() === 'button' ||
                                         element.tagName.toLowerCase() === 'a' ||
                                         (element.tagName.toLowerCase() === 'input' && 
                                          ['button', 'submit', 'reset', 'text', 'password', 'email', 'number', 'tel'].includes(element.type))
                        };
                    }

                    // Function to check if element has shadow DOM
                    function hasShadowDOM(element) {
                        return element.shadowRoot !== null;
                    }

                    // Function to get shadow root mode
                    function getShadowRootMode(element) {
                        const shadowRoot = element.shadowRoot;
                        return shadowRoot ? {
                            mode: shadowRoot.mode,
                            delegatesFocus: shadowRoot.delegatesFocus,
                            isClosed: shadowRoot.mode === 'closed'
                        } : null;
                    }

                    // Function to get all elements in shadow DOM
                    function getShadowElements(element, depth = 0, maxDepth = 5) {
                        if (depth > maxDepth) return [];
                        
                        const shadowRoot = element.shadowRoot;
                        if (!shadowRoot) return [];

                        const elements = [];
                        const walker = document.createTreeWalker(
                            shadowRoot,
                            NodeFilter.SHOW_ELEMENT,
                            null,
                            false
                        );

                        let node;
                        while (node = walker.nextNode()) {
                            const elementInfo = {
                                ...getElementDetails(node),
                                shadowChildren: getShadowElements(node, depth + 1, maxDepth),
                                hasShadowDOM: hasShadowDOM(node),
                                shadowRoot: getShadowRootMode(node)
                            };
                            elements.push(elementInfo);
                        }

                        return elements;
                    }

                    // Function to get all elements that might have shadow DOM
                    function getAllElementsWithShadowDOM(root) {
                        const elements = [];
                        const walker = document.createTreeWalker(
                            root,
                            NodeFilter.SHOW_ELEMENT,
                            null,
                            false
                        );

                        let node;
                        while (node = walker.nextNode()) {
                            if (hasShadowDOM(node)) {
                                elements.push(node);
                            }
                        }
                        return elements;
                    }

                    // Get shadow DOM info
                    const hasShadowRoot = hasShadowDOM(el);
                    const shadowRootInfo = hasShadowRoot ? getShadowRootMode(el) : null;
                    const shadowElements = hasShadowRoot ? getShadowElements(el) : [];
                    
                    // Get all elements that might have shadow DOM
                    const elementsWithShadow = getAllElementsWithShadowDOM(document.body);
                    
                    // Get element details
                    const elementDetails = getElementDetails(el);
                    
                    // Determine if element has shadow DOM
                    const finalHasShadowDOM = hasShadowRoot || elementsWithShadow.length > 0;
                    
                    return {
                        ...elementDetails,
                        xpath: getXPath(el),
                        hasShadowDOM: finalHasShadowDOM,
                        shadowRoot: shadowRootInfo,
                        shadowElements: shadowElements,
                        elementsWithShadowDOM: elementsWithShadow.map(el => ({
                            tagName: el.tagName.toLowerCase(),
                            id: el.id,
                            classes: Array.from(el.classList),
                            xpath: getXPath(el)
                        })),
                        rect: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        },
                        computedStyle: {
                            display: computedStyle.display,
                            visibility: computedStyle.visibility,
                            opacity: computedStyle.opacity,
                            position: computedStyle.position,
                            zIndex: computedStyle.zIndex
                        }
                    };
                }
            """)
            
            # Determine available actions based on element properties
            actions = []
            if properties['isInteractive']:
                if properties['tagName'] in ['button', 'a'] or 'clickable' in properties.get('attributes', {}):
                    actions.append('click')
                if properties['tagName'] == 'input' and properties.get('type') in ['text', 'password', 'email', 'number', 'tel']:
                    actions.append('type')
                if properties['tagName'] == 'select' or 'selectable' in properties.get('attributes', {}):
                    actions.append('select')
            
            properties['actions'] = actions
            return properties
            
        except Exception as e:
            logger.error(f"Error getting element info: {str(e)}")
            return None

    async def record_action(self, action_type: str, element: Optional[Dict] = None, **kwargs):
        """Record an action with element information."""
        try:
            action_data = {
                "timestamp": datetime.now().isoformat(),
                "action": action_type,
                "element": element,
                **kwargs
            }
            
            # Remove any binary data or screenshots
            if "screenshot" in action_data:
                del action_data["screenshot"]
            
            self.actions.append(action_data)
            logger.debug(f"Recorded action: {action_type}")
        except Exception as e:
            logger.error(f"Error recording action: {str(e)}") 
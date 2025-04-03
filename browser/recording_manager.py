import os
from datetime import datetime
from typing import Dict, Optional, List, Any
from playwright.async_api import Browser, Page, ElementHandle
import json
import logging

logger = logging.getLogger(__name__)

class RecordingManager:
    def __init__(self, browser: Browser, output_dir: str = "output"):
        self.browser = browser
        self.output_dir = output_dir
        self.recording_data = {
            'metadata': {
                'browser_type': 'chrome',
                'start_time': None,
                'end_time': None,
                'version': '1.0'
            },
            'actions': []
        }
        self._action_counter = 0

    async def start_recording(self):
        """Start recording browser actions"""
        self.recording_data['metadata']['start_time'] = datetime.now().isoformat()

    async def stop_recording(self):
        """Stop recording and save the recording data"""
        self.recording_data['metadata']['end_time'] = datetime.now().isoformat()
        
        # Save recording to file
        recording_file = os.path.join(
            self.output_dir,
            f"agent_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(recording_file, 'w') as f:
            json.dump(self.recording_data, f, indent=2)
            
        return recording_file

    async def get_element_info(self, element: ElementHandle) -> Dict[str, Any]:
        """Get detailed element information including XPath, shadow DOM path, and other attributes"""
        try:
            # Get basic element properties
            basic_info = await element.evaluate("""element => {
                const info = {
                    tagName: element.tagName.toLowerCase(),
                    id: element.id || '',
                    text: element.textContent?.trim() || ''
                };
                // Only include non-empty attributes
                const attrs = Array.from(element.attributes)
                    .filter(attr => attr.value)
                    .reduce((acc, attr) => {
                        acc[attr.name] = attr.value;
                        return acc;
                    }, {});
                if (Object.keys(attrs).length > 0) {
                    info.attributes = attrs;
                }
                return info;
            }""")

            # Get XPath
            xpath = await element.evaluate("""element => {
                const getXPath = function(element) {
                    if (!element) return '';
                    if (element.id) return `//*[@id="${element.id}"]`;
                    if (element.className) return `//*[contains(@class, "${element.className}")]`;
                    const idx = (sib, name) => sib 
                        ? idx(sib.previousElementSibling, name||sib.tagName) + (sib.tagName == name)
                        : 1;
                    const segs = elm => !elm || elm.nodeType !== 1 
                        ? ['']
                        : [...segs(elm.parentNode), `${elm.tagName}[${idx(elm)}]`];
                    return segs(element).join('/').toLowerCase();
                };
                return getXPath(element);
            }""")

            # Get shadow DOM path with detailed information
            shadow_info = await element.evaluate("""element => {
                const getShadowPath = function(element) {
                    let path = [];
                    let currentElement = element;
                    
                    while (currentElement && currentElement !== document.documentElement) {
                        let elementInfo = {
                            tagName: currentElement.tagName.toLowerCase()
                        };
                        
                        // Add ID if exists
                        if (currentElement.id) {
                            elementInfo.id = currentElement.id;
                        }
                        
                        // Add class if exists
                        if (currentElement.className) {
                            elementInfo.className = currentElement.className;
                        }
                        
                        // Add shadow root info if exists
                        if (currentElement.shadowRoot) {
                            elementInfo.hasShadowRoot = true;
                        }
                        
                        // Add index among siblings
                        let siblings = Array.from(currentElement.parentElement?.children || []);
                        elementInfo.index = siblings.indexOf(currentElement);
                        
                        path.unshift(elementInfo);
                        
                        if (currentElement.assignedSlot) {
                            currentElement = currentElement.assignedSlot;
                        } else if (currentElement.parentNode?.host) {
                            currentElement = currentElement.parentNode.host;
                        } else {
                            currentElement = currentElement.parentNode;
                        }
                    }
                    return path;
                };
                return getShadowPath(element);
            }""")

            element_info = {
                'basic': basic_info,
                'xpath': xpath,
                'shadowDomPath': shadow_info
            }

            # Only include these if they're true
            if await element.is_visible():
                element_info['isVisible'] = True
            if await element.is_enabled():
                element_info['isEnabled'] = True

            # Only include bounding box if element is visible
            if await element.is_visible():
                box = await element.bounding_box()
                if box:
                    element_info['boundingBox'] = box

            return element_info
        except Exception as e:
            logger.error(f"Error getting element info: {str(e)}")
            return {
                'error': str(e)
            }

    async def record_action(self, action_type: str, element: Optional[ElementHandle] = None, **kwargs):
        """Record a browser action with comprehensive information"""
        self._action_counter += 1
        
        action = {
            'id': self._action_counter,
            'timestamp': datetime.now().isoformat(),
            'type': action_type
        }

        # Add element information if available
        if element:
            try:
                element_info = await self.get_element_info(element)
                action['element'] = element_info
            except Exception as e:
                logger.error(f"Error recording element info: {str(e)}")
                action['element'] = {'error': str(e)}

        # Add page state information
        if 'state' in kwargs:
            state = kwargs['state']
            page_state = {}
            
            # Only include URL if it's not about:blank
            if state.get('url') and state['url'] != 'about:blank':
                page_state['url'] = state['url']
            
            # Only include title if it's not empty
            if state.get('title'):
                page_state['title'] = state['title']
            
            # Only include tabs if there are multiple tabs
            if state.get('tabs') and len(state['tabs']) > 1:
                page_state['tabs'] = [{
                    'id': tab.get('page_id'),
                    'url': tab.get('url'),
                    'title': tab.get('title')
                } for tab in state['tabs'] if tab.get('url') != 'about:blank']
            
            if page_state:
                action['pageState'] = page_state

        # Add any additional parameters (excluding None values)
        params = {k: v for k, v in kwargs.items() if k != 'state' and v is not None}
        if params:
            action['parameters'] = params

        # Record any errors
        if 'error' in kwargs:
            action['status'] = 'failed'
            action['error'] = str(kwargs['error'])

        self.recording_data['actions'].append(action)
        return action

    async def close(self):
        """Clean up resources"""
        pass 
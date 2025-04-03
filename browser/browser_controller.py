from playwright.async_api import async_playwright, Browser, Page, ElementHandle
from typing import Dict, Optional, List, Any
import logging
from .streamlined_recorder import StreamlinedRecorder

logger = logging.getLogger(__name__)

class BrowserController:
    def __init__(self, output_dir: str = "output"):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.recorder: Optional[StreamlinedRecorder] = None
        self.output_dir = output_dir

    async def start(self):
        """Start the browser and initialize recording"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        self.recorder = StreamlinedRecorder(self.browser, self.output_dir)
        await self.recorder.start_recording()

    async def stop(self):
        """Stop the browser and save recording"""
        if self.recorder:
            await self.recorder.stop_recording()
        if self.browser:
            await self.browser.close()

    async def navigate(self, url: str):
        """Navigate to a URL and record the action"""
        try:
            await self.page.goto(url)
            await self.recorder.record_action(
                'navigate',
                state={
                    'url': url,
                    'title': await self.page.title()
                }
            )
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            await self.recorder.record_action('navigate', error=str(e))

    async def click(self, selector: str):
        """Click an element and record the action"""
        try:
            element = await self.page.wait_for_selector(selector)
            if element:
                await element.click()
                await self.recorder.record_action('click', element=element)
            else:
                raise Exception(f"Element not found: {selector}")
        except Exception as e:
            logger.error(f"Click error: {str(e)}")
            await self.recorder.record_action('click', error=str(e))

    async def type(self, selector: str, text: str):
        """Type text into an element and record the action"""
        try:
            element = await self.page.wait_for_selector(selector)
            if element:
                await element.fill(text)
                await self.recorder.record_action('type', element=element, text=text)
            else:
                raise Exception(f"Element not found: {selector}")
        except Exception as e:
            logger.error(f"Type error: {str(e)}")
            await self.recorder.record_action('type', error=str(e))

    async def get_text(self, selector: str) -> str:
        """Get text from an element and record the action"""
        try:
            element = await self.page.wait_for_selector(selector)
            if element:
                text = await element.text_content()
                await self.recorder.record_action('get_text', element=element, text=text)
                return text
            else:
                raise Exception(f"Element not found: {selector}")
        except Exception as e:
            logger.error(f"Get text error: {str(e)}")
            await self.recorder.record_action('get_text', error=str(e))
            return ""

    async def get_attribute(self, selector: str, attribute: str) -> str:
        """Get attribute from an element and record the action"""
        try:
            element = await self.page.wait_for_selector(selector)
            if element:
                value = await element.get_attribute(attribute)
                await self.recorder.record_action(
                    'get_attribute',
                    element=element,
                    attribute=attribute,
                    value=value
                )
                return value
            else:
                raise Exception(f"Element not found: {selector}")
        except Exception as e:
            logger.error(f"Get attribute error: {str(e)}")
            await self.recorder.record_action('get_attribute', error=str(e))
            return ""

    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> Optional[ElementHandle]:
        """Wait for an element to appear and record the action"""
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            if element:
                await self.recorder.record_action('wait_for_selector', element=element)
            return element
        except Exception as e:
            logger.error(f"Wait for selector error: {str(e)}")
            await self.recorder.record_action('wait_for_selector', error=str(e))
            return None

    async def get_state(self) -> Dict[str, Any]:
        """Get current page state and record it"""
        try:
            state = {
                'url': await self.page.url,
                'title': await self.page.title(),
                'tabs': [{
                    'page_id': page.context.pages.index(page),
                    'url': page.url,
                    'title': await page.title()
                } for page in self.browser.contexts[0].pages]
            }
            await self.recorder.record_action('get_state', state=state)
            return state
        except Exception as e:
            logger.error(f"Get state error: {str(e)}")
            await self.recorder.record_action('get_state', error=str(e))
            return {} 
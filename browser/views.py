from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel

from servicenow_browser_use.dom.history_tree_processor.service import DOMHistoryElement
from servicenow_browser_use.dom.views import DOMState, DOMElementNode, SelectorMap


# Pydantic
class TabInfo(BaseModel):
	"""Represents information about a browser tab"""

	page_id: int
	url: str
	title: str


@dataclass
class BrowserState(DOMState):
	"""Represents the current state of the browser"""
	url: str
	title: str
	tabs: list[TabInfo]
	screenshot: Optional[str] = None
	pixels_above: int = 0
	pixels_below: int = 0
	browser_errors: list[str] = field(default_factory=list)

	def __init__(self, element_tree: DOMElementNode, selector_map: SelectorMap, url: str, title: str, tabs: list[TabInfo], screenshot: Optional[str] = None, pixels_above: int = 0, pixels_below: int = 0, browser_errors: list[str] = None):
		super().__init__(element_tree=element_tree, selector_map=selector_map)
		self.url = url
		self.title = title
		self.tabs = tabs
		self.screenshot = screenshot
		self.pixels_above = pixels_above
		self.pixels_below = pixels_below
		self.browser_errors = browser_errors or []


@dataclass
class BrowserStateHistory:
	url: str
	title: str
	tabs: list[TabInfo]
	interacted_element: list[DOMHistoryElement | None] | list[None]
	screenshot: Optional[str] = None

	def to_dict(self) -> dict[str, Any]:
		data = {}
		data['tabs'] = [tab.model_dump() for tab in self.tabs]
		data['screenshot'] = self.screenshot
		data['interacted_element'] = [el.to_dict() if el else None for el in self.interacted_element]
		data['url'] = self.url
		data['title'] = self.title
		return data


class BrowserError(Exception):
	"""Base class for all browser errors"""


class URLNotAllowedError(BrowserError):
	"""Error raised when a URL is not allowed"""

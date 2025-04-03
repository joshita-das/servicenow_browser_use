"""
Generate Selenium Java scripts from agent recordings.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

def generate_selenium_script(actions: List[Dict], output_file: str):
    """Generate a Selenium Java script from the agent's actions."""
    script = """package com.example.selenium;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class GeneratedSeleniumScript {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        
        try {
"""
    
    for action in actions:
        if 'go_to_url' in action:
            script += f'            driver.get("{action["go_to_url"]["url"]}");\n'
        elif 'input_text' in action:
            script += f'            WebElement element{action["input_text"]["index"]} = wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("[data-index=\\"{action["input_text"]["index"]}\\"]")));\n'
            script += f'            element{action["input_text"]["index"]}.sendKeys("{action["input_text"]["text"]}");\n'
        elif 'click_element' in action:
            script += f'            WebElement element{action["click_element"]["index"]} = wait.until(ExpectedConditions.elementToBeClickable(By.cssSelector("[data-index=\\"{action["click_element"]["index"]}\\"]")));\n'
            script += f'            element{action["click_element"]["index"]}.click();\n'
        elif 'scroll_down' in action:
            script += f'            ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("window.scrollBy(0, {action["scroll_down"]["amount"]});");\n'
        elif 'send_keys' in action:
            script += f'            new org.openqa.selenium.interactions.Actions(driver).sendKeys(org.openqa.selenium.Keys.{action["send_keys"]["keys"].upper()}).perform();\n'
    
    script += """        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            driver.quit();
        }
    }
}"""
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w") as f:
        f.write(script)

def convert_agent_recording_to_selenium(recording_file: str, output_file: Optional[str] = None) -> str:
    """Convert an agent recording JSON file to a Selenium Java script."""
    with open(recording_file, 'r') as f:
        recording = json.load(f)
    
    # If no output file specified, create one with timestamp
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/selenium_script_{timestamp}.java"
    
    # Extract actions from the recording
    actions = []
    if isinstance(recording, dict) and 'all_model_outputs' in recording:
        actions = recording['all_model_outputs']
    elif isinstance(recording, list):
        actions = recording
    
    generate_selenium_script(actions, output_file)
    return output_file 
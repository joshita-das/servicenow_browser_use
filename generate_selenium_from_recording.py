import json
import os
from datetime import datetime

def generate_selenium_code(json_file):
    try:
        with open(json_file, 'r') as f:
            recording = json.load(f)

        # Generate Java code
        java_code = create_selenium_code(recording)
        
        # Create output directory if it doesn't exist
        java_output_dir = "output"
        if not os.path.exists(java_output_dir):
            os.makedirs(java_output_dir)

        # Save Java code
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        java_file = os.path.join(java_output_dir, f"SeleniumTest_{timestamp}.java")
        with open(java_file, 'w') as f:
            f.write(java_code)

        # Get absolute path for logging
        abs_path = os.path.abspath(java_file)
        print(f"\nSelenium test code has been saved to:")
        print(f"Location: {abs_path}")
        print(f"Directory: {os.path.dirname(abs_path)}")
        print(f"Filename: {os.path.basename(abs_path)}\n")
        return java_file

    except Exception as e:
        print(f"Error processing {json_file}: {str(e)}")
        return None

def process_action(action_data):
    """Generate Java code for a single action based on its type and parameters."""
    action_lines = []
    
    action_type = action_data.get("action")
    element = action_data.get("element", {})
    
    if action_type == "type":
        # Get element details
        element_id = element.get("id")
        element_xpath = element.get("xpath")
        text = action_data.get("text", "")
        
        # Choose the best locator strategy
        if element_id:
            locator = f'By.id("{element_id}")'
        elif element_xpath:
            locator = f'By.xpath("{element_xpath}")'
        else:
            return []  # Skip if no good locator found
        
        action_lines.extend([
            f"            // Input text into element",
            f"            WebElement inputElement = waitForElement({locator});",
            "            inputElement.clear();",
            f'            inputElement.sendKeys("{text}");'
        ])
    
    elif action_type == "click":
        # Get element details
        element_id = element.get("id")
        element_xpath = element.get("xpath")
        element_text = element.get("text")
        has_shadow_dom = element.get("hasShadowDOM", False)
        
        if has_shadow_dom:
            shadow_elements = element.get("elementsWithShadowDOM", [])
            shadow_parts = []
            for e in shadow_elements:
                tag_name = e.get("tagName", "").lower()
                element_id = e.get("id", "")
                if element_id:
                    shadow_parts.append(f"{tag_name}#{element_id}")
                else:
                    shadow_parts.append(tag_name)
            shadow_path = " >>> ".join(shadow_parts)
            action_lines.extend([
                f"            // Click shadow DOM element",
                f'            WebElement clickElement = findElementWithShadowDOM("{shadow_path}");'
            ])
        else:
            # Choose the best locator strategy
            if element_id:
                locator = f'By.id("{element_id}")'
            elif element_xpath:
                locator = f'By.xpath("{element_xpath}")'
            elif element_text:
                locator = f'By.xpath("//*[contains(text(), \'{element_text}\')]")'
            else:
                return []  # Skip if no good locator found
            
            action_lines.extend([
                f"            // Click element",
                f"            WebElement clickElement = waitForElementClickable({locator});"
            ])
        
        action_lines.extend([
            "            clickElement.click();",
            "            waitForPageLoad();"
        ])

    return action_lines

def create_selenium_code(recording):
    # Generate Java class name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    class_name = f"SeleniumTest_{timestamp}"

    # Start with imports and class definition
    code = [
        "package com.example.selenium;",
        "",
        "import org.openqa.selenium.By;",
        "import org.openqa.selenium.WebDriver;",
        "import org.openqa.selenium.WebElement;",
        "import org.openqa.selenium.chrome.ChromeDriver;",
        "import org.openqa.selenium.chrome.ChromeOptions;",
        "import org.openqa.selenium.support.ui.ExpectedConditions;",
        "import org.openqa.selenium.support.ui.WebDriverWait;",
        "import org.openqa.selenium.JavascriptExecutor;",
        "import java.time.Duration;",
        "import org.testng.annotations.*;",
        "import java.util.Properties;",
        "import java.io.FileInputStream;",
        "import java.io.IOException;",
        "",
        f"public class {class_name} {{",
        "    private static WebDriver driver;",
        "    private static WebDriverWait wait;",
        "    private static JavascriptExecutor js;",
        "    private static Properties config;",
        "",
        "    @BeforeClass",
        "    public static void setup() throws IOException {{",
        "        // Load configuration from properties file",
        "        config = new Properties();",
        "        try (FileInputStream fis = new FileInputStream(\"config.properties\")) {{",
        "            config.load(fis);",
        "        }}",
        "",
        "        // Set up Chrome options",
        "        ChromeOptions options = new ChromeOptions();",
        "        options.addArguments(\"--remote-allow-origins=*\");",
        "        options.addArguments(\"--disable-web-security\");",
        "        options.addArguments(\"--disable-site-isolation-trials\");",
        "        options.addArguments(\"--no-sandbox\");",
        "        options.addArguments(\"--disable-dev-shm-usage\");",
        "        options.addArguments(\"--remote-debugging-port=9222\");",
        "        ",
        "        // Initialize WebDriver",
        "        driver = new ChromeDriver(options);",
        "        driver.manage().window().maximize();",
        "        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));",
        "        driver.manage().timeouts().pageLoadTimeout(Duration.ofSeconds(30));",
        "        ",
        "        // Initialize WebDriverWait and JavascriptExecutor",
        "        wait = new WebDriverWait(driver, Duration.ofSeconds(10));",
        "        js = (JavascriptExecutor) driver;",
        "    }}",
        "",
        "    @AfterClass",
        "    public static void tearDown() {{",
        "        if (driver != null) {{",
        "            driver.quit();",
        "        }}",
        "    }}",
        "",
        "    private static WebElement findElementWithShadowDOM(String shadowPath) {{",
        "        String[] selectors = shadowPath.split(\" >>> \");",
        "        WebElement element = null;",
        "        ",
        "        for (String selector : selectors) {{",
        "            if (element == null) {{",
        "                element = driver.findElement(By.cssSelector(selector));",
        "            }} else {{",
        "                element = (WebElement) js.executeScript(\"return arguments[0].shadowRoot\", element);",
        "                element = element.findElement(By.cssSelector(selector));",
        "            }}",
        "        }}",
        "        return element;",
        "    }}",
        "",
        "    private static WebElement waitForElement(By locator) {{",
        "        return wait.until(ExpectedConditions.presenceOfElementLocated(locator));",
        "    }}",
        "",
        "    private static WebElement waitForElementClickable(By locator) {{",
        "        return wait.until(ExpectedConditions.elementToBeClickable(locator));",
        "    }}",
        "",
        "    private static void waitForPageLoad() {{",
        "        wait.until(webDriver -> ((JavascriptExecutor) webDriver).executeScript(\"return document.readyState\").equals(\"complete\"));",
        "    }}",
        "",
        "    @Test",
        "    public void testServiceNowAutomation() {{",
        "        try {{",
        "            // Navigate to ServiceNow instance",
        "            String servicenowUrl = config.getProperty(\"servicenow.url\", \"https://your-instance.service-now.com\");",
        "            driver.get(servicenowUrl);",
        "            waitForPageLoad();",
        ""
    ]

    # Process each action from the recording
    if isinstance(recording, list):
        for action_data in recording:
            action_lines = process_action(action_data)
            if action_lines:
                code.extend(action_lines)
                code.append("")  # Add blank line between actions

    # Add closing braces
    code.extend([
        "        }} catch (Exception e) {{",
        "            System.err.println(\"Error during test execution: \" + e.getMessage());",
        "            e.printStackTrace();",
        "            throw e;",
        "        }}",
        "    }}",
        "}"
    ])

    return "\n".join(code)

if __name__ == "__main__":
    # Find the most recent streamlined recording file
    recording_files = [f for f in os.listdir("output") if f.startswith("streamlined_recording_") and f.endswith(".json")]
    if not recording_files:
        print("No streamlined recording files found in output directory")
        exit(1)
    
    latest_recording = max(recording_files, key=lambda x: os.path.getctime(os.path.join("output", x)))
    generate_selenium_code(os.path.join("output", latest_recording)) 
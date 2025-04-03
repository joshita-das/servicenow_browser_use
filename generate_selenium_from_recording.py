import json
import os
from datetime import datetime

def generate_selenium_code(json_file):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)

        # Generate Java code
        java_code = create_selenium_code(data)
        
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

def create_selenium_code(actions):
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
        "",
        f"public class {class_name} {{",
        "    private static WebDriver driver;",
        "    private static WebDriverWait wait;",
        "    private static JavascriptExecutor js;",
        "",
        "    @BeforeClass",
        "    public static void setup() {",
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
        "    }",
        "",
        "    @AfterClass",
        "    public static void tearDown() {",
        "        if (driver != null) {",
        "            driver.quit();",
        "        }",
        "    }",
        "",
        "    private static WebElement findElementWithShadowDOM(String shadowPath) {",
        "        String[] selectors = shadowPath.split(\" >>> \");",
        "        WebElement element = null;",
        "        ",
        "        for (String selector : selectors) {",
        "            if (element == null) {",
        "                element = driver.findElement(By.cssSelector(selector));",
        "            } else {",
        "                element = (WebElement) js.executeScript(\"return arguments[0].shadowRoot\", element);",
        "                element = element.findElement(By.cssSelector(selector));",
        "            }",
        "        }",
        "        return element;",
        "    }",
        "",
        "    private void handleLogin() throws InterruptedException {",
        "        // Wait for username field and enter credentials",
        "        WebElement usernameField = wait.until(ExpectedConditions.presenceOfElementLocated(By.id(\"user_name\")));",
        "        usernameField.clear();",
        "        usernameField.sendKeys(\"admin\");",
        "        Thread.sleep(500);",
        "",
        "        // Enter password",
        "        WebElement passwordField = wait.until(ExpectedConditions.presenceOfElementLocated(By.id(\"user_password\")));",
        "        passwordField.clear();",
        "        passwordField.sendKeys(\"admin\");",
        "        Thread.sleep(500);",
        "",
        "        // Click login button",
        "        WebElement loginButton = wait.until(ExpectedConditions.elementToBeClickable(By.id(\"sysverb_login\")));",
        "        loginButton.click();",
        "        Thread.sleep(2000);  // Wait for login to complete",
        "    }",
        "",
        "    @Test",
        "    public void runTest() {",
        "        try {",
        "            // Navigate to the target website",
        "            driver.get(\"https://k8s0722360-node1.thunder.devsnc.com/now/workflow-studio/home/process\");",
        "            Thread.sleep(2000);  // Wait for initial page load",
        "",
        "            // Handle login if redirected",
        "            if (driver.getCurrentUrl().contains(\"login.do\")) {",
        "                handleLogin();",
        "            }",
        "",
        "            // Wait for page to load after login",
        "            Thread.sleep(2000);",
        "",
        "            // Click on New button",
        "            WebElement newButton = wait.until(ExpectedConditions.elementToBeClickable(",
        "                By.cssSelector(\"button[data-testid='new-button']\")))",
        "            newButton.click();",
        "            Thread.sleep(1000);",
        "",
        "            // Verify Flow tab is present",
        "            WebElement flowTab = wait.until(ExpectedConditions.presenceOfElementLocated(",
        "                By.cssSelector(\"div[data-testid='flow-tab']\")))",
        "            assert flowTab.isDisplayed() : \"Flow tab is not visible\";",
        "",
    ]

    # Add test steps based on actions
    for action in actions:
        if action['action'] == 'type':
            element = action['element']
            text = action['text']
            
            # Skip login-related actions as they're handled in handleLogin()
            if element.get('id') in ['user_name', 'user_password'] or text in ['admin']:
                continue
                
            # Handle shadow DOM elements
            if element.get('hasShadowDOM'):
                shadow_elements = element.get('elementsWithShadowDOM', [])
                shadow_parts = []
                for e in shadow_elements:
                    tag_name = e.get('tagName', '').lower()
                    element_id = e.get('id', '')
                    if element_id:
                        shadow_parts.append(f"{tag_name}#{element_id}")
                    else:
                        shadow_parts.append(tag_name)
                shadow_path = " >>> ".join(shadow_parts)
                code.append(f"            WebElement inputElement = findElementWithShadowDOM(\"{shadow_path}\");")
            else:
                # Use XPath if available, otherwise use ID
                if element.get('xpath'):
                    code.append(f"            WebElement inputElement = wait.until(ExpectedConditions.presenceOfElementLocated(By.xpath(\"{element.get('xpath')}\")));")
                elif element.get('id'):
                    code.append(f"            WebElement inputElement = wait.until(ExpectedConditions.presenceOfElementLocated(By.id(\"{element.get('id')}\")));")
                else:
                    continue
                    
            code.append("            inputElement.clear();")
            code.append(f"            inputElement.sendKeys(\"{text}\");")
            code.append("            Thread.sleep(500);")
            
        elif action['action'] == 'click':
            element = action['element']
            
            # Skip login-related actions
            if element.get('id') == 'sysverb_login':
                continue
                
            # Handle shadow DOM elements
            if element.get('hasShadowDOM'):
                shadow_elements = element.get('elementsWithShadowDOM', [])
                shadow_parts = []
                for e in shadow_elements:
                    tag_name = e.get('tagName', '').lower()
                    element_id = e.get('id', '')
                    if element_id:
                        shadow_parts.append(f"{tag_name}#{element_id}")
                    else:
                        shadow_parts.append(tag_name)
                shadow_path = " >>> ".join(shadow_parts)
                code.append(f"            WebElement clickElement = findElementWithShadowDOM(\"{shadow_path}\");")
            else:
                # Use XPath if available, otherwise use ID
                if element.get('xpath'):
                    code.append(f"            WebElement clickElement = wait.until(ExpectedConditions.elementToBeClickable(By.xpath(\"{element.get('xpath')}\")));")
                elif element.get('id'):
                    code.append(f"            WebElement clickElement = wait.until(ExpectedConditions.elementToBeClickable(By.id(\"{element.get('id')}\")));")
                else:
                    continue
                    
            code.append("            clickElement.click();")
            code.append("            Thread.sleep(1000);")

    # Add main method with proper error handling
    code.extend([
        "        } catch (Exception e) {",
        "            System.err.println(\"Test failed with error: \" + e.getMessage());",
        "            e.printStackTrace();",
        "        } finally {",
        "            tearDown();",
        "        }",
        "    }",
        "",
        "    public static void main(String[] args) {",
        f"        {class_name} test = new {class_name}();",
        "        test.runTest();",
        "    }",
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
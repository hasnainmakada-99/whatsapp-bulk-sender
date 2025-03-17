from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep
from urllib.parse import quote
import os

# Try importing Service for newer Selenium versions
try:
    from selenium.webdriver.chrome.service import Service
    newer_selenium = True
except ImportError:
    newer_selenium = False

# Set Chrome options
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--profile-directory=Default")
options.add_argument("--user-data-dir=/var/tmp/chrome_user_data")
options.add_argument("--remote-debugging-port=9222")  # Helps with Web WhatsApp connection

# Function to print colored messages
class style():
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    MAGENTA = '\033[35m'
    RESET = '\033[0m'

# Print startup message
print(style.YELLOW + "**************************************")
print("*****  WHATSAPP BULK MESSENGER  *****")
print("*****  Built for automation!    *****")
print("**************************************" + style.RESET)

# Load message
try:
    with open("message.txt", "r", encoding="utf8") as f:
        message = f.read()
except FileNotFoundError:
    print(style.RED + "Error: message.txt not found!" + style.RESET)
    exit()

print(style.GREEN + "Message to be sent: \n" + message + style.RESET)
message = quote(message)  # Encode message

# Load numbers
numbers = []
try:
    with open("numbers.txt", "r") as f:
        numbers = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(style.RED + "Error: numbers.txt not found!" + style.RESET)
    exit()

total_number = len(numbers)
print(style.YELLOW + f"Found {total_number} numbers to send messages." + style.RESET)

# Initialize ChromeDriver with the specified path
try:
    # First try using WebDriver Manager (most reliable method)
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        if newer_selenium:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    except Exception as e:
        print(style.YELLOW + f"Could not use WebDriver Manager: {str(e)}" + style.RESET)
        print("Falling back to local ChromeDriver...")
        
        # Try using local ChromeDriver
        chromedriver_path = "C:\\Windows\\chromedriver.exe"  # Manually specified ChromeDriver path
        if newer_selenium:
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)

    print(style.MAGENTA + "Open WhatsApp Web and scan the QR code if needed." + style.RESET)
    driver.get('https://web.whatsapp.com')

    input(style.GREEN + "Press ENTER after logging into WhatsApp Web and chats are visible..." + style.RESET)

    delay = 30  # Time to wait for elements
    for idx, number in enumerate(numbers):
        print(style.YELLOW + f"Sending message to {idx+1}/{total_number}: {number}" + style.RESET)
        try:
            url = f'https://web.whatsapp.com/send?phone={number}&text={message}'
            driver.get(url)
            
            # Wait for elements to load and for chat to be ready
            sleep(5)  # Give some time for the page to load
            
            # Try multiple XPATH patterns for the send button (WhatsApp changes these occasionally)
            send_button_xpaths = [
                "//button[@data-testid='compose-btn-send']",
                "//span[@data-icon='send']",
                "//span[@data-testid='send']",
                "//button[contains(@class, 'send')]",
                "//*[@id='main']/footer/div[1]/div/span[2]/div/div[2]/div[2]/button"
            ]
            
            sent = False
            for xpath in send_button_xpaths:
                if sent:
                    break
                try:
                    send_btn = WebDriverWait(driver, delay).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    # Sometimes the element is found but not yet clickable
                    sleep(2)
                    send_btn.click()
                    sent = True
                    sleep(3)  # Wait after sending
                    print(style.GREEN + f"Message sent to {number}" + style.RESET)
                except Exception:
                    continue  # Try the next xpath pattern
            
            if not sent:
                # Try one last approach - sending Enter key if message is loaded
                try:
                    # Find the message input field and press Enter
                    input_box = WebDriverWait(driver, delay).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
                    )
                    from selenium.webdriver.common.keys import Keys
                    input_box.send_keys(Keys.ENTER)
                    sent = True
                    sleep(3)
                    print(style.GREEN + f"Message sent to {number} using Enter key" + style.RESET)
                except Exception as e:
                    print(style.RED + f"Failed to send message to {number}: {str(e)}" + style.RESET)
            
            if not sent:
                print(style.RED + f"Failed to send message to {number}: could not find or click send button" + style.RESET)
                
        except Exception as e:
            print(style.RED + f"Failed to send message to {number}: {str(e)}" + style.RESET)

except Exception as e:
    print(style.RED + f"Error initializing Chrome WebDriver: {str(e)}" + style.RESET)
    print("Make sure you have: ")
    print("1. Installed Google Chrome (latest version).")
    print("2. Downloaded correct ChromeDriver from: https://chromedriver.chromium.org/downloads")
    print("3. Placed ChromeDriver.exe in C:\\Windows\\ directory.")
    print("4. Updated Selenium with: pip install selenium --upgrade")

finally:
    try:
        if 'driver' in locals():
            driver.quit()  # Ensures proper closure
    except Exception:
        pass
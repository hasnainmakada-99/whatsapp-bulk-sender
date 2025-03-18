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

# Set Chrome options - using these to speed up performance
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--profile-directory=Default")
options.add_argument("--user-data-dir=/var/tmp/chrome_user_data")
options.add_argument("--remote-debugging-port=9222") 
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

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

# Create results log file for tracking successful/failed sends
with open("message_log.txt", "w") as log_file:
    log_file.write("WhatsApp Bulk Messenger Log\n")
    log_file.write("==========================\n\n")

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

    # Ultra-fast timing settings
    delay = 10         # Max wait time for elements
    page_load_wait = 2 # Wait time for page to load
    send_wait = 0.5    # Wait time after sending

    # SUCCESS AND FAILURE COUNTERS
    success_count = 0
    failure_count = 0
    invalid_number_count = 0
    
    for idx, number in enumerate(numbers):
        print(style.YELLOW + f"Processing {idx+1}/{total_number}: {number}" + style.RESET)
        try:
            url = f'https://web.whatsapp.com/send?phone={number}&text={message}'
            driver.get(url)
            
            # SHORT WAIT FOR PAGE TO LOAD
            sleep(page_load_wait)
            
            # CHECK FOR INVALID NUMBER ERROR - Multiple ways WhatsApp shows this
            try:
                # Wait a short time to see if error message appears
                error_elements = [
                    "//div[contains(text(), 'Phone number shared via url is invalid')]",
                    "//div[contains(text(), 'The phone number')]",
                    "//div[contains(@data-animate-invalid-number, 'true')]"
                ]
                
                for error_xpath in error_elements:
                    try:
                        WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, error_xpath))
                        )
                        print(style.RED + f"Invalid number detected: {number}" + style.RESET)
                        with open("message_log.txt", "a") as log_file:
                            log_file.write(f"INVALID: {number} - Not on WhatsApp\n")
                        invalid_number_count += 1
                        failure_count += 1
                        raise Exception("Invalid number detected")
                    except TimeoutException:
                        # No error found with this xpath, continue checking
                        pass
            except TimeoutException:
                # No error found, continue with sending
                pass
            
            # OPTIMIZED XPATHS - FEWER, MORE RELIABLE ONES
            send_button_xpaths = [
                "//button[@data-testid='compose-btn-send']",  # Most common
                "//span[@data-icon='send']",                  # Alternative
                "//*[@id='main']/footer//button[contains(@class, 'send')]" # Backup
            ]
            
            sent = False
            for xpath in send_button_xpaths:
                if sent:
                    break
                try:
                    # Shorter wait time
                    send_btn = WebDriverWait(driver, delay).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    send_btn.click()
                    sent = True
                    sleep(send_wait)
                    print(style.GREEN + f"Message sent to {number}" + style.RESET)
                    with open("message_log.txt", "a") as log_file:
                        log_file.write(f"SUCCESS: {number}\n")
                    success_count += 1
                    break  # Exit loop on success
                except Exception:
                    continue  # Try the next xpath pattern
            
            if not sent:
                # Last resort - try Enter key
                try:
                    input_box = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
                    )
                    from selenium.webdriver.common.keys import Keys
                    input_box.send_keys(Keys.ENTER)
                    sent = True
                    sleep(send_wait)
                    print(style.GREEN + f"Message sent to {number} using Enter key" + style.RESET)
                    with open("message_log.txt", "a") as log_file:
                        log_file.write(f"SUCCESS: {number} (using Enter key)\n")
                    success_count += 1
                except Exception as e:
                    print(style.RED + f"Failed to send message to {number}" + style.RESET)
                    with open("message_log.txt", "a") as log_file:
                        log_file.write(f"FAILED: {number} - {str(e)[:100]}\n")
                    failure_count += 1
            
            if not sent:
                print(style.RED + f"Failed to send message to {number}: could not find send button" + style.RESET)
                with open("message_log.txt", "a") as log_file:
                    log_file.write(f"FAILED: {number} - Could not find send button\n")
                failure_count += 1
                
        except Exception as e:
            print(style.RED + f"Failed to process {number}: {str(e)}" + style.RESET)
            with open("message_log.txt", "a") as log_file:
                log_file.write(f"ERROR: {number} - {str(e)[:100]}\n")
            failure_count += 1

    # Print summary
    print("\n" + style.YELLOW + "========== SUMMARY ==========" + style.RESET)
    print(style.GREEN + f"✓ Successfully sent: {success_count}" + style.RESET)
    print(style.RED + f"✗ Failed to send: {failure_count - invalid_number_count}" + style.RESET)
    print(style.YELLOW + f"! Invalid numbers: {invalid_number_count}" + style.RESET)
    print(style.YELLOW + f"See message_log.txt for details" + style.RESET)
    
    # Write summary to log
    with open("message_log.txt", "a") as log_file:
        log_file.write("\n========== SUMMARY ==========\n")
        log_file.write(f"Successfully sent: {success_count}\n")
        log_file.write(f"Failed to send: {failure_count - invalid_number_count}\n")
        log_file.write(f"Invalid numbers: {invalid_number_count}\n")

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
# -*- coding: utf-8 -*-
"""IpoGmpData

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1PRlfnhnmM8Y2aiE4gsv-dofYvEaSl8Kq
"""

#FinalCode
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from io import StringIO
import time
import requests
import json

# --- Configuration for Green API (replace with your details) ---
GREEN_API_INSTANCE_ID = 'xxxxxxxxxx'  # Replace with your Instance ID
GREEN_API_TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'        # Replace with your API Token
TARGET_PHONE_NUMBER = '91xxxxxxxxxx'      # Replace with your target phone number (including country code)


# --- Function to send WhatsApp message using Green API ---
def send_whatsapp_message_greenapi(phone_number: str, message: str):
    """
    Sends a WhatsApp message using the Green API.
    """
    api_url = f"https://7105.api.green-api.com/waInstance{GREEN_API_INSTANCE_ID}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": f"{phone_number}@c.us",
        "message": message
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        print(f"[GREEN API] Message sent successfully to {phone_number}:")
        print(message)
        print("-" * 30)
        print(f"[GREEN API] Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[GREEN API ERROR] Failed to send message to {phone_number}: {e}")
    except json.JSONDecodeError:
        print(f"[GREEN API ERROR] Failed to decode JSON response: {response.text}")


# Set up headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


driver = webdriver.Chrome(options=chrome_options)

# Open the IPO Watch GMP page
url = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"
driver.get(url)

# Wait for the page to load and scroll
time.sleep(5)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(5)

# Try to find the specific table containing Current IPO GMP
try:
    # The table seems to be the first one with the specific structure
    table = driver.find_element(By.XPATH, "//table[contains(., 'Current IPOs') and contains(., 'IPO GMP')]")
    html = table.get_attribute('outerHTML')

    # Use StringIO to avoid warning
    df = pd.read_html(StringIO(html))[0]

    # Extract headers from the first row of the tbody
    tbody = table.find_element(By.TAG_NAME, "tbody")
    header_row = tbody.find_elements(By.TAG_NAME, "tr")[0]
    header_cols_elements = header_row.find_elements(By.TAG_NAME, "td")
    header_cols = [col.find_element(By.TAG_NAME, 'strong').text.strip() if col.find_elements(By.TAG_NAME, 'strong') else col.text.strip() for col in header_cols_elements]

    # If we have header columns, use them
    if header_cols:
        df.columns = header_cols
        # Filter required columns
        expected_cols = ['Current IPOs', 'IPO GMP', 'Price', 'Gain', 'Date', 'Subject', 'Type']
        df_filtered = df[[col for col in expected_cols if col in df.columns]].copy()

        # Function to check if a date string contains a year (more robust)
        def has_year(date_str):
            return any(len(part) == 4 and part.isdigit() for part in date_str.split())

        # Filter the DataFrame to show only rows where 'Date' DOES NOT have a year
        df_without_year = df_filtered[~df_filtered['Date'].apply(has_year)]

        print("\n--- Current IPOs with Date (without year) ---")
        print(df_without_year)

        # --- WhatsApp Messaging Logic using Green API ---
        if not df_without_year.empty:
            print("\nPreparing to send WhatsApp messages for each row (starting from the second) using Green API...")
            # Iterate through rows starting from index 1
            for index, row in df_without_year.iloc[1:].iterrows():
                whatsapp_message = (
                    f"IPO Name: {row.iloc[0]}\n"
                    f"GMP: {row.iloc[1]}\n"
                    f"Price: {row.iloc[2]}\n"
                    f"Gain: {row.iloc[3]}\n"
                    f"Date: {row.iloc[4]}\n"
                    f"Subject: {row.iloc[5]}\n"
                    f"Type: {row.iloc[6]}"
                )

                # Send the message using Green API
                send_whatsapp_message_greenapi(TARGET_PHONE_NUMBER, whatsapp_message)
                time.sleep(2) # Add a small delay between messages

            print("\nFinished processing rows and sending WhatsApp messages (starting from the second) using Green API.")
        else:
            print("\nNo IPOs found without a year in their date to send via WhatsApp using Green API.")

    else:
        print("Could not extract table headers properly from the first tbody row.")

except Exception as e:
    print(f"An error occurred while finding or processing the table: {e}")
    print("Could not retrieve the Current IPOs table.")

driver.quit()
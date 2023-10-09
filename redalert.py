import requests
from time import sleep
from datetime import datetime
import json
import subprocess
import re


URL = 'https://www.oref.org.il/WarningMessages/alert/alerts.json'
CITIES_URL = 'https://www.oref.org.il/Shared/Ajax/GetCitiesMix.aspx?lang=he'
CATEGORIES_URL = 'https://www.oref.org.il/Leftovers/HE.Leftovers.json'


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
    'Accept': '*/*',
    #'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.oref.org.il//12481-he/Pakar.aspx',
    #'Content-Type': 'application/json;charset=utf-8',
    'X-Requested-With': 'XMLHttpRequest',
    #'DNT': '1',
    #'Connection': 'keep-alive',
    #'Sec-Fetch-Dest': 'empty',
    #'Sec-Fetch-Mode': 'cors',
    #'Sec-Fetch-Site': 'same-origin',
    #'Pragma': 'no-cache',
    'Cache-Control': 'no-cache'
}

# Keep track of already processed alert IDs
processed_ids = set()

def get_label_by_category(category_num, json_data):
    for item in json_data:
        if item['category'] == category_num:
            return item['label']

# Function to get json list
def get_json_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Decode the content using utf-8-sig to handle BOM if present
        content = response.content.decode('utf-8-sig')
        
        # Parse the content to JSON
        data = json.loads(content)
        
        return data
        
    except Exception as e:
        print(f"Error occurred while fetching category data: {e}")
        return []
    

def process_alert(data, alert_city):
    alert_id = str(data.get("id"))
    index_of_last_non_zero = max(i for i, char in enumerate(alert_id) if char != '0')
    alert_id = alert_id[:index_of_last_non_zero+1]
    alert_id = int(alert_id)

    
    # If the ID has not been processed yet
    if alert_id not in processed_ids:
        processed_ids.add(alert_id)

        category_id = data.get("cat")
        #category = get_label_by_category(int(category_id), category_data)
        title = data.get("title")
        areas_list = data.get("data", [])
        areas = ", ".join(areas_list)
        description = data.get("desc")
        
        # Check if alert_city is in the list of alerted areas
        #if alert_city and alert_city not in areas_list: # exact match only
        #if alert_city and not any(alert_city in area for area in areas_list): # partial match
        #if alert_city and not any(alert_city in area.split() for area in areas_list): # partial whole word

        
        if alert_city and not any(re.search(r'\b' + re.escape(alert_city) + r'\b', area) for area in areas_list): # should match partial or whole words only
            print(f"areas_list: {areas_list}")
            print(f"alert_city: {alert_city}")
            print("alert city exist but not matched in list")
            return
        


        migun_time = []


        for area in areas_list:
            for city in cities_data:
                if area == city.get("label"):
                    migun_time.append(city.get("migun_time"))

                
        migun_time = [int(x) for x in migun_time]
        migun_time = min(migun_time)

        if alert_city:
            delay = migun_time
        else:
            delay = 7


        tv_message = f"{title} לעבר {areas} היכנס למרחב מוגן תוך {migun_time} שניות"
        tv_message2 = f"התראת {title} בישובים: {areas}, זמן הגעה למרחב מוגן {migun_time} שניות, {description}"

        current_date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        # Printing the alert details
        print("ID:", alert_id)
        print("Date:", current_date)
        #print("Category:", category)
        print("Alert:", title)
        print("Area:", areas)
        print("Time to cover:", migun_time)
        print("Action:", description)
        print("-" * 50)  # Separator for better readability



        try:
            # Pass the message to a Linux command
            cmd = ["lgtv", "LG", "createAlert", tv_message2, "OK"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=4)

            # Extract the alertId value from the command output
            output = result.stdout.strip()
            response_dict = json.loads(output.split('\n')[0])
            tv_alert_id = response_dict["payload"]["alertId"]

            # Close Alert after the delay
            sleep(delay)

            # Pass the close message to a Linux command
            cmd = ["lgtv", "LG", "closeAlert", tv_alert_id]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
        except Exception as e:
            print(f"--- TV is Off or Offline ---\n{str(e)}")


def fetch_alert(alert_city):
    try:
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()
        
        # Decode using utf-8-sig to handle the BOM
        content = response.content.decode('utf-8-sig')

        # Check if content is not empty
        if content.strip():
            alerts = json.loads(content)

            # Ensure alerts is a list
            if not isinstance(alerts, list):
                alerts = [alerts]

            # Process each alert in the list
            for alert in alerts:
                process_alert(alert, alert_city)

    except requests.RequestException as err:
        if "Max retries exceeded" not in str(err):
            print(f'Error occurred: {err}')
    except ValueError as val_err:
        print(f"Value error occurred: {val_err}")

if __name__ == '__main__':
    alert_city = input("Enter the city name for alert (blank for all cities): ").strip()
    cities_data = get_json_data(CITIES_URL)
    #category_data = get_json_data(CATEGORIES_URL)
    while True:
        fetch_alert(alert_city)
        sleep(1)

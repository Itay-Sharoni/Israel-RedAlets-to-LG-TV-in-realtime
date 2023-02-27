import requests
import json
import time
import subprocess

# URL to monitor for JSON updates
json_url = "https://www.oref.org.il/WarningMessages/History/AlertsHistory.json"

# Polling interval in seconds
polling_interval = 5

# Keep track of the last JSON response
last_response = None

while True:
    try:
        # Make an HTTP request to the JSON URL
        response = requests.get(json_url)

        # If the response is different from the last response,
        # parse the JSON and trigger an alert
        if response.text != last_response:
            last_response = response.text
            data = json.loads(response.text)
            alert = data[0]
            message_cli = f"{alert['alertDate']} {alert['title']} {alert['data']}"
            message = f"{alert['title']} לעבר {alert['data']}"

            print("-" * 40)
            print("--- Red Alert ---")
            print(message_cli)
            print("-" * 40)


            try:
                # Pass the message to a Linux command
                cmd = ["lgtv", "LG", "createAlert", message, "OK"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)

                # Extract the alertId value from the command output
                output = result.stdout.strip()
                response_dict = json.loads(output.split('\n')[0])
                alert_id = response_dict["payload"]["alertId"]

                # Close Alert after 15 seconds
                time.sleep(15)
                # Pass the close message to a Linux command
                cmd = ["lgtv", "LG", "closeAlert", alert_id]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            except Exception as e:
                print("--- TV is Off or Offline ---")

        # Wait for the specified polling interval
        time.sleep(polling_interval)

    except Exception as e:
        #print("Error: " + str(e))
        print("אין התראות")
        # Wait for a shorter interval if there was an error
        time.sleep(polling_interval)

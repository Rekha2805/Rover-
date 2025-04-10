import requests
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import random
import ast

# API Endpoints
SESSION_URL = "https://roverdata2-production.up.railway.app/api/session/start"
ROVER_STATUS_URL = "https://roverdata2-production.up.railway.app/api/rover/status"
SENSOR_DATA_URL = "https://roverdata2-production.up.railway.app/api/rover/sensor-data"
MOVE_ROVER_URL = "https://roverdata2-production.up.railway.app/api/rover/move"
STOP_ROVER_URL = "https://roverdata2-production.up.railway.app/api/rover/stop"
CHARGE_ROVER_URL = "https://roverdata2-production.up.railway.app/api/rover/charge"

LOG_FILE = "rover_sensor_log.txt"

# Initialize lists
rover_x, rover_y = [], []
obstacles = []
tag_detections_x, tag_detections_y = [], []

# Load previous data
def load_previous_data():
    try:
        with open(LOG_FILE, "r") as log_file:
            for line in log_file:
                try:
                    coords, sensor_data_str = line.strip().split(" -> ")
                    x, y = ast.literal_eval(coords)
                    sensor_data = ast.literal_eval(sensor_data_str)

                    # Restore rover path
                    rover_x.append(x)
                    rover_y.append(y)

                    # Restore RFID tags
                    if sensor_data.get("rfid", {}).get("tag_detected", False):
                        tag_detections_x.append(x)
                        tag_detections_y.append(y)

                    # Restore obstacles
                    if sensor_data.get("obstacle", False):
                        obstacles.append((x, y))

                except Exception as e:
                    print(f"Error processing log line: {line}. Error: {e}")
    except FileNotFoundError:
        print("No previous log found, starting fresh.")

def start_session():
    try:
        response = requests.post(SESSION_URL)
        data = response.json()
        return data.get("session_id")
    except Exception as e:
        return None

def fetch_coordinates(session_id):
    try:
        response = requests.get(f"{ROVER_STATUS_URL}?session_id={session_id}")
        data = response.json()
        return data.get("coordinates", [0, 0]), data.get("battery", 100)
    except Exception as e:
        return None, None

def fetch_sensor_data(session_id):
    try:
        response = requests.get(f"{SENSOR_DATA_URL}?session_id={session_id}")
        return response.json()
    except Exception as e:
        return {}

def move_rover(session_id):
    try:
        requests.post(f"{MOVE_ROVER_URL}?session_id={session_id}&direction={random.choice(['forward', 'backward', 'left', 'right'])}")
    except Exception as e:
        print("Error moving rover:", e)

def stop_rover(session_id):
    try:
        requests.post(f"{STOP_ROVER_URL}?session_id={session_id}")
    except Exception as e:
        print("Error stopping rover:", e)

def charge_rover(session_id):
    try:
        requests.post(f"{CHARGE_ROVER_URL}?session_id={session_id}")
    except Exception as e:
        print("Error charging rover:", e)

load_previous_data()

session_id = start_session()
if not session_id:
    exit()

def update(frame):
    """Fetch new data, move the rover, update the plot, and save sensor data"""

    coords, battery = fetch_coordinates(session_id)
    if coords is None:
        return  
    
    x, y = coords
    sensor_data = fetch_sensor_data(session_id)

    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"({x}, {y}) -> {sensor_data}\n")

    # Detect RFID tag
    if sensor_data.get("rfid", {}).get("tag_detected", False):
        tag_detections_x.append(x)
        tag_detections_y.append(y)

    # Detect obstacles
    if sensor_data.get("obstacle", False):
        obstacles.append((x, y))

    if battery < 10:
        stop_rover(session_id)
        charge_rover(session_id)
    else:
        move_rover(session_id)

    # Update rover path
    rover_x.append(x)
    rover_y.append(y)

    # Clear previous plots
    ax1.cla()
    ax2.cla()
    ax3.cla()

    # Plot Rover Path
    ax1.plot(rover_x, rover_y, marker="o", linestyle="-", color="blue", label="Rover Path", alpha=0.6)
    ax1.scatter([x], [y], color="red", edgecolors="black", s=100, label="Current Position", zorder=3)

    # Plot obstacles
    if obstacles:
        obs_x, obs_y = zip(*obstacles) if obstacles else ([], [])
        ax1.scatter(obs_x, obs_y, color="black", marker="x", label="Obstacles", zorder=2)

    # Plot RFID tag detections on main map
    if tag_detections_x and tag_detections_y:
        ax1.scatter(tag_detections_x, tag_detections_y, color="cyan", marker="s", s=80, label="RFID Tags", zorder=2)

    ax1.set_xlim(-250, 250)
    ax1.set_ylim(-250, 250)
    ax1.set_xlabel("X Coordinate")
    ax1.set_ylabel("Y Coordinate")
    ax1.set_title("Rover Real-Time Position", fontsize=10, fontweight="bold",style="italic")
    ax1.legend()
    ax1.grid(True)

    # Update Sensor Data Display
    sensor_text = "\n".join([f"{key}: {value}" for key, value in sensor_data.items()])
    ax2.text(0.1, 0.5, sensor_text, fontsize=9, verticalalignment="center")
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_title("Sensor Data", fontsize=10, fontweight="bold",style="italic")

    # Plot RFID Tag Graph with Line Plot
    if tag_detections_x and tag_detections_y:
        ax3.plot(tag_detections_x, tag_detections_y, marker="o", linestyle="-", color="cyan", label="RFID Detections")
        ax3.scatter(tag_detections_x, tag_detections_y, color="blue", s=100)  # Highlight points
        ax3.set_xlabel("X Coordinate")
        ax3.set_ylabel("Y Coordinate")
        ax3.set_title("RFID Tag Detections Over Time", fontsize=10, fontweight="bold",style="italic")
        ax3.legend()
        ax3.grid(True)

    plt.draw()

# Set up 3 subplots: Rover Path, Sensor Data, and RFID Tag Detections
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
ani = FuncAnimation(fig, update, interval=1000, cache_frame_data=False)
plt.show()
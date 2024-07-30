#!/bin/bash

# Start avahi-publish-service in the background and save its PID
nohup avahi-publish-service -s "CL IMAGE REPO" _image_repo_api._tcp 5000 "CL Image Repo Service" > /dev/null  2>&1 &

# Save the PID of the last background command
PID=$!

# Function to stop the service
stop_service() {
    echo "Stopping the service... $PID"
    kill $PID
    echo "Service stopped."
    exit
}

# Trap SIGINT (Ctrl+C) to call the stop_service function
trap 'stop_service' SIGINT

# Loop to keep the script running
while true; do
    sleep 1
done

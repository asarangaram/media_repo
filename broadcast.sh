#!/bin/bash

###############################################################################
# dns-sd on macOS / avahi-publish + avahi-browse on Linux
###############################################################################

# Load variables from an env file
ENV_FILE="$HOME/.mediarepo"  # or absolute path like "$HOME/.mediarepo"

if [ -f "$ENV_FILE" ]; then
    
    set -a
    source "$ENV_FILE"
    set +a
    
else
    echo "Environment file not found: $ENV_FILE"
    exit 1
fi
printenv
if [ -z "$HOST_PORT" ]; then
  echo "Error: HOST_PORT is not set in the environment."
  exit 1
fi


SERVICE_NAME="server200@cloudonlapapps" # FIXME: make it env variable
SERVICE_TYPE="_http._tcp"
PORT=$HOST_PORT
TXT_RECORD="desc=CL Image Repo Service"

OS_TYPE=$(uname)

# Set timeout command
if [[ "$OS_TYPE" == "Darwin" ]]; then
    TIMEOUT_CMD="gtimeout"
else
    TIMEOUT_CMD="timeout"
fi

# Check if timeout exists
if ! command -v "$TIMEOUT_CMD" >/dev/null 2>&1; then
    echo "'$TIMEOUT_CMD' not found. Attempting to install..."

    if [[ "$OS_TYPE" == "Darwin" ]]; then
        if command -v brew >/dev/null 2>&1; then
            echo "Installing coreutils with Homebrew..."
            brew install coreutils
        else
            echo "Homebrew not found. Please install Homebrew first: https://brew.sh"
            exit 1
        fi
    elif [[ "$OS_TYPE" == "Linux" ]]; then
        if command -v apt >/dev/null 2>&1; then
            echo "Installing coreutils using apt..."
            sudo apt update && sudo apt install -y coreutils
        else
            echo "Unknown Linux distro or missing package manager. Install 'timeout' manually."
            exit 1
        fi
    fi

    # Retry command check
    if ! command -v "$TIMEOUT_CMD" >/dev/null 2>&1; then
        echo "'$TIMEOUT_CMD' still not found after installation. Exiting."
        exit 1
    fi
fi


if [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "Detected macOS"

    SERVICE_EXISTS=""
    if [[ -n "$TIMEOUT_CMD" ]]; then
        SERVICE_EXISTS=$($TIMEOUT_CMD 2 dns-sd -B "$SERVICE_TYPE" local 2>/dev/null | grep "$APP_NAME" || true)
    else
        SERVICE_EXISTS=$(dns-sd -B "$SERVICE_TYPE" local 2>/dev/null | grep "$APP_NAME" || true)
    fi

    if [[ -n "$SERVICE_EXISTS" ]]; then
        echo "Service '$SERVICE_NAME' already advertised."
    else
        echo "Registering DNS-SD service '$SERVICE_NAME' using dns-sd..."
        dns-sd -R "$SERVICE_NAME" "$SERVICE_TYPE" local "$PORT" "$TXT_RECORD" 
    fi

elif [[ "$OS_TYPE" == "Linux" ]]; then
    echo "Detected Linux"

    if avahi-browse -rt "$SERVICE_TYPE" | grep -q "$SERVICE_NAME"; then
        echo "Service '$SERVICE_NAME' already advertised."
    else
        echo "Registering DNS-SD service '$SERVICE_NAME' using avahi..."
        avahi-publish -s "$SERVICE_NAME" "$SERVICE_TYPE" "$PORT" "$TXT_RECORD" 
    fi

else
    echo "Unsupported OS: $OS_TYPE"
    exit 1
fi

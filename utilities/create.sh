#!/bin/bash

# Check if at least one argument is provided
if [ "$#" -lt 2 ]; then
    echo "Usage: create -key1 value1 -key2 value2 ... -media filename"
    exit 1
fi

# Declare variables
declare -A params

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    key="$1"
    value="$2"
    
    # Remove leading '-' from key
    key="${key#-}"
    
    params[$key]="$value"
    
    # Shift to next key-value pair
    shift 2
done





# Build curl command
curl_cmd=("curl" "-X" "POST" "http://192.168.0.225:5000/entity")


for key in "${!params[@]}"; do
    if [ "$key" != "media" ]; then
        # Add all parameters except media
        curl_cmd+=("-F" "$key=${params[$key]}")
    fi
    if [ "$key" = "media" ]; then
        # Detect MIME type
        type=$(file --mime-type -b "${params[media]}")
        # Add media parameter separately with detected MIME type
        curl_cmd+=("-F" "media=@${params[media]};type=$type")
    fi
done

# Execute curl command
"${curl_cmd[@]}"

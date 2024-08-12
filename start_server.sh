#! /bin/bash

set -e

create_venv() {
    V_ENV=".venv"
    
    if [ ! -d "$V_ENV" ]; then
        echo "$V_ENV does not exist. Creating"
        python3.11 -m venv .venv
        if [ -f "${V_ENV}/bin/activate" ]; then
            source "${V_ENV}/bin/activate"
        else
            echo "Error: Virtual environment activation script not found."
            exit 1
        fi
        # Example: Call the function with a specific requirements file
        install_packages_from_requirements "requirements.txt"
    else
        echo "$V_ENV Found"
        
        if [ -f "${V_ENV}/bin/activate" ]; then
            source "${V_ENV}/bin/activate"
        else
            echo "Error: Virtual environment activation script not found."
            exit 1
        fi
        install_packages_from_requirements "requirements.txt"
    fi
    
}

install_packages_from_requirements() {
    pip install --upgrade pip
    requirements_file="$1"
    echo "install pacakges if missing"
    if [ -f "$requirements_file" ]; then
        while IFS= read -r requirement; do
            package_name=$(echo "$requirement" | cut -d'=' -f1)
            if ! pip show "$package_name" > /dev/null 2>&1; then
                
                echo "Installing $requirement..."
                pip install "$requirement"
            fi
        done < "$requirements_file"
    else
        echo "Error: $requirements_file not found."
        exit 1
    fi
}

check_system_software()
{
    if brew list --versions libmagic > /dev/null; then
        echo "libmagic is installed."
    else
        echo "libmagic is not found. Install it before starting the server"
        exit 1
    fi
}

os_name=$(uname)
if [ "$os_name" == "Darwin" ]; then
    check_system_software
fi
create_venv

if [ "$os_name" == "Linux" ]; then
    avahi-publish-service -s "CL IMAGE REPO" _image_repo_api._tcp 5000 "CL Image Repo Service" &
fi
python -m src.wsgi


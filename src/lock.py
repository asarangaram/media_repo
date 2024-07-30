
from tendo import singleton
import os

def instance_already_running(config_object):
    lock_file = f"{config_object.FILE_STORAGE_LOCATION}/app.lock"
    if not os.path.exists(config_object.FILE_STORAGE_LOCATION):
        os.makedirs(config_object.FILE_STORAGE_LOCATION)
    try:
        singleton.SingleInstance(lockfile=lock_file) 
        already_running = False
    except IOError:
        already_running = True

    return already_running

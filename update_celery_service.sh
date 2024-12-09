#! /bin/bash

sudo systemctl daemon-reload
sudo systemctl restart celery
sudo systemctl status celery
#!/bin/bash

source .venv/bin/activate
python selfie.py

yesterday=$(date --date="yesterday" +"%Y-%m-%d")
commit_message="Generated image for $yesterday"

git add .
git commit -m "$commit_message"
git push

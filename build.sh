#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
cd backend
pip install --upgrade pip
pip install -r requirement.txt
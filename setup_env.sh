#!/bin/bash

echo "Creating .env file from .env.example..."

# Check if .env already exists
if [ -f ".env" ]; then
  echo "Warning: .env file already exists. Do you want to overwrite it? (y/N)"
  read -r response
  if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Operation cancelled."
    exit 0
  fi
fi

# Copy the example file
cp .env.example .env

echo ".env file created successfully."
echo "Please edit the .env file with your specific configuration values."

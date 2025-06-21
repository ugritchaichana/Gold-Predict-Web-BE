#!/bin/bash

# Script to initialize cache table for database caching
echo "Creating cache table for database caching..."
python manage.py createcachetable

echo "Cache table created successfully!"

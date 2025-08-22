#!/bin/bash

echo "🚀 Starting TapNex deployment build process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Clear existing static files
echo "🧹 Clearing existing static files..."
rm -rf staticfiles_build/*

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Verify static files were collected
echo "✅ Static files collected successfully!"
echo "📂 Static files location: $(python -c "import os; from pathlib import Path; print(Path(__file__).parent / 'staticfiles_build')")"

# List collected static files for verification
echo "📋 Checking collected static files:"
if [ -d "staticfiles_build/core/images" ]; then
    echo "   ✅ Images directory exists"
    ls -la staticfiles_build/core/images/
else
    echo "   ❌ Images directory missing!"
fi

if [ -d "staticfiles_build/sounds" ]; then
    echo "   ✅ Sounds directory exists"
    ls -la staticfiles_build/sounds/
else
    echo "   ❌ Sounds directory missing!"
fi

echo "🎉 Build process completed!"
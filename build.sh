#!/bin/bash

echo "🚀 Starting Vercel build process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Verify static files
echo "✅ Verifying static files..."
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

# Create a test to verify static files are accessible
echo "🧪 Testing static file accessibility..."
if [ -f "staticfiles_build/core/images/TAPNEX_LOGO_BG.jpg" ]; then
    echo "   ✅ TapNex logo exists"
    ls -la staticfiles_build/core/images/TAPNEX_LOGO_BG.jpg
else
    echo "   ❌ TapNex logo missing!"
fi

echo "🎉 Vercel build completed!"

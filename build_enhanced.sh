#!/bin/bash

# Enhanced Vercel Build Script for TapNex Ticketing System
echo "🚀 Starting Enhanced Vercel Build Process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p staticfiles_build
mkdir -p media

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Collect static files with extra verbosity
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear --verbosity=2

# Verify critical static files exist
echo "✅ Verifying critical static files..."
LOGO_PATH="staticfiles_build/images/logos/TAPNEX_LOGO_BG.jpg"
if [ -f "$LOGO_PATH" ]; then
    echo "✅ Logo file found: $LOGO_PATH"
    echo "📊 Logo file size: $(stat -c%s "$LOGO_PATH") bytes"
else
    echo "❌ Logo file missing: $LOGO_PATH"
    echo "📁 Available logo files:"
    find staticfiles_build -name "*.jpg" -o -name "*.png" | head -10
fi

# List static files structure
echo "📁 Static files structure:"
echo "📂 Root directories in staticfiles_build:"
ls -la staticfiles_build/ | head -10

echo "📂 Images directory:"
if [ -d "staticfiles_build/images" ]; then
    ls -la staticfiles_build/images/
else
    echo "❌ Images directory not found"
fi

echo "📂 Logos directory:"
if [ -d "staticfiles_build/images/logos" ]; then
    ls -la staticfiles_build/images/logos/
else
    echo "❌ Logos directory not found"
fi

# Test static file access patterns
echo "🔍 Testing static file patterns..."
echo "Available CSS files:"
find staticfiles_build -name "*.css" | head -5

echo "Available JS files:"
find staticfiles_build -name "*.js" | head -5

echo "Available image files:"
find staticfiles_build -name "*.jpg" -o -name "*.png" | head -10

# Create a static file manifest for debugging
echo "📝 Creating static file manifest..."
find staticfiles_build -type f > static_files_manifest.txt
echo "📊 Total static files: $(wc -l < static_files_manifest.txt)"

echo "🎉 Build completed successfully!"
echo "📊 Build summary:"
echo "- Static files collected: $(find staticfiles_build -type f | wc -l)"
echo "- Logo files found: $(find staticfiles_build -name "*LOGO*" | wc -l)"
echo "- Total build size: $(du -sh staticfiles_build 2>/dev/null | cut -f1 || echo 'Unknown')"

# Final verification
if [ -f "staticfiles_build/images/logos/TAPNEX_LOGO_BG.jpg" ]; then
    echo "✅ CRITICAL: Logo file successfully deployed!"
else
    echo "❌ CRITICAL: Logo file deployment failed!"
    exit 1
fi

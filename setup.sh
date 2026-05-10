#!/bin/bash

# Quick Setup for Advanced Stock Screener
# Uses available Python 3.12 to create environment

echo "🚀 Quick Setup for Advanced Stock Screener"
echo "=========================================="

# Clean up existing environments
echo "🧹 Cleaning up existing environments..."
rm -rf venv new_venv

# Create virtual environment with Python 3.12
echo "📦 Creating virtual environment..."
python3.12 -m venv venv

# Activate and install dependencies
echo "⚡ Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo "Run with: source venv/bin/activate && python app.py"

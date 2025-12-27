#!/bin/bash
# build.sh - Build script for Render deployment
# Trains models if they don't exist

set -e

echo "🔧 Installing dependencies..."
pip install -r requirements.txt
npm install

echo "🧠 Checking for trained models..."
if [ ! -f "early_warning_model_pipeline_tuned.joblib" ] || [ ! -f "label_encoder.joblib" ] || [ ! -f "student_risk_classifier_tuned.joblib" ]; then
    echo "📚 Models not found. Training on first deploy (this may take 2-3 minutes)..."
    python train_model.py
else
    echo "✅ Models already exist, skipping training"
fi

echo "🎨 Building Tailwind CSS..."
npm run tailwind:build

echo "✨ Build complete!"

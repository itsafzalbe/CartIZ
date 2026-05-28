#!/bin/bash

echo "🚀 Starting CartIZ Development Servers..."

# Function to clean up background processes when you press Ctrl+C
cleanup() {
    echo -e "\n🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap SIGINT (Ctrl+C) and run cleanup
trap cleanup SIGINT SIGTERM

# 1. Start Django Backend
echo "🐍 Starting Django backend..."
source .venv/bin/activate && python manage.py runserver &
BACKEND_PID=$!

# 2. Start Vite Frontend
echo "⚛️  Starting Vite frontend..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# Wait forever (until Ctrl+C is pressed)
wait

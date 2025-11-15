#!/bin/bash
# Unified startup script for all monitoring services
# This script runs all services in a single container

set -e

echo "========================================="
echo "  Network Monitoring System - Starting"
echo "========================================="
echo

# Initialize database
echo "📦 Initializing database..."
python -c "from src.database import init_db; init_db()"
echo "✅ Database initialized"
echo

# Start services in background
echo "🚀 Starting services..."

# Start FastAPI server
echo "  - Starting API server..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 &
API_PID=$!
echo "    API server started (PID: $API_PID)"

# Give API time to start
sleep 2

# Start scheduler service
echo "  - Starting scheduler service..."
python -m src.services.scheduler_service &
SCHEDULER_PID=$!
echo "    Scheduler started (PID: $SCHEDULER_PID)"

# Start internet monitor
echo "  - Starting internet monitor..."
python -m src.services.internet_monitor &
MONITOR_PID=$!
echo "    Internet monitor started (PID: $MONITOR_PID)"

echo
echo "✅ All services started successfully!"
echo
echo "========================================="
echo "  Service Status"
echo "========================================="
echo "API Server:        http://0.0.0.0:8080"
echo "Dashboard:         http://0.0.0.0:8080/api/v1/dashboard"
echo "Health Check:      http://0.0.0.0:8080/api/v1/health"
echo "API Docs:          http://0.0.0.0:8080/docs"
echo "========================================="
echo

# Function to handle shutdown
shutdown() {
    echo
    echo "🛑 Shutting down services..."
    kill $API_PID $SCHEDULER_PID $MONITOR_PID 2>/dev/null || true
    wait $API_PID $SCHEDULER_PID $MONITOR_PID 2>/dev/null || true
    echo "✅ All services stopped"
    exit 0
}

# Trap signals
trap shutdown SIGTERM SIGINT

# Wait for any service to exit
wait -n

# If we get here, one service died unexpectedly
echo "⚠️  A service has stopped unexpectedly"
shutdown

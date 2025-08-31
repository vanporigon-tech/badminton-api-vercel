#!/usr/bin/env python3
"""
Simple script to run the Badminton Rating Mini App
"""

import uvicorn
from config import settings

if __name__ == "__main__":
    print("🏸 Starting Badminton Rating Mini App...")
    print(f"📊 Environment: {'Development' if settings.DEBUG else 'Production'}")
    print(f"🌐 Server will be available at: http://localhost:8000")
    print(f"📱 Mini App will be available at: http://localhost:8000/app")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )


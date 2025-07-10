import sys
import uvicorn
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.resolve())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the FastAPI app
from backend.app.main import app, create_application

def test_app():
    """Test that the FastAPI app starts correctly"""
    try:
        # Test creating the application
        test_app = create_application()
        assert test_app is not None, "Failed to create FastAPI application"
        
        # Test the root endpoint
        from fastapi.testclient import TestClient
        client = TestClient(test_app)
        
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "running"
        
        # Test health check
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_app():
        # If tests pass, run the development server
        print("\nStarting development server...")
        uvicorn.run(
            "backend.app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )

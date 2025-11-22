from fastapi.middleware.cors import CORSMiddleware
from config import config

class CORSConfig:
    @staticmethod
    def get_config():
        """Get CORS configuration for FastAPI"""
        if config['app_env'] == 'production':
            allow_origins = ['https://your-production-domain.com']
        else:
            allow_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
        return {
            "allow_origins": allow_origins,
            "allow_credentials": True,
            "allow_methods": [
                "GET",
                "POST",
                "PUT",
                "DELETE",
            ],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "Access-Control-Allow-Headers",
                "Access-Control-Allow-Origin",
                "X-Requested-With",
                "Accept",
            ],
        }

    @staticmethod
    def setup_cors(app):
        """Setup CORS middleware for FastAPI app"""
        app.add_middleware(
            CORSMiddleware,
            **CORSConfig.get_config()
        )
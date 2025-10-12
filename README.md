# suspense_stories_api

- A RESTful API for managing suspense stories with user and admin authentication, built with FastAPI and MongoDB.  

### Features
- Dual Authentication System (User and Admin roles)
- CRUD operations for stories &amp; channels
- Log of API request &amp; response
- Channel specific story listings
- Motor to use async await functions
- JWT authentication for dual auth guard
- Usage of FastAPI background jobs for story processing
- Redis caching mongo query cache
- Email notification on new stories published
- Pagination support for list pages (Channel, Story, Users, Admins)
- HTML email templates for notifications

### Future Implementations
- Rate limiting for API endpoints
- Search functionality for stories
- Forget password functionality
- Email template centralization with Placeholder Values

# HOW TO SET UP
- CONNECT WITH MONGODB
- RUN REDIS CACHE
- RUN FASTAPI
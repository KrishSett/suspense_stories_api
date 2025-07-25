# suspense_stories_api

- A RESTful API for managing suspense stories with user and admin authentication, built with FastAPI and MongoDB.  

### Features
- Dual Authentication System (User and Admin roles)
- CRUD operations for stories &amp; channels
- Log of API request &amp; response
- Channel specific story listings
- Motor to use async await functions
- JWT authentication for dual auth guard
- Usage of FastAPI background jobs
- Redis caching mongo query cache
- Email notification on new stories published

### Future Implementations
- Pagination support for list pages (Channel, Story)
- Rate limiting for API endpoints
- Search functionality for stories
- Threading for story processing
- HTML email templates for notifications
# suspense_stories_api

- A RESTful API for managing suspense stories with user and admin authentication, built with FastAPI and MongoDB.  

### Features
- Dual Authentication System (User and Admin roles)
- CRUD operations for stories &amp; channels
- Categorize channels
- Channel specific story listings
- Motor to use async await functions
- JWT authentication for dual auth guard

### Future Implementations
- Redis caching mongo query cache
- Push notification on new stories
- Pagination support 
- Rate limiting for API endpoints
- Usage of kafka queue to run background jobs
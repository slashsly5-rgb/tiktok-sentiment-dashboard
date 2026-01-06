# TikTok Scraper API Documentation

## Overview
RESTful API for the TikTok Scraper application. Provides endpoints for managing scraping jobs, retrieving analytics data, and accessing scraped content.

- **Base URL**: `http://localhost:5000/api`
- **Version**: 1.0
- **Content-Type**: `application/json`

## Authentication
Currently using session-based authentication. JWT implementation planned for production.

## Endpoints

### Health Check

#### GET /health
Check if the API is running.

- **URL**: `/health`
- **Method**: `GET`
- **Auth Required**: No
- **Request Parameters**: None
- **Response**:
  ```json
  {
    "status": "healthy",
    "timestamp": "2025-12-27T10:00:00Z"
  }
  ```
- **Error Responses**: None

---

### Scraping Jobs

#### GET /jobs
Retrieve all scraping jobs.

- **URL**: `/api/jobs`
- **Method**: `GET`
- **Auth Required**: No (will require auth in production)
- **Query Parameters**:
  - `status` (optional): Filter by job status (`pending`, `running`, `completed`, `failed`)
  - `limit` (optional): Number of results to return (default: 50)
  - `offset` (optional): Pagination offset (default: 0)

- **Response**:
  ```json
  {
    "jobs": [
      {
        "id": 1,
        "url": "https://tiktok.com/@username",
        "status": "completed",
        "created_at": "2025-12-27T10:00:00Z",
        "completed_at": "2025-12-27T10:05:00Z",
        "videos_scraped": 150
      }
    ],
    "total": 100,
    "limit": 50,
    "offset": 0
  }
  ```
- **Error Responses**:
  - `500`: Database error

#### POST /jobs
Create a new scraping job.

- **URL**: `/api/jobs`
- **Method**: `POST`
- **Auth Required**: No (will require auth in production)
- **Request Body**:
  ```json
  {
    "url": "https://tiktok.com/@username",
    "type": "user",
    "options": {
      "max_videos": 100,
      "include_comments": true
    }
  }
  ```
- **Response**:
  ```json
  {
    "job_id": 123,
    "status": "pending",
    "message": "Scraping job created successfully"
  }
  ```
- **Error Responses**:
  - `400`: Invalid URL or parameters
  - `500`: Failed to create job

#### GET /jobs/:id
Retrieve details for a specific job.

- **URL**: `/api/jobs/:id`
- **Method**: `GET`
- **Auth Required**: No
- **URL Parameters**:
  - `id` (required): Job ID

- **Response**:
  ```json
  {
    "id": 123,
    "url": "https://tiktok.com/@username",
    "status": "running",
    "progress": 45,
    "created_at": "2025-12-27T10:00:00Z",
    "videos_scraped": 45,
    "total_videos": 100
  }
  ```
- **Error Responses**:
  - `404`: Job not found
  - `500`: Database error

---

### Analytics

#### GET /analytics/overview
Get overview analytics for all scraped data.

- **URL**: `/api/analytics/overview`
- **Method**: `GET`
- **Auth Required**: No
- **Query Parameters**:
  - `start_date` (optional): Filter data from this date (ISO 8601)
  - `end_date` (optional): Filter data until this date (ISO 8601)

- **Response**:
  ```json
  {
    "total_videos": 5000,
    "total_users": 50,
    "total_views": 15000000,
    "total_likes": 500000,
    "avg_engagement_rate": 3.5,
    "date_range": {
      "start": "2025-12-01",
      "end": "2025-12-27"
    }
  }
  ```
- **Error Responses**:
  - `400`: Invalid date format
  - `500`: Database error

#### GET /analytics/trends
Get trending analysis data.

- **URL**: `/api/analytics/trends`
- **Method**: `GET`
- **Auth Required**: No
- **Query Parameters**:
  - `period` (optional): Time period (`day`, `week`, `month`) - default: `week`
  - `metric` (optional): Metric to analyze (`views`, `likes`, `shares`, `comments`) - default: `views`

- **Response**:
  ```json
  {
    "period": "week",
    "metric": "views",
    "data": [
      {
        "date": "2025-12-20",
        "value": 50000,
        "videos": 100
      },
      {
        "date": "2025-12-21",
        "value": 65000,
        "videos": 120
      }
    ]
  }
  ```
- **Error Responses**:
  - `400`: Invalid parameters
  - `500`: Database error

---

### Videos

#### GET /videos
Retrieve scraped videos.

- **URL**: `/api/videos`
- **Method**: `GET`
- **Auth Required**: No
- **Query Parameters**:
  - `user_id` (optional): Filter by user ID
  - `min_views` (optional): Minimum view count
  - `min_likes` (optional): Minimum like count
  - `sort` (optional): Sort field (`views`, `likes`, `created_at`) - default: `created_at`
  - `order` (optional): Sort order (`asc`, `desc`) - default: `desc`
  - `limit` (optional): Results per page (default: 50, max: 100)
  - `offset` (optional): Pagination offset (default: 0)

- **Response**:
  ```json
  {
    "videos": [
      {
        "id": "7123456789012345678",
        "url": "https://tiktok.com/@user/video/7123456789012345678",
        "description": "Video description",
        "created_at": "2025-12-25T15:30:00Z",
        "views": 100000,
        "likes": 5000,
        "shares": 500,
        "comments": 200,
        "user": {
          "id": "user123",
          "username": "username",
          "display_name": "Display Name"
        }
      }
    ],
    "total": 500,
    "limit": 50,
    "offset": 0
  }
  ```
- **Error Responses**:
  - `400`: Invalid parameters
  - `500`: Database error

#### GET /videos/:id
Get details for a specific video.

- **URL**: `/api/videos/:id`
- **Method**: `GET`
- **Auth Required**: No
- **URL Parameters**:
  - `id` (required): TikTok video ID

- **Response**:
  ```json
  {
    "id": "7123456789012345678",
    "url": "https://tiktok.com/@user/video/7123456789012345678",
    "description": "Video description",
    "created_at": "2025-12-25T15:30:00Z",
    "views": 100000,
    "likes": 5000,
    "shares": 500,
    "comments_count": 200,
    "hashtags": ["#trending", "#viral"],
    "music": {
      "id": "music123",
      "title": "Song Title",
      "author": "Artist Name"
    },
    "user": {
      "id": "user123",
      "username": "username",
      "display_name": "Display Name",
      "followers": 50000
    }
  }
  ```
- **Error Responses**:
  - `404`: Video not found
  - `500`: Database error

---

### Users

#### GET /users
Retrieve scraped user profiles.

- **URL**: `/api/users`
- **Method**: `GET`
- **Auth Required**: No
- **Query Parameters**:
  - `min_followers` (optional): Minimum follower count
  - `sort` (optional): Sort field (`followers`, `videos`, `username`) - default: `followers`
  - `order` (optional): Sort order (`asc`, `desc`) - default: `desc`
  - `limit` (optional): Results per page (default: 50)
  - `offset` (optional): Pagination offset (default: 0)

- **Response**:
  ```json
  {
    "users": [
      {
        "id": "user123",
        "username": "username",
        "display_name": "Display Name",
        "bio": "User bio",
        "followers": 50000,
        "following": 500,
        "total_likes": 1000000,
        "total_videos": 150,
        "verified": true
      }
    ],
    "total": 50,
    "limit": 50,
    "offset": 0
  }
  ```
- **Error Responses**:
  - `400`: Invalid parameters
  - `500`: Database error

#### GET /users/:id
Get details for a specific user.

- **URL**: `/api/users/:id`
- **Method**: `GET`
- **Auth Required**: No
- **URL Parameters**:
  - `id` (required): TikTok user ID or username

- **Response**:
  ```json
  {
    "id": "user123",
    "username": "username",
    "display_name": "Display Name",
    "bio": "User bio",
    "avatar_url": "https://...",
    "followers": 50000,
    "following": 500,
    "total_likes": 1000000,
    "total_videos": 150,
    "verified": true,
    "created_at": "2020-01-15T10:00:00Z",
    "scraped_at": "2025-12-27T10:00:00Z"
  }
  ```
- **Error Responses**:
  - `404`: User not found
  - `500`: Database error

---

## Data Models

### Job Object
```json
{
  "id": "integer - Unique job identifier",
  "url": "string - TikTok URL to scrape",
  "type": "string - Job type (user, video, hashtag)",
  "status": "string - Job status (pending, running, completed, failed)",
  "progress": "integer - Completion percentage (0-100)",
  "created_at": "string - ISO 8601 timestamp",
  "started_at": "string - ISO 8601 timestamp (nullable)",
  "completed_at": "string - ISO 8601 timestamp (nullable)",
  "error": "string - Error message if failed (nullable)",
  "videos_scraped": "integer - Number of videos scraped",
  "options": "object - Job configuration options"
}
```

### Video Object
```json
{
  "id": "string - TikTok video ID",
  "url": "string - Full TikTok video URL",
  "description": "string - Video caption/description",
  "created_at": "string - ISO 8601 timestamp",
  "views": "integer - View count",
  "likes": "integer - Like count",
  "shares": "integer - Share count",
  "comments_count": "integer - Comment count",
  "hashtags": "array[string] - Hashtags used",
  "user_id": "string - Author user ID",
  "music_id": "string - Music track ID (nullable)",
  "scraped_at": "string - ISO 8601 timestamp"
}
```

### User Object
```json
{
  "id": "string - TikTok user ID",
  "username": "string - User handle",
  "display_name": "string - Display name",
  "bio": "string - User biography",
  "avatar_url": "string - Profile picture URL",
  "followers": "integer - Follower count",
  "following": "integer - Following count",
  "total_likes": "integer - Total likes received",
  "total_videos": "integer - Total videos posted",
  "verified": "boolean - Verification status",
  "created_at": "string - Account creation date (ISO 8601)",
  "scraped_at": "string - Last scrape timestamp (ISO 8601)"
}
```

## Error Handling

All error responses follow this format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional error details (optional)"
  }
}
```

### Common Error Codes
- `INVALID_REQUEST`: Request validation failed
- `NOT_FOUND`: Requested resource not found
- `DATABASE_ERROR`: Database operation failed
- `SCRAPER_ERROR`: Scraping operation failed
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Unexpected server error

### HTTP Status Codes
- `200`: Success
- `201`: Resource created
- `400`: Bad request (invalid parameters)
- `401`: Unauthorized (future implementation)
- `404`: Resource not found
- `429`: Rate limit exceeded (future implementation)
- `500`: Internal server error

## Rate Limiting
**Note**: Rate limiting is planned but not yet implemented.

Planned limits:
- 100 requests per minute per IP
- 1000 requests per hour per IP

Rate limit headers (future):
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640606400
```

## Pagination

Endpoints that return lists support pagination:
- `limit`: Number of results per page (default varies by endpoint)
- `offset`: Number of results to skip

Response includes pagination metadata:
```json
{
  "data": [...],
  "total": 1000,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

## Filtering & Sorting

Many endpoints support filtering and sorting via query parameters. Refer to individual endpoint documentation for supported parameters.

## CORS
CORS is enabled for development. Production configuration will restrict origins.

## Changelog

### Version 1.0 (2025-12-27)
- Initial API documentation
- Core endpoints defined: jobs, videos, users, analytics
- Basic authentication placeholder
- Error handling standards established

---

**Maintained by**: Development Team
**Last Updated**: 2025-12-27
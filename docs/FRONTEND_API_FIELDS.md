# Frontend API Field Reference

This document describes all data fields returned by the backend API endpoints, formatted in **camelCase** for JavaScript/React consumption.

## Table of Contents
- [Videos](#videos)
- [Comments](#comments)
- [Sentiment Analysis](#sentiment-analysis)
- [Analytics & Statistics](#analytics--statistics)
- [API Response Examples](#api-response-examples)

---

## Videos

### Video Object Fields

When fetching videos from any endpoint, you'll receive objects with these fields:

| Field Name (camelCase) | Type | Description | Database Field |
|----------------------|------|-------------|----------------|
| `id` | UUID | Unique identifier | `id` |
| `tiktokId` | string | TikTok video ID from URL | `tiktok_id` |
| `url` | string | TikTok video URL | `url` |
| `authorUsername` | string | TikTok creator username | `author_username` |
| `description` | string | Video caption/description | `description` |
| `postUrl` | string | Supabase Storage URL for video screenshot | `post_url` |
| `transcribedUrl` | string | Supabase Storage URL for transcription file | `transcribed_url` |
| `summary` | string | AI-generated video summary | `summary` |
| `screenshotBase64` | string | Base64 encoded screenshot | `screenshot_base64` |
| `viewsCount` | number | Total video views | `views_count` |
| `likesCount` | number | Total likes | `likes_count` |
| `sharesCount` | number | Total shares | `shares_count` |
| `commentsCount` | number | Total comments | `comments_count` |
| `hashtags` | array | Array of hashtag strings | `hashtags` |
| `searchKeyword` | string | Keyword used to discover video | `search_keyword` |
| `scrapedAt` | timestamp | When video was scraped | `scraped_at` |
| `createdAt` | timestamp | Database record creation time | `created_at` |
| `engagementRate` | number | Calculated engagement rate (likes+comments+shares)/views | `engagement_rate` (computed) |

### Nested Fields

Videos may include nested objects when specific query parameters are used:

#### With Comments (`include_comments=true`)
```javascript
{
  // ... video fields
  "comments": [/* array of Comment objects */]
}
```

#### With Sentiment (`include_sentiment=true`)
```javascript
{
  // ... video fields
  "sentiment": {/* Sentiment object */}
}
```

---

## Comments

### Comment Object Fields

| Field Name (camelCase) | Type | Description | Database Field |
|----------------------|------|-------------|----------------|
| `id` | UUID | Unique identifier | `id` |
| `videoId` | UUID | Associated video ID | `video_id` |
| `commentText` | string | Comment content | `comment_text` or `text` |
| `text` | string | Comment content (alternative field) | `text` |
| `authorUsername` | string | Comment author username | `author_username` |
| `likesCount` | number | Comment likes | `likes_count` |
| `createdAt` | timestamp | Comment creation time | `created_at` |

> **Note**: Both `commentText` and `text` fields represent the same data. The API normalizes this to prefer `commentText`.

---

## Sentiment Analysis

### Sentiment Object Fields

| Field Name (camelCase) | Type | Description | Database Field |
|----------------------|------|-------------|----------------|
| `id` | UUID | Unique identifier | `id` |
| `videoId` | UUID | Associated video ID | `video_id` |
| `sentiment` | string | Overall sentiment: `positive`, `negative`, `neutral`, `mixed` | `sentiment` or `overall_sentiment` |
| `overallSentiment` | string | Overall sentiment (alternative field) | `overall_sentiment` |
| `sentimentScore` | number | Sentiment score (1-10 scale) | `sentiment_score` |
| `topic` | string | Main topic discussed | `topic` |
| `discussionPoints` | string | Key discussion points | `discussion_points` |
| `keyIssues` | array | Array of key issues/topics | `key_issues` |
| `transcript` | string | AI-generated transcript | `transcript` |
| `summary` | string | AI-generated summary | `summary` |
| `analyzedAt` | timestamp | Analysis completion time | `analyzed_at` |

### Nested Fields

#### With Video (`include_video=true`)
```javascript
{
  // ... sentiment fields
  "video": {/* Video object */}
}
```

---

## Analytics & Statistics

### Dashboard Analytics

**Endpoint**: `GET /api/analytics/dashboard?days=7`

```javascript
{
  "periodDays": 7,
  "videoStats": {
    "total": 150,
    "totalViews": 1250000,
    "totalLikes": 45000,
    "totalComments": 8500,
    "totalShares": 3200,
    "avgViewsPerVideo": 8333.33
  },
  "sentimentStats": {
    "analyzedCount": 140,
    "avgScore": 6.5,
    "sentimentBreakdown": {
      "positive": 85,
      "negative": 30,
      "neutral": 20,
      "mixed": 5
    }
  },
  "topAuthors": [/* array of author stats */],
  "topHashtags": [/* array of hashtag stats */],
  "topKeywords": [/* array of keyword performance */]
}
```

### Top Authors

**Endpoint**: `GET /api/analytics/top-authors?days=30&limit=10`

```javascript
{
  "periodDays": 30,
  "metric": "videos",
  "count": 10,
  "topAuthors": [
    {
      "username": "user123",
      "videoCount": 25,
      "totalViews": 500000,
      "totalLikes": 15000,
      "avgViews": 20000
    }
    // ...
  ]
}
```

### Top Hashtags

**Endpoint**: `GET /api/analytics/top-hashtags?days=30&limit=20`

```javascript
{
  "periodDays": 30,
  "count": 20,
  "topHashtags": [
    {
      "hashtag": "#politics",
      "videoCount": 85,
      "totalViews": 2500000,
      "avgViews": 29411.76
    }
    // ...
  ]
}
```

### Top Issues

**Endpoint**: `GET /api/analytics/top-issues?days=30&limit=20`

```javascript
{
  "periodDays": 30,
  "count": 20,
  "topIssues": [
    {
      "issue": "Infrastructure Development",
      "mentionCount": 45,
      "avgSentiment": 7.2,
      "videoCount": 42
    }
    // ...
  ]
}
```

### Keyword Performance

**Endpoint**: `GET /api/analytics/keyword-performance?days=30`

```javascript
{
  "periodDays": 30,
  "count": 5,
  "keywords": [
    {
      "keyword": "Abang Johari",
      "videoCount": 120,
      "totalViews": 3500000,
      "avgSentiment": 6.8,
      "sentimentDistribution": {
        "positive": 75,
        "negative": 25,
        "neutral": 20
      }
    }
    // ...
  ]
}
```

### Sentiment Trends

**Endpoint**: `GET /api/analytics/sentiment-trends?days=30&interval=day`

```javascript
{
  "interval": "day",
  "dataPoints": [
    {
      "date": "2025-12-20",
      "avgScore": 6.5,
      "videoCount": 25,
      "sentimentBreakdown": {
        "positive": 15,
        "negative": 7,
        "neutral": 3
      }
    }
    // ...
  ]
}
```

### Engagement Statistics

**Endpoint**: `GET /api/analytics/engagement-stats?days=7&group_by=author`

```javascript
{
  "avgEngagementRate": 0.0425,
  "avgLikeRate": 0.0360,
  "avgCommentRate": 0.0045,
  "avgShareRate": 0.0020,
  "totalVideos": 150,
  "periodDays": 7,
  "distribution": [
    {
      "author": "user123",
      "engagementRate": 0.0550,
      "views": 125000
    }
    // ...
  ]
}
```

### Comment Statistics

**Endpoint**: `GET /api/comments/stats?days=7`

```javascript
{
  "totalComments": 8500,
  "uniqueAuthors": 4200,
  "avgLikesPerComment": 5.2,
  "totalLikes": 44200,
  "periodDays": 7
}
```

### Top Commenters

**Endpoint**: `GET /api/comments/top-commenters?days=30&limit=10`

```javascript
{
  "periodDays": 30,
  "count": 10,
  "topCommenters": [
    {
      "username": "commenter123",
      "commentCount": 150,
      "totalLikes": 2500,
      "avgLikes": 16.67
    }
    // ...
  ]
}
```

---

## API Response Examples

### GET /videos

Get recent videos with optional sentiment data.

**Request**:
```
GET /videos?limit=10&days=7&include_sentiment=true
```

**Response**:
```javascript
{
  "count": 10,
  "videos": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "tiktokId": "7234567890123456789",
      "url": "https://tiktok.com/@user/video/7234567890123456789",
      "authorUsername": "user123",
      "description": "Discussing infrastructure development in Sarawak #politics",
      "viewsCount": 125000,
      "likesCount": 4500,
      "sharesCount": 320,
      "commentsCount": 850,
      "hashtags": ["#politics", "#sarawak", "#infrastructure"],
      "searchKeyword": "Abang Johari",
      "scrapedAt": "2025-12-20T10:30:00Z",
      "createdAt": "2025-12-20T10:30:00Z",
      "sentiment": "positive",
      "sentimentScore": 7.5,
      "summary": "Discussion about new infrastructure projects...",
      "topic": "Infrastructure Development",
      "keyIssues": ["Roads", "Bridges", "Rural Development"]
    }
    // ... 9 more videos
  ]
}
```

### GET /api/videos/:videoId/complete

Get complete video view with all related data.

**Request**:
```
GET /api/videos/550e8400-e29b-41d4-a716-446655440000/complete
```

**Response**:
```javascript
{
  "video": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "tiktokId": "7234567890123456789",
    "authorUsername": "user123",
    "description": "Discussing infrastructure...",
    "viewsCount": 125000,
    "likesCount": 4500,
    "sharesCount": 320,
    "commentsCount": 850,
    // ... other video fields
  },
  "comments": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "videoId": "550e8400-e29b-41d4-a716-446655440000",
      "commentText": "Great infrastructure plans!",
      "authorUsername": "commenter1",
      "likesCount": 25,
      "createdAt": "2025-12-20T11:00:00Z"
    }
    // ... more comments
  ],
  "sentiment": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "videoId": "550e8400-e29b-41d4-a716-446655440000",
    "sentiment": "positive",
    "sentimentScore": 7.5,
    "topic": "Infrastructure Development",
    "discussionPoints": "Users are discussing...",
    "keyIssues": ["Roads", "Bridges", "Rural Development"],
    "analyzedAt": "2025-12-20T12:00:00Z"
  },
  "stats": {
    "commentCount": 850,
    "analyzed": true
  }
}
```

### GET /api/videos/search

Advanced video search with multiple filters.

**Request**:
```
GET /api/videos/search?keyword=infrastructure&min_views=10000&sort_by=views_count&limit=20
```

**Response**:
```javascript
{
  "count": 20,
  "total": 145,
  "offset": 0,
  "limit": 20,
  "filtersApplied": {
    "keyword": "infrastructure",
    "min_views": 10000,
    "sort_by": "views_count"
  },
  "videos": [
    // ... array of video objects
  ]
}
```

### GET /api/comments

Get comments with pagination and filtering.

**Request**:
```
GET /api/comments?limit=50&offset=0&min_likes=10
```

**Response**:
```javascript
{
  "count": 50,
  "total": 2500,
  "offset": 0,
  "limit": 50,
  "comments": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "videoId": "550e8400-e29b-41d4-a716-446655440000",
      "commentText": "Great video!",
      "authorUsername": "user456",
      "likesCount": 15,
      "createdAt": "2025-12-20T11:00:00Z"
    }
    // ... 49 more comments
  ]
}
```

### GET /sentiment/overview

Get sentiment statistics overview.

**Request**:
```
GET /sentiment/overview?days=30
```

**Response**:
```javascript
{
  "totalVideos": 450,
  "totalAnalyzed": 420,
  "avgSentiment": 6.7,
  "sentimentBreakdown": {
    "positive": 250,
    "negative": 100,
    "neutral": 50,
    "mixed": 20
  },
  "topKeyword": "Abang Johari",
  "totalViews": 15000000
}
```

---

## Pagination Pattern

All paginated endpoints follow this consistent pattern:

```javascript
{
  "count": 50,        // Number of items in current response
  "total": 2500,      // Total items available
  "offset": 0,        // Current offset
  "limit": 50,        // Requested limit
  "[dataKey]": []     // Array of items (varies by endpoint)
}
```

Common data keys:
- `videos` - for video lists
- `comments` - for comment lists
- `analyses` - for sentiment analysis lists

---

## TypeScript Type Definitions

```typescript
// Video Type
interface Video {
  id: string;
  tiktokId: string;
  url: string;
  authorUsername: string;
  description?: string;
  postUrl?: string;
  transcribedUrl?: string;
  summary?: string;
  screenshotBase64?: string;
  viewsCount: number;
  likesCount: number;
  sharesCount: number;
  commentsCount: number;
  hashtags: string[];
  searchKeyword?: string;
  scrapedAt: string;
  createdAt: string;
  engagementRate?: number;

  // Optional nested objects
  comments?: Comment[];
  sentiment?: Sentiment;
}

// Comment Type
interface Comment {
  id: string;
  videoId: string;
  commentText: string;
  text?: string;
  authorUsername: string;
  likesCount: number;
  createdAt: string;
}

// Sentiment Type
interface Sentiment {
  id: string;
  videoId: string;
  sentiment: 'positive' | 'negative' | 'neutral' | 'mixed';
  overallSentiment?: 'positive' | 'negative' | 'neutral' | 'mixed';
  sentimentScore: number;
  topic?: string;
  discussionPoints?: string;
  keyIssues: string[];
  transcript?: string;
  summary?: string;
  analyzedAt: string;

  // Optional nested object
  video?: Video;
}

// Paginated Response Type
interface PaginatedResponse<T> {
  count: number;
  total: number;
  offset: number;
  limit: number;
  [key: string]: T[] | number;
}
```

---

## Migration Notes

### From snake_case to camelCase

If you're migrating from directly accessing the database or an older API version:

| Old Field | New Field |
|-----------|-----------|
| `tiktok_id` | `tiktokId` |
| `author_username` | `authorUsername` |
| `views_count` | `viewsCount` |
| `likes_count` | `likesCount` |
| `comments_count` | `commentsCount` |
| `shares_count` | `sharesCount` |
| `search_keyword` | `searchKeyword` |
| `scraped_at` | `scrapedAt` |
| `created_at` | `createdAt` |
| `video_id` | `videoId` |
| `comment_text` | `commentText` |
| `overall_sentiment` | `sentiment` or `overallSentiment` |
| `sentiment_score` | `sentimentScore` |
| `discussion_points` | `discussionPoints` |
| `key_issues` | `keyIssues` |
| `analyzed_at` | `analyzedAt` |

---

## Support

For questions or issues with the API, please refer to:
- [API Documentation](./API.md)
- [Local Setup Guide](./LOCAL_SETUP.md)
- GitHub Issues: https://github.com/your-repo/issues

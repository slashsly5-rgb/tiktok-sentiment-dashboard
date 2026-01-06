# Field Naming Fix - Frontend/Backend Synchronization

## Issue
The frontend was displaying "@unknown" for usernames and showing 0 for all engagement metrics (views, likes, comments, shares) because there was a mismatch between:
- **Backend API**: Returning camelCase field names (e.g., `authorUsername`, `viewsCount`)
- **Frontend Components**: Expecting snake_case field names (e.g., `author_username`, `views_count`)

## Root Cause
When we implemented the field transformation layer in the backend ([backend/transform.py](backend/transform.py)), we converted all database field names from snake_case to camelCase for the API responses. However, the frontend components were not updated to use the new camelCase naming convention.

## Solution
Updated all frontend components to use camelCase field names that match the backend API responses.

---

## Files Modified

### Frontend Components

#### 1. [VideoCard.jsx](frontend/src/components/VideoCard.jsx)
**Changes:**
- `video.author_username` → `video.authorUsername`
- `video.views_count` → `video.viewsCount`
- `video.likes_count` → `video.likesCount`
- `video.comments_count` → `video.commentsCount`
- `video.shares_count` → `video.sharesCount`
- `video.scraped_at` → `video.scrapedAt`
- `video.key_issues` → `video.keyIssues`
- Updated PropTypes to match camelCase naming

#### 2. [VideoList.jsx](frontend/src/components/VideoList.jsx)
**Changes:**
- Search filter: Updated field references to camelCase
  - `video.author_username` → `video.authorUsername`
  - `video.search_keyword` → `video.searchKeyword`
- Sort functionality: Updated all engagement metric references
  - `video.scraped_at` → `video.scrapedAt`
  - `video.views_count` → `video.viewsCount`
  - `video.likes_count` → `video.likesCount`
  - `video.comments_count` → `video.commentsCount`
  - `video.shares_count` → `video.sharesCount`
- Updated PropTypes to match camelCase naming

#### 3. [api.js](frontend/src/services/api.js)
**Changes:**
- `item.video_count` → `item.videoCount` (in `formatKeyIssues` function)

---

## Field Mapping Reference

### Video Fields
| Database (snake_case) | API Response (camelCase) | Frontend Usage |
|-----------------------|-------------------------|----------------|
| `id` | `id` | `video.id` |
| `tiktok_id` | `tiktokId` | `video.tiktokId` |
| `url` | `url` | `video.url` |
| `author_username` | `authorUsername` | `video.authorUsername` |
| `description` | `description` | `video.description` |
| `views_count` | `viewsCount` | `video.viewsCount` |
| `likes_count` | `likesCount` | `video.likesCount` |
| `comments_count` | `commentsCount` | `video.commentsCount` |
| `shares_count` | `sharesCount` | `video.sharesCount` |
| `hashtags` | `hashtags` | `video.hashtags` |
| `search_keyword` | `searchKeyword` | `video.searchKeyword` |
| `scraped_at` | `scrapedAt` | `video.scrapedAt` |
| `created_at` | `createdAt` | `video.createdAt` |
| `screenshot_base64` | `screenshotBase64` | `video.screenshotBase64` |

### Sentiment Fields
| Database (snake_case) | API Response (camelCase) | Frontend Usage |
|-----------------------|-------------------------|----------------|
| `sentiment` | `sentiment` | `video.sentiment` |
| `sentiment_score` | `sentimentScore` | `video.sentimentScore` |
| `key_issues` | `keyIssues` | `video.keyIssues` |
| `summary` | `summary` | `video.summary` |

---

## Expected Result

After these changes, the frontend should now correctly display:

1. ✅ **Username**: Shows actual TikTok username instead of "@unknown"
   - Example: `@user123` instead of `@unknown`

2. ✅ **View Count**: Shows actual view numbers
   - Example: `125,000` instead of `0`

3. ✅ **Like Count**: Shows actual like numbers
   - Example: `4,500` instead of `0`

4. ✅ **Comment Count**: Shows actual comment numbers
   - Example: `850` instead of `0`

5. ✅ **Share Count**: Shows actual share numbers
   - Example: `320` instead of `0`

6. ✅ **Engagement Rate**: Calculates correctly based on actual metrics
   - Example: `4.5%` instead of `0.0%`

---

## Testing

To verify the fix is working:

1. **Start the backend API**:
   ```bash
   cd backend
   python run_api.py
   ```

2. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Check the video cards**:
   - Navigate to the dashboard
   - Verify that video cards show:
     - Actual usernames (not "@unknown")
     - Real engagement metrics (not all zeros)
     - Proper hashtags display
     - Sentiment badges and scores

4. **Test search and filtering**:
   - Search by username → Should work
   - Filter by sentiment → Should work
   - Sort by views/likes → Should work correctly

---

## Related Documentation

- [Frontend API Fields Reference](docs/FRONTEND_API_FIELDS.md) - Complete field documentation
- [Backend Transformation Utility](backend/transform.py) - Field transformation logic
- [API Documentation](docs/API.md) - API endpoint documentation

---

## Migration Notes

**For Future Development:**
- Always use camelCase for frontend field names
- The backend handles transformation automatically via [backend/transform.py](backend/transform.py)
- Database uses snake_case (PostgreSQL convention)
- API returns camelCase (JavaScript convention)
- No manual transformation needed in frontend - just use the camelCase names

**If adding new fields:**
1. Add to database schema with snake_case
2. Add mapping to `VIDEO_FIELD_MAP`, `COMMENT_FIELD_MAP`, or `SENTIMENT_FIELD_MAP` in [backend/transform.py](backend/transform.py)
3. Use camelCase in frontend components
4. Update TypeScript types in [docs/FRONTEND_API_FIELDS.md](docs/FRONTEND_API_FIELDS.md)

---

## Status
✅ **RESOLVED** - All frontend components now use camelCase field names matching the backend API responses.

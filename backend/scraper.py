import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import re
import os
import json
from typing import Optional, List, Dict, Any
from database import SupabaseClient
import logging

# Configure logging
# logging.basicConfig(level=logging.INFO) # REMOVED to avoid conflict
logger = logging.getLogger(__name__)


def extract_tiktok_id(url: str) -> Optional[str]:
    """
    Extract TikTok video ID from URL

    Args:
        url: TikTok video URL

    Returns:
        Video ID if found, None otherwise

    Example:
        https://www.tiktok.com/@user/video/1234567890 -> 1234567890
    """
    try:
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        logger.error(f"Error extracting TikTok ID from {url}: {e}")
        return None


class TikTokScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.playwright = None

    async def start(self):
        self.playwright = await async_playwright().start()
        logger.info(f"Launching browser (Headless={self.headless})...")
        
        args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-infobars',
            '--ignore-certificate-errors',
            '--ignore-ssl-errors',
            '--disable-extensions'
        ]
        
        if not self.headless:
            args.append('--start-maximized')

        # CLOUD FIX: Force headless if on Linux/Streamlit Cloud
        # Streamlit Cloud runs on Linux and has no display. 'Visible' mode will crash it.
        if os.name == 'posix':  # Linux/Mac
             if not self.headless:
                 print("WARNING: 'Visible' mode requested but running on Linux/Cloud. Forcing HEADLESS to prevent crash.")
                 self.headless = True
        
        # CLOUD FIX: Do not specify channel="chrome". 
        # Use bundled chromium which is guaranteed to be present after 'playwright install'
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            # channel="chrome", # REMOVED: Causes crash on Cloud where only Chromium is available
            args=args
        )
        # Load auth state (preferred) or cookies
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        auth_file = os.path.join(root_dir, "auth.json")
        cookie_file = os.path.join(root_dir, "cookies.json")
        
        if os.path.exists(auth_file):
            # Create context with storage state (Cookies + LocalStorage)
            self.context = await self.browser.new_context(
                storage_state=auth_file,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                locale='en-US',
                timezone_id='America/New_York'
            )
            logger.info(f"Loaded authentication from {auth_file}")
        else:
            # Fallback to standard context (and maybe cookies.json)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            if os.path.exists(cookie_file):
                try:
                    with open(cookie_file, 'r') as f:
                        cookies = json.load(f)
                    await self.context.add_cookies(cookies)
                    logger.info(f"Loaded {len(cookies)} cookies from {cookie_file}")
                except Exception as e:
                    logger.error(f"Failed to load cookies: {e}")

        # Add init script to hide webdriver property
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

    async def stop(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def search_videos(self, keyword, limit=3):
        if not self.context:
            await self.start()
            
        page = await self.context.new_page()
        encoded_keyword = keyword.replace(" ", "%20")
        url = f"https://www.tiktok.com/search?q={encoded_keyword}"
        
        print(f"Navigating to {url}")
        await page.goto(url)
        
        # Handle "Log in to search" Modal - Aggressive Strategy
        try:
            await asyncio.sleep(3) # Wait for modal to fully render
            
            # 1. Try Escape Key (Most robust)
            print("Trying Escape key...")
            await page.keyboard.press("Escape")
            await asyncio.sleep(1)
            
            # 2. Try clicking the "X" button with various selectors
            close_selectors = [
                '[data-e2e="modal-close-inner-button"]',
                '[data-e2e="modal-close"]',
                'button[aria-label="Close"]',
                'div[role="dialog"] button',
                'svg[class*="StyledCloseIcon"]',
                '#login-modal-close'
            ]
            
            for selector in close_selectors:
                if await page.is_visible(selector):
                    print(f"Login modal detected. Closing with {selector}...")
                    await page.click(selector)
                    await asyncio.sleep(1)
            
            # 3. Try clicking outside the modal (Backdrop)
            # Usually the top-left corner (10, 10) is safe if the modal is centered
            await page.mouse.click(10, 10)
            
        except Exception as e:
            print(f"Error handling modal: {e}")

        try:
            # Scroll to trigger load
            await page.evaluate("window.scrollTo(0, 500)")
            await asyncio.sleep(2)
            
            # Wait longer for results (15s - optimized)
            await page.wait_for_selector('a[href*="/video/"]', timeout=15000)
        except Exception as e:
            print(f"Main search timeout or error: {e}")
            # Do NOT return here, let it fall through to the fallback!
            
        elements = await page.query_selector_all('a[href*="/video/"]')
        video_links = []
        for el in elements:
            href = await el.get_attribute('href')
            if href and "/video/" in href:
                video_links.append(href)
                
        # Remove duplicates
        video_links = list(set(video_links))
        
        # --- FALLBACK: HASHTAG SEARCH ---
        if not video_links:
            print("Main search blocked. Trying Hashtag Page fallback...")
            try:
                # Construct hashtag URL (remove spaces)
                tag = keyword.replace(" ", "")
                tag_url = f"https://www.tiktok.com/tag/{tag}"
                print(f"Navigating to {tag_url}")
                
                await page.goto(tag_url)
                await asyncio.sleep(2)
                
                # Scroll a bit
                await page.evaluate("window.scrollTo(0, 500)")
                await asyncio.sleep(2)
                
                # Wait for video links
                try:
                    await page.wait_for_selector('a[href*="/video/"]', timeout=15000)
                except: pass
                
                # Extract again
                elements = await page.query_selector_all('a[href*="/video/"]')
                for el in elements:
                    href = await el.get_attribute('href')
                    if href and "/video/" in href:
                        video_links.append(href)
                        
                video_links = list(set(video_links))
                
            except Exception as e:
                print(f"Hashtag fallback failed: {e}")

        if not video_links:
            print("No videos found after fallback, taking debug screenshot...")
            await page.screenshot(path="search_debug.png")
            
        await page.close()
        return video_links[:limit]

    async def scrape_video_details(self, url):
        import random
        page = await self.context.new_page()
        print(f"Scraping {url}")
        
        data = {'url': url}
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                await page.goto(url)
                # Random delay to mimic human
                await asyncio.sleep(random.uniform(2, 5))
                
                # Handle "Log in to search" Modal - Aggressive Strategy (Same as search)
                try:
                    await asyncio.sleep(2)
                    # 1. Try Escape Key
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(1)
                    
                    # 2. Try clicking the "X" button
                    close_selectors = [
                        '[data-e2e="modal-close-inner-button"]',
                        '[data-e2e="modal-close"]',
                        'button[aria-label="Close"]',
                        'div[role="dialog"] button',
                        'svg[class*="StyledCloseIcon"]',
                        '#login-modal-close'
                    ]
                    for selector in close_selectors:
                        if await page.is_visible(selector):
                            await page.click(selector)
                            await asyncio.sleep(1)
                    
                    # 3. Try clicking outside
                    await page.mouse.click(10, 10)
                except: pass

                # Wait for load
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except: pass

                # Capture Screenshot for UI
                import base64
                screenshot_bytes = await page.screenshot()
                data['screenshot_base64'] = base64.b64encode(screenshot_bytes).decode('utf-8')

                # Try JSON extraction first
                import json
                import re
                content = await page.content()
                
                # Check if we got blocked (simple check)
                if "verify" in (await page.title()).lower():
                    print(f"Captcha/Verify detected in title: {await page.title()}")
                    await asyncio.sleep(5)
                    continue # Retry
                
                break # Success
            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    await page.close()
                    return None

        # ... (JSON Extraction Block - keeping existing logic but ensuring variables exist) ...
        # I will rewrite the JSON block to be safe
        
        try:
            content = await page.content()
            sigi_match = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', content)
            if sigi_match:
                sigi_data = json.loads(sigi_match.group(1))
                item_module = sigi_data.get('ItemModule', {})
                for key, item in item_module.items():
                    data['description'] = item.get('desc', data.get('description', ''))
                    data['author'] = item.get('author', data.get('author', ''))
                    stats = item.get('stats', {})
                    data['stats'] = {
                        'views': stats.get('playCount', 0),
                        'likes': stats.get('diggCount', 0),
                        'shares': stats.get('shareCount', 0),
                        'comments': stats.get('commentCount', 0)
                    }
                    video_info = item.get('video', {})
                    data['thumbnail'] = video_info.get('cover', '')
                    challenges = item.get('challenges', [])
                    data['hashtags'] = [c.get('title') for c in challenges]
                    break
            
            # Universal Data Fallback
            if 'description' not in data:
                univ_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', content)
                if univ_match:
                    univ_data = json.loads(univ_match.group(1))
                    default_scope = univ_data.get('__DEFAULT_SCOPE__', {})
                    webapp_video_detail = default_scope.get('webapp.video-detail', {})
                    item_info = webapp_video_detail.get('itemInfo', {}).get('itemStruct', {})
                    if item_info:
                        data['description'] = item_info.get('desc', data.get('description', ''))
                        data['author'] = item_info.get('author', {}).get('nickname', data.get('author', ''))
                        stats = item_info.get('stats', {})
                        data['stats'] = {
                            'views': stats.get('playCount', 0),
                            'likes': stats.get('diggCount', 0),
                            'shares': stats.get('shareCount', 0),
                            'comments': stats.get('commentCount', 0)
                        }
                        video_info = item_info.get('video', {})
                        data['thumbnail'] = video_info.get('cover', '')
                        challenges = item_info.get('challenges', [])
                        data['hashtags'] = [c.get('title') for c in challenges]

        except Exception as e:
            print(f"JSON extraction failed: {e}")

        # --- DOM/META FALLBACKS ---
        
        # Description
        if not data.get('description'):
            try:
                # 1. Try Meta Description (Very reliable)
                meta_desc = await page.query_selector('meta[name="description"]')
                if meta_desc:
                    content = await meta_desc.get_attribute('content')
                    # Clean up "Watch [Author] video..." prefix if present
                    data['description'] = content.split(' on TikTok')[0]
                
                # 2. Try Page Title
                if not data.get('description'):
                    title = await page.title()
                    # Title format: "Description | Author | TikTok" or similar
                    if "|" in title:
                        data['description'] = title.split('|')[0].strip()
                    else:
                        data['description'] = title

                # 3. Try DOM
                if not data.get('description'):
                    desc_el = await page.query_selector('[data-e2e="browse-video-desc"]')
                    if not desc_el: desc_el = await page.query_selector('h1')
                    data['description'] = await desc_el.inner_text() if desc_el else "No description found"
            except: data['description'] = ""

        # Thumbnail
        if not data.get('thumbnail'):
            try:
                # Try OpenGraph Image
                og_img = await page.query_selector('meta[property="og:image"]')
                if og_img:
                    data['thumbnail'] = await og_img.get_attribute('content')
            except: pass

        # Author
        if not data.get('author'):
            try:
                author_el = await page.query_selector('[data-e2e="browse-user-detail"] h3')
                if not author_el: author_el = await page.query_selector('span[data-e2e="browse-username"]')
                data['author'] = await author_el.inner_text() if author_el else "Unknown Author"
            except: data['author'] = ""

        # Stats (DOM Fallback)
        if 'stats' not in data:
            data['stats'] = {}
            try:
                likes_el = await page.query_selector('[data-e2e="like-count"]')
                data['stats']['likes'] = await likes_el.inner_text() if likes_el else "N/A"
                
                comments_el = await page.query_selector('[data-e2e="comment-count"]')
                data['stats']['comments'] = await comments_el.inner_text() if comments_el else "N/A"
                
                # Views often not shown on video page detail, only on feed.
                data['stats']['views'] = "N/A" 
            except: pass

        # Hashtags (DOM Fallback)
        if 'hashtags' not in data:
            try:
                # Hashtags are usually links in the description
                tag_els = await page.query_selector_all('a[href*="/tag/"]')
                data['hashtags'] = [await t.inner_text() for t in tag_els]
            except: data['hashtags'] = []

        # Comments (Scroll and scrape)
        await page.evaluate("window.scrollTo(0, 500)")
        await asyncio.sleep(3)
        
        comments = []
        comment_elements = await page.query_selector_all('[data-e2e="comment-level-1"]')
        if not comment_elements:
             comment_elements = await page.query_selector_all('div[class*="DivCommentContentContainer"]')

        for el in comment_elements[:20]: 
            text_el = await el.query_selector('p[data-e2e="comment-level-1__content"]')
            if not text_el: text_el = await el.query_selector('p')
            if text_el:
                text = await text_el.inner_text()
                if "trouble playing" not in text:
                    comments.append(text)
        
        if not comments:
             ps = await page.query_selector_all('p')
             for p in ps[:20]:
                 text = await p.inner_text()
                 if len(text) > 5 and len(text) < 200 and "trouble playing" not in text:
                     comments.append(text)

        data['comments'] = comments

        await page.close()
        return data


async def scrape_and_save(keyword: str, max_videos: int, db_client: SupabaseClient, scraper: TikTokScraper = None, headless: bool = True) -> Dict[str, Any]:
    """
    Scrape videos by keyword and save to database

    Args:
        keyword: Search keyword
        max_videos: Maximum number of videos to scrape
        db_client: Database client instance
        scraper: Optional existing scraper instance

    Returns:
        Dictionary with scraping results
    """
    close_scraper = False
    if not scraper:
        scraper = TikTokScraper(headless=headless)
        await scraper.start()
        close_scraper = True

    try:
        logger.info(f"Searching for '{keyword}' (max {max_videos} videos)")

        # Search for videos
        video_urls = await scraper.search_videos(keyword, limit=max_videos)

        if not video_urls:
            logger.warning(f"No videos found for keyword: {keyword}")
            return {
                "keyword": keyword,
                "found": 0,
                "scraped": 0,
                "skipped": 0,
                "video_ids": []
            }

        scraped_count = 0
        skipped_count = 0
        video_ids = []

        for url in video_urls:
            # Extract TikTok ID
            tiktok_id = extract_tiktok_id(url)
            if not tiktok_id:
                logger.warning(f"Could not extract ID from URL: {url}")
                continue

            # Scrape video details
            logger.info(f"Scraping video {tiktok_id}...")
            video_data = await scraper.scrape_video_details(url)

            if not video_data:
                logger.error(f"Failed to scrape video: {url}")
                continue

            # Log captured details for User visibility
            v_auth = video_data.get("author", "Unknown")
            v_desc = video_data.get("description", "")[:50].replace("\n", " ") + "..."
            v_stats = video_data.get("stats", {})
            logger.info(f"   -> Found: @{v_auth} | {v_desc}")
            logger.info(f"      Stats: {v_stats.get('views', 'N/A')} views, {v_stats.get('likes', 'N/A')} likes, {v_stats.get('comments', 'N/A')} comments")

            # Prepare data for database
            video_record = {
                "tiktok_id": tiktok_id,
                "url": url,
                "author_username": video_data.get("author", "Unknown"),
                "description": video_data.get("description", ""),
                "views_count": int(video_data.get("stats", {}).get("views", 0)) if isinstance(video_data.get("stats", {}).get("views"), int) else 0,
                "likes_count": int(video_data.get("stats", {}).get("likes", 0)) if isinstance(video_data.get("stats", {}).get("likes"), int) else 0,
                "shares_count": int(video_data.get("stats", {}).get("shares", 0)) if isinstance(video_data.get("stats", {}).get("shares"), int) else 0,
                "comments_count": int(video_data.get("stats", {}).get("comments", 0)) if isinstance(video_data.get("stats", {}).get("comments"), int) else 0,
                "hashtags": video_data.get("hashtags", []),
                "screenshot_base64": video_data.get("screenshot_base64"),
                "search_keyword": keyword
            }

            # Check if already exists in database
            existing = db_client.get_video_by_tiktok_id(tiktok_id)
            
            if existing:
                # Update existing video
                success = db_client.update_video(video_record)
                if success:
                    logger.info(f"Updated video {tiktok_id} with new stats")
                    scraped_count += 1
                    video_ids.append(existing["id"])
                else:
                    logger.error(f"Failed to update video {tiktok_id}")
            else:
                # Insert new video
                video_id = db_client.insert_video(video_record)

                if video_id:
                    logger.info(f"Saved video {tiktok_id} to database with ID {video_id}")
                    scraped_count += 1
                    video_ids.append(video_id)

                    # Insert comments
                    comments = video_data.get("comments", [])
                    if comments:
                        comment_records = [
                            {
                                "author_username": "Unknown",
                                "comment_text": comment,
                                "likes_count": 0
                            }
                            for comment in comments
                        ]
                        db_client.insert_comments(video_id, comment_records)
                else:
                    logger.error(f"Failed to save video {tiktok_id} to database")

        return {
            "keyword": keyword,
            "found": len(video_urls),
            "scraped": scraped_count,
            "skipped": skipped_count,
            "video_ids": video_ids
        }

    finally:
        if close_scraper:
            await scraper.stop()

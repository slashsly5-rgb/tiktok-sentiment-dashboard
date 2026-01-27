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
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
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

                except Exception as e:
                    logger.error(f"Failed to load cookies: {e}")

        # --- STEALTH UPGRADE ---
        # "Playwright Stealth" injects multiple scripts to hide Headless detection
        # (WebGL, Permissions, Plugins, Languages, Console debugs, etc.)
        try:
            from playwright_stealth import stealth_async
            page_temp = await self.context.new_page()
            await stealth_async(page_temp)
            await page_temp.close()
            logger.info("🛡️ Stealth Mode Initiated: playwright-stealth active.")
        except ImportError:
            logger.warning("Stealth module not found. Running with basic masking.")
            # Fallback handling
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
        except Exception as e:
            logger.error(f"Stealth injection failed: {e}")

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
        
        # Apply Stealth to this page explicitly
        try:
             from playwright_stealth import stealth_async
             await stealth_async(page)
        except: pass

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
            
        # Try to find video containers with stats for "Most Engaged" sorting
        # Search Item Selector: [data-e2e="search_top_item"] or [data-e2e="search_item"]
        try:
             # Wait for at least one search item
             await page.wait_for_selector('[data-e2e="search_card"]', state="attached", timeout=5000)
        except: pass

        # Get all cards
        # We try broad selection then filter
        # Common selectors for view count: .video-count, [data-e2e="video-views"]
        cards = await page.query_selector_all('[data-e2e="search_card"]')
        
        candidates = []
        
        for card in cards:
            try:
                # 1. Get Link
                link_el = await card.query_selector('a[href*="/video/"]')
                if not link_el: continue
                href = await link_el.get_attribute('href')
                
                # 2. Get View Count
                views = 0
                # Try multiple selectors for views
                view_el = await card.query_selector('[data-e2e="video-views"]')
                if not view_el: view_el = await card.query_selector('.video-count')
                
                if view_el:
                    text = await view_el.inner_text() 
                    # Parse "1.2M", "500K", "100"
                    text = text.upper().replace("VIEWS", "").strip()
                    if "M" in text:
                        views = float(text.replace("M", "")) * 1_000_000
                    elif "K" in text:
                        views = float(text.replace("K", "")) * 1_000
                    elif "B" in text:
                        views = float(text.replace("B", "")) * 1_000_000_000
                    else:
                        try: views = float(text)
                        except: views = 0
                
                candidates.append({"url": href, "views": int(views)})
            except: continue
        
        # If we found rich cards, sort them!
        if candidates:
            logger.info(f"Found {len(candidates)} videos with stats. Sorting by engagement...")
            # Sort DESC by views
            candidates.sort(key=lambda x: x["views"], reverse=True)
            video_links = [c["url"] for c in candidates]
        else:
            # Fallback to old simple link extraction if cards failed 
            logger.warning("Could not parse stats. Falling back to simple link extraction.")
            elements = await page.query_selector_all('a[href*="/video/"]')
            video_links = []
            for el in elements:
                href = await el.get_attribute('href')
                if href and "/video/" in href:
                    video_links.append(href)

        # Remove duplicates
        video_links = list(set(video_links))
        
        # Re-Sort duplicates removal might have shuffled, but since we are taking top K, set() is risky.
        # Actually, let's keep list order if candidates existed
        if candidates:
             # Re-deduplicate preserving order
             seen = set()
             deduped_links = []
             for l in video_links:
                 if l not in seen:
                     deduped_links.append(l)
                     seen.add(l)
             video_links = deduped_links
        
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
        data = {'url': url}
        max_retries = 1 # Optimized: Faster fail
        
        for attempt in range(max_retries + 1):
            try:
                await page.goto(url)
                # Optimized: Shorter delay
                await asyncio.sleep(random.uniform(1, 2))
                
                # Handle "Log in to search" Modal - Aggressive Strategy (Same as search)
                try:
                    await asyncio.sleep(1) # Optimized
                    # 1. Try Escape Key
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(0.5) 
                    
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
                            await asyncio.sleep(0.5)
                    
                    # 3. Try clicking outside
                    await page.mouse.click(10, 10)
                except: pass

                # Wait for load
                try:
                    await page.wait_for_load_state('networkidle', timeout=5000) # Optimized: 5s max
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

        # Stats (DOM Fallback)
        # If JSON failed to find stats, scrape them from UI
        if 'stats' not in data or data['stats'].get('likes', 0) == 0:
            dom_stats = {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0}
            try:
                # Likes
                like_el = await page.query_selector('[data-e2e="like-count"]')
                if like_el: dom_stats['likes'] = self._parse_stat(await like_el.inner_text())
                
                # Comments
                comm_el = await page.query_selector('[data-e2e="comment-count"]')
                if comm_el: dom_stats['comments'] = self._parse_stat(await comm_el.inner_text())
                
                # Shares 
                share_el = await page.query_selector('[data-e2e="share-count"]')
                if share_el: dom_stats['shares'] = self._parse_stat(await share_el.inner_text())
                
                if 'stats' not in data: data['stats'] = {}
                data['stats'].update(dom_stats)
            except Exception as e:
                print(f"DOM stats extraction failed: {e}")

    def _parse_stat(self, text):
        """Helper to parse '1.2M', '10K', '100'"""
        if not text: return 0
        text = str(text) # Safety
        text = text.upper().replace('K', '000').replace('M', '000000').replace('B', '000000000').replace('.', '')
        try:
            val = text.replace(',', '')
            if 'K' in text: val = float(text.replace('K', '')) * 1000
            elif 'M' in text: val = float(text.replace('M', '')) * 1000000
            elif 'B' in text: val = float(text.replace('B', '')) * 1000000000
            return int(float(val))
        except: return 0

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

        if 'hashtags' not in data:
            try:
                tag_els = await page.query_selector_all('a[href*="/tag/"]')
                data['hashtags'] = [await t.inner_text() for t in tag_els]
            except: data['hashtags'] = []

        # Comments (Scroll and scrape)
        await page.evaluate("window.scrollTo(0, 500)")
        await asyncio.sleep(3)
        
        comments = []
        try:
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
        except: pass
        
        data['comments'] = comments

        await page.close()
        return data

async def _save_video_to_db(db_client, video_record, comments):
    """Helper to save video and comments to DB"""
    try:
        tiktok_id = video_record["tiktok_id"]
        existing = db_client.get_video_by_tiktok_id(tiktok_id)
        if existing:
            success = db_client.update_video(video_record)
            return existing["id"] if success else None
        else:
            video_id = db_client.insert_video(video_record)
            if video_id and comments:
                 comment_records = [{"author_username": "Unknown", "comment_text": c, "likes_count": 0} for c in comments]
                 db_client.insert_comments(video_id, comment_records)
            return video_id
    except Exception as e:
        logger.error(f"DB Save Error: {e}")
        return None

async def scrape_direct_urls(urls: List[str], db_client: SupabaseClient, scraper: TikTokScraper = None, headless: bool = True) -> Dict[str, Any]:
    """Scrape specific video URLs directly"""
    close_scraper = False
    if not scraper:
        scraper = TikTokScraper(headless=headless)
        await scraper.start()
        close_scraper = True

    scraped_count = 0
    video_ids = []
    
    try:
        for url in urls:
            logger.info(f"Direct Scraping: {url}")
            tiktok_id = extract_tiktok_id(url)
            if not tiktok_id:
                logger.warning(f"Invalid TikTok URL: {url}")
                continue
                
            video_data = await scraper.scrape_video_details(url)
            if video_data:
                # Prepare record
                video_record = {
                    "tiktok_id": tiktok_id,
                    "url": url,
                    "author_username": video_data.get("author", "Unknown"),
                    "description": video_data.get("description", ""),
                    "views_count": int(video_data.get("stats", {}).get("views", 0)),
                    "likes_count": int(video_data.get("stats", {}).get("likes", 0)),
                    "shares_count": int(video_data.get("stats", {}).get("shares", 0)),
                    "comments_count": int(video_data.get("stats", {}).get("comments", 0)),
                    "hashtags": video_data.get("hashtags", []),
                    "screenshot_base64": video_data.get("screenshot_base64"),
                    "search_keyword": "Direct Link" # Special keyword
                }
                
                vid_id = await _save_video_to_db(db_client, video_record, video_data.get("comments", []))
                if vid_id:
                    scraped_count += 1
                    video_ids.append(vid_id)
                    logger.info(f"✅ Saved: {tiktok_id}")
            
    finally:
        if close_scraper:
            await scraper.stop()
            
    return {
        "keyword": "Direct Link",
        "found": len(urls),
        "scraped": scraped_count,
        "skipped": len(urls) - scraped_count,
        "video_ids": video_ids
    }

async def scrape_and_save(keyword: str, max_videos: int, db_client: SupabaseClient, scraper: TikTokScraper = None, headless: bool = True) -> Dict[str, Any]:
    """Scrape videos by keyword and save to database"""
    close_scraper = False
    if not scraper:
        scraper = TikTokScraper(headless=headless)
        await scraper.start()
        close_scraper = True

    try:
        logger.info(f"Searching for '{keyword}' (max {max_videos} videos)")

        # Search for videos
        video_urls = await scraper.search_videos(keyword, limit=max_videos)
        
        # Parallel Processing with Semaphore (Max 3 concurrent tabs to save memory)
        sem = asyncio.Semaphore(3)

        async def process_video(url):
            async with sem:
                tiktok_id = extract_tiktok_id(url)
                if not tiktok_id: return None

                logger.info(f"Scraping video {tiktok_id}...")
                video_data = await scraper.scrape_video_details(url)
                if not video_data: return None

                # Prepare record
                video_record = {
                    "tiktok_id": tiktok_id,
                    "url": url,
                    "author_username": video_data.get("author", "Unknown"),
                    "description": video_data.get("description", ""),
                     "views_count": int(video_data.get("stats", {}).get("views", 0)),
                    "likes_count": int(video_data.get("stats", {}).get("likes", 0)),
                    "shares_count": int(video_data.get("stats", {}).get("shares", 0)),
                    "comments_count": int(video_data.get("stats", {}).get("comments", 0)),
                    "hashtags": video_data.get("hashtags", []),
                    "screenshot_base64": video_data.get("screenshot_base64"),
                    "search_keyword": keyword
                }
                return (video_record, video_data.get("comments", []))

        # Run tasks
        logger.info(f"Parallel scraping started for {len(video_urls)} videos...")
        tasks = [process_video(url) for url in video_urls]
        results = await asyncio.gather(*tasks)
        
        scraped_count = 0
        video_ids = []
        
        # Save to DB
        for res in results:
            if not res: continue
            video_record, comments = res
            vid_id = await _save_video_to_db(db_client, video_record, comments)
            if vid_id:
                scraped_count += 1
                video_ids.append(vid_id)

        return {
            "keyword": keyword,
            "found": len(video_urls),
            "scraped": scraped_count,
            "skipped": len(video_urls) - scraped_count,
            "video_ids": video_ids
        }

    finally:
        if close_scraper:
            await scraper.stop()

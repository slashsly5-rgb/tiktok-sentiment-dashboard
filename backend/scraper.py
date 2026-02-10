import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import re
import os
import json
import httpx
from typing import Optional, List, Dict, Any
from database import SupabaseClient
import logging

# Configure logging
# logging.basicConfig(level=logging.INFO) # REMOVED to avoid conflict
logger = logging.getLogger(__name__)

# Shared HTTP headers that mimic a real browser (used for non-Playwright requests)
_HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}


def _extract_from_item(item):
    """Helper to extract data from a TikTok item struct (JSON embedded in page)"""
    extracted = {}
    extracted['description'] = item.get('desc', '')
    # Author can be string or dict
    author_val = item.get('author', '')
    if isinstance(author_val, dict):
        extracted['author'] = author_val.get('nickname', author_val.get('uniqueId', ''))
    else:
        extracted['author'] = str(author_val)
    stats = item.get('stats', {})
    extracted['stats'] = {
        'views': stats.get('playCount', 0) or stats.get('viewCount', 0) or stats.get('views', 0),
        'likes': stats.get('diggCount', 0) or stats.get('likeCount', 0) or stats.get('likes', 0),
        'shares': stats.get('shareCount', 0) or stats.get('shares', 0),
        'comments': stats.get('commentCount', 0) or stats.get('comments', 0)
    }
    video_info = item.get('video', {})
    extracted['thumbnail'] = video_info.get('cover', video_info.get('dynamicCover', ''))
    challenges = item.get('challenges', [])
    extracted['hashtags'] = [c.get('title') for c in challenges if isinstance(c, dict)]
    return extracted


def _extract_json_from_html(html_content: str) -> Optional[dict]:
    """
    Extract video data from TikTok HTML without a browser.
    Tries all known JSON embedding strategies.
    Returns extracted data dict or None.
    """
    data = {}
    json_extracted = False

    # Strategy 1: SIGI_STATE (legacy)
    sigi_match = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', html_content, re.DOTALL)
    if sigi_match:
        try:
            sigi_data = json.loads(sigi_match.group(1))
            item_module = sigi_data.get('ItemModule', {})
            for key, item in item_module.items():
                extracted = _extract_from_item(item)
                data.update(extracted)
                json_extracted = True
                break
        except Exception as e:
            logger.warning(f"SIGI_STATE parse failed: {e}")

    # Strategy 2: __UNIVERSAL_DATA_FOR_REHYDRATION__ (current primary)
    if not json_extracted:
        univ_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', html_content, re.DOTALL)
        if univ_match:
            try:
                univ_data = json.loads(univ_match.group(1))
                default_scope = univ_data.get('__DEFAULT_SCOPE__', {})

                item_info = None
                # Path A
                vd = default_scope.get('webapp.video-detail', {})
                item_info = vd.get('itemInfo', {}).get('itemStruct', None)
                # Path B
                if not item_info:
                    item_info = vd.get('itemStruct', None)
                # Path C
                if not item_info:
                    vd2 = default_scope.get('webapp.video.detail', {})
                    item_info = vd2.get('itemInfo', {}).get('itemStruct', None)
                    if not item_info:
                        item_info = vd2.get('itemStruct', None)

                if item_info:
                    extracted = _extract_from_item(item_info)
                    data.update(extracted)
                    json_extracted = True
            except Exception as e:
                logger.warning(f"UNIVERSAL_DATA parse failed: {e}")

    # Strategy 3: __NEXT_DATA__
    if not json_extracted:
        next_match = re.search(r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>', html_content, re.DOTALL)
        if next_match:
            try:
                next_data = json.loads(next_match.group(1))
                props = next_data.get('props', {}).get('pageProps', {})
                item_info = props.get('itemInfo', {}).get('itemStruct', None)
                if not item_info:
                    item_info = props.get('videoData', None)
                if item_info:
                    extracted = _extract_from_item(item_info)
                    data.update(extracted)
                    json_extracted = True
            except Exception as e:
                logger.warning(f"NEXT_DATA parse failed: {e}")

    # Strategy 4: JSON-LD schema
    if not json_extracted:
        try:
            ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html_content, re.DOTALL)
            for ld_str in ld_matches:
                ld_data = json.loads(ld_str)
                if isinstance(ld_data, dict) and ld_data.get('@type') in ('VideoObject', 'SocialMediaPosting'):
                    interaction_stats = ld_data.get('interactionStatistic', [])
                    if isinstance(interaction_stats, list):
                        stats = {}
                        for stat in interaction_stats:
                            stat_type = stat.get('interactionType', {})
                            type_name = stat_type if isinstance(stat_type, str) else stat_type.get('@type', '')
                            count = int(stat.get('userInteractionCount', 0))
                            if 'Watch' in type_name or 'View' in type_name:
                                stats['views'] = count
                            elif 'Like' in type_name:
                                stats['likes'] = count
                            elif 'Comment' in type_name:
                                stats['comments'] = count
                            elif 'Share' in type_name:
                                stats['shares'] = count
                        if stats.get('views', 0) > 0 or stats.get('likes', 0) > 0:
                            data['stats'] = stats
                            data.setdefault('description', ld_data.get('description', ''))
                            data.setdefault('author', ld_data.get('creator', ''))
                            data.setdefault('thumbnail', ld_data.get('thumbnailUrl', ''))
                            json_extracted = True
                            break
        except Exception as e:
            logger.warning(f"JSON-LD parse failed: {e}")

    # Strategy 5: Meta tag fallback for description/stats from text
    if not json_extracted or not data.get('description'):
        try:
            meta_match = re.search(r'<meta\s+name="description"\s+content="(.*?)"', html_content)
            if meta_match:
                meta_text = meta_match.group(1)
                if not data.get('description'):
                    data['description'] = meta_text.split(' on TikTok')[0] if ' on TikTok' in meta_text else meta_text

                # Parse stats from meta: "1.9M Likes, 12.7K Comments"
                if 'stats' not in data:
                    data['stats'] = {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0}
                flags = re.IGNORECASE
                if data['stats'].get('likes', 0) == 0:
                    m = re.search(r'([\d\.]+[KMB]?)\s+Likes?', meta_text, flags)
                    if m: data['stats']['likes'] = _parse_stat_static(m.group(1))
                if data['stats'].get('comments', 0) == 0:
                    m = re.search(r'([\d\.]+[KMB]?)\s+Comments?', meta_text, flags)
                    if m: data['stats']['comments'] = _parse_stat_static(m.group(1))
                if data['stats'].get('views', 0) == 0:
                    m = re.search(r'([\d\.]+[KMB]?)\s+Views?', meta_text, flags)
                    if m: data['stats']['views'] = _parse_stat_static(m.group(1))
        except Exception as e:
            logger.warning(f"Meta tag fallback failed: {e}")

    # Author fallback from meta
    if not data.get('author'):
        try:
            # og:title often has author info
            og_match = re.search(r'<meta\s+property="og:title"\s+content="(.*?)"', html_content)
            if og_match:
                og_title = og_match.group(1)
                if '(@' in og_title:
                    author_match = re.search(r'\(@(\w+)\)', og_title)
                    if author_match:
                        data['author'] = author_match.group(1)
        except:
            pass

    # Thumbnail fallback
    if not data.get('thumbnail'):
        try:
            og_img = re.search(r'<meta\s+property="og:image"\s+content="(.*?)"', html_content)
            if og_img:
                data['thumbnail'] = og_img.group(1)
        except:
            pass

    # Hashtags from description
    if not data.get('hashtags') and data.get('description'):
        data['hashtags'] = re.findall(r"#([^\s\.,!?:;\"'()]+)", data['description'])

    # Ensure stats has all keys
    if 'stats' not in data:
        data['stats'] = {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0}
    for k in ['views', 'likes', 'comments', 'shares']:
        if k not in data['stats']:
            data['stats'][k] = 0

    if json_extracted:
        return data
    # Even if JSON extraction failed, return what we got from meta if we have description
    if data.get('description') or data.get('stats', {}).get('likes', 0) > 0:
        return data
    return None


def _parse_stat_static(text):
    """Static version of _parse_stat for use outside class"""
    if not text: return 0
    text = str(text).strip()
    text = re.sub(r'\s*(views?|likes?|comments?|shares?)\s*$', '', text, flags=re.IGNORECASE)
    text = text.upper().replace(',', '').replace(' ', '').strip()
    if not text: return 0
    try:
        multiplier = 1
        if text.endswith('K'):
            multiplier = 1000
            text = text[:-1]
        elif text.endswith('M'):
            multiplier = 1000000
            text = text[:-1]
        elif text.endswith('B'):
            multiplier = 1000000000
            text = text[:-1]
        return int(float(text) * multiplier)
    except:
        return 0


async def scrape_video_via_http(url: str) -> Optional[dict]:
    """
    Scrape a TikTok video using HTTP requests only (no browser).
    This avoids CAPTCHA/bot detection entirely.
    Returns video data dict or None.
    """
    logger.info(f"HTTP Scraping: {url}")
    data = {'url': url}

    try:
        async with httpx.AsyncClient(
            headers=_HTTP_HEADERS,
            follow_redirects=True,
            timeout=15.0
        ) as client:
            # Resolve short URLs via HTTP redirect
            if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url or '/t/' in url:
                try:
                    resp = await client.head(url, follow_redirects=True)
                    resolved = str(resp.url)
                    if '/video/' in resolved or '/photo/' in resolved:
                        logger.info(f"HTTP resolved short URL: {url} -> {resolved}")
                        url = resolved
                        data['url'] = url
                except:
                    pass

            # Fetch the page HTML
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code} for {url}")
                return None

            html = resp.text

            # Check for CAPTCHA/block page
            if 'verify' in html[:2000].lower() and 'tiktok' in html[:2000].lower() and len(html) < 5000:
                logger.warning(f"HTTP request returned verify/CAPTCHA page for {url}")
                # Still try to extract - sometimes the JSON is there even with CAPTCHA overlay
                pass

            # Extract data from HTML
            extracted = _extract_json_from_html(html)
            if extracted:
                data.update(extracted)
                logger.info(f"HTTP extraction successful. Views: {data.get('stats', {}).get('views', 'N/A')}, "
                           f"Likes: {data.get('stats', {}).get('likes', 'N/A')}")
                return data

            logger.warning(f"HTTP extraction found no data in HTML for {url}")
            return None

    except Exception as e:
        logger.error(f"HTTP scrape failed for {url}: {e}")
        return None


async def get_oembed_data(url: str) -> Optional[dict]:
    """
    Get basic video metadata from TikTok's public oEmbed API.
    This is an official API - never blocked.
    Returns dict with title, author, thumbnail or None.
    """
    oembed_url = f"https://www.tiktok.com/oembed?url={urllib.parse.quote(url, safe='')}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(oembed_url)
            if resp.status_code == 200:
                oembed = resp.json()
                return {
                    'description': oembed.get('title', ''),
                    'author': oembed.get('author_name', ''),
                    'thumbnail': oembed.get('thumbnail_url', ''),
                    'author_url': oembed.get('author_url', ''),
                }
    except Exception as e:
        logger.warning(f"oEmbed API failed for {url}: {e}")
    return None


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
        # Standard /video/ URL
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        # Photo/slide URL format
        match = re.search(r'/photo/(\d+)', url)
        if match:
            return match.group(1)
        # Bare numeric ID at end of URL (e.g. after redirect)
        match = re.search(r'/(\d{15,})(?:\?|$)', url)
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
            args=args,
            ignore_default_args=["--enable-automation"]
        )
        # Load auth state (preferred) or cookies
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        auth_file = os.path.join(root_dir, "auth.json")
        cookie_file = os.path.join(root_dir, "cookies.json")
        
        if os.path.exists(auth_file):
            # Create context with storage state (Cookies + LocalStorage)
            self.context = await self.browser.new_context(
                storage_state=auth_file,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                locale='en-US',
                timezone_id='America/New_York'
            )
            logger.info(f"Loaded authentication from {auth_file}")
        else:
            # Fallback to standard context (and maybe cookies.json)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
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

        # --- STEALTH UPGRADE ---
        # Robust manual injection to mask automation signals
        await self.context.add_init_script("""
            // 1. Mask WebDriver
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            
            // 2. Mock Plugins (Chrome obviously has plugins)
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            
            // 3. Mock Chrome Runtime
            window.chrome = { runtime: {} };
            
            // 4. Reset Permissions Query
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: 'denied' }) :
                originalQuery(parameters)
            );
            
            // 5. WebGL vendor spoofing (Generic Intel/Google)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Google Inc. (Intel)';
                if (parameter === 37446) return 'ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0, or similar)';
                return getParameter(parameter);
            };
        """)
        
        try:
            from playwright_stealth import stealth_async
            page_temp = await self.context.new_page()
            await stealth_async(page_temp)
            await page_temp.close()
            logger.info("🛡️ Stealth Mode: playwright-stealth module active + Manual Overrides.")
        except ImportError:
            logger.info("🛡️ Stealth Mode: Manual Injection Active (Module not found).")
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

        encoded_keyword = urllib.parse.quote(keyword)
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
        # TikTok updates selectors frequently - try multiple variants
        search_card_selectors = [
            '[data-e2e="search_card"]',
            '[data-e2e="search-card"]',
            '[data-e2e="search_top-item"]',
            '[data-e2e="search-common-link"]',
            'div[class*="DivItemCardContainer"]',
            'div[class*="DivVideoCardContainer"]',
        ]

        cards = []
        for card_sel in search_card_selectors:
            try:
                await page.wait_for_selector(card_sel, state="attached", timeout=3000)
                cards = await page.query_selector_all(card_sel)
                if cards:
                    logger.info(f"Found {len(cards)} cards with selector: {card_sel}")
                    break
            except:
                continue
        
        candidates = []
        
        for card in cards:
            try:
                # 1. Get Link
                link_el = await card.query_selector('a[href*="/video/"]')
                if not link_el: continue
                href = await link_el.get_attribute('href')
                
                # 2. Get View Count
                views = 0
                # Try multiple selectors for views (TikTok changes these frequently)
                view_selectors = [
                    '[data-e2e="video-views"]',
                    '.video-count',
                    'strong[data-e2e="video-views"]',
                    'span[class*="SpanOtherInfos"]',
                    'span[class*="VideoCount"]',
                    'div[class*="DivPlayCount"]',
                ]
                view_el = None
                for vs in view_selectors:
                    view_el = await card.query_selector(vs)
                    if view_el:
                        break

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

    async def _resolve_short_url(self, url):
        """Resolve short/redirect TikTok URLs (vm.tiktok.com, vt.tiktok.com) to full URLs"""
        if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url or '/t/' in url:
            try:
                page = await self.context.new_page()
                await page.goto(url, wait_until='domcontentloaded', timeout=10000)
                resolved = page.url
                await page.close()
                if '/video/' in resolved or '/photo/' in resolved:
                    logger.info(f"Resolved short URL: {url} -> {resolved}")
                    return resolved
            except Exception as e:
                logger.warning(f"Failed to resolve short URL {url}: {e}")
        return url

    async def scrape_video_details(self, url):
        """
        Scrape video details using a 3-tier strategy:
        1. HTTP request (fastest, no CAPTCHA)
        2. oEmbed API (official, never blocked, but limited data)
        3. Playwright browser (last resort, may hit CAPTCHA)
        """
        import random

        # ==============================================
        # TIER 1: HTTP-only scraping (no browser needed)
        # ==============================================
        http_data = await scrape_video_via_http(url)
        if http_data and http_data.get('stats', {}).get('likes', 0) > 0:
            logger.info(f"TIER 1 (HTTP) succeeded for {url}")
            # Ensure all required fields
            http_data.setdefault('comments', [])
            http_data.setdefault('author', 'Unknown')
            http_data.setdefault('hashtags', [])
            http_data.setdefault('screenshot_base64', None)
            return http_data

        # ==============================================
        # TIER 2: oEmbed API (always works, limited data)
        # ==============================================
        oembed_data = await get_oembed_data(url)

        # If HTTP got stats but no description, merge with oEmbed
        if http_data and oembed_data:
            if not http_data.get('description') and oembed_data.get('description'):
                http_data['description'] = oembed_data['description']
            if not http_data.get('author') or http_data.get('author') == 'Unknown':
                http_data['author'] = oembed_data.get('author', http_data.get('author', 'Unknown'))
            if not http_data.get('thumbnail') and oembed_data.get('thumbnail'):
                http_data['thumbnail'] = oembed_data['thumbnail']
            if http_data.get('description') or http_data.get('stats', {}).get('views', 0) > 0:
                logger.info(f"TIER 1+2 (HTTP+oEmbed merge) succeeded for {url}")
                http_data.setdefault('comments', [])
                http_data.setdefault('hashtags', [])
                http_data.setdefault('screenshot_base64', None)
                return http_data

        # ==============================================
        # TIER 3: Playwright browser (last resort)
        # ==============================================
        logger.info(f"TIER 3 (Playwright) for {url} - HTTP methods insufficient")

        # Resolve short URLs first
        url = await self._resolve_short_url(url)

        page = await self.context.new_page()
        print(f"Scraping via browser: {url}")

        data = {'url': url}

        # Merge any oEmbed data we already have
        if oembed_data:
            data['description'] = oembed_data.get('description', '')
            data['author'] = oembed_data.get('author', '')
            data['thumbnail'] = oembed_data.get('thumbnail', '')

        # Merge any HTTP data we already have
        if http_data:
            for k, v in http_data.items():
                if v and k != 'url':
                    data.setdefault(k, v)

        max_retries = 2

        for attempt in range(max_retries + 1):
            try:
                await page.goto(url)
                await asyncio.sleep(random.uniform(1, 2))

                # Handle login modal
                try:
                    await asyncio.sleep(1)
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(0.5)
                    close_selectors = [
                        '[data-e2e="modal-close-inner-button"]',
                        '[data-e2e="modal-close"]',
                        'button[aria-label="Close"]',
                        'div[role="dialog"] button',
                    ]
                    for selector in close_selectors:
                        if await page.is_visible(selector):
                            await page.click(selector)
                            await asyncio.sleep(0.5)
                    await page.mouse.click(10, 10)
                except: pass

                # Wait for load
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    try:
                        await page.wait_for_load_state('domcontentloaded', timeout=5000)
                    except: pass
                    await asyncio.sleep(2)

                # Screenshot
                import base64
                screenshot_bytes = await page.screenshot()
                data['screenshot_base64'] = base64.b64encode(screenshot_bytes).decode('utf-8')

                content = await page.content()

                # Check for CAPTCHA
                title = await page.title()
                if "verify" in title.lower():
                    print(f"Captcha detected: {title}")
                    await asyncio.sleep(3)
                    continue

                # Check for login wall redirect
                if "Make Your Day" in title or title.strip() == "TikTok" or "Log in" in title:
                    logger.warning(f"Login wall detected on attempt {attempt}")
                    if attempt < max_retries:
                        await asyncio.sleep(2)
                        continue
                    else:
                        # If we have data from HTTP/oEmbed, return that instead of None
                        if data.get('description') or data.get('stats', {}).get('likes', 0) > 0:
                            logger.info("Browser blocked but returning HTTP/oEmbed data")
                            data.setdefault('stats', {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0})
                            data.setdefault('comments', [])
                            data.setdefault('hashtags', [])
                            await page.close()
                            return data
                        await page.close()
                        return None

                # Try extracting from browser page HTML
                extracted = _extract_json_from_html(content)
                if extracted:
                    for k, v in extracted.items():
                        if v and (k not in data or not data[k]):
                            data[k] = v
                    # Merge stats carefully
                    if 'stats' in extracted:
                        data.setdefault('stats', {})
                        for sk, sv in extracted['stats'].items():
                            if sv and data['stats'].get(sk, 0) == 0:
                                data['stats'][sk] = sv

                break  # Success
            except Exception as e:
                print(f"Browser attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    # Return HTTP/oEmbed data if available
                    if data.get('description') or data.get('stats', {}).get('likes', 0) > 0:
                        data.setdefault('stats', {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0})
                        data.setdefault('comments', [])
                        data.setdefault('hashtags', [])
                        await page.close()
                        return data
                    await page.close()
                    return None

        # DOM stats fallback (only if browser loaded successfully)
        if 'stats' not in data:
            data['stats'] = {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0}
        for k in ['views', 'likes', 'comments', 'shares']:
            if k not in data['stats']: data['stats'][k] = 0

        try:
            try:
                await page.wait_for_selector('[data-e2e="like-count"]', state="visible", timeout=5000)
            except: pass

            stat_selectors = {
                'views': ['[data-e2e="video-views"]', '[data-e2e="browse-video-count"]'],
                'likes': ['[data-e2e="like-count"]', '[data-e2e="browse-like-count"]'],
                'comments': ['[data-e2e="comment-count"]', '[data-e2e="browse-comment-count"]'],
                'shares': ['[data-e2e="share-count"]', '[data-e2e="browse-share-count"]'],
            }
            for stat_key, selectors in stat_selectors.items():
                if data['stats'].get(stat_key, 0) == 0:
                    for sel in selectors:
                        el = await page.query_selector(sel)
                        if el:
                            val = self._parse_stat(await el.inner_text())
                            if val > 0:
                                data['stats'][stat_key] = val
                                break
        except Exception as e:
            logger.warning(f"DOM stats fallback failed: {e}")

        # Comment scraping via browser
        comments = []
        try:
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)

            container_selectors = [
                '[data-e2e="comment-level-1"]',
                '[data-e2e="comment-item"]',
                'div[class*="CommentItem"]',
            ]
            for sel in container_selectors:
                els = await page.query_selector_all(sel)
                if els:
                    for el in els[:25]:
                        text_el = await el.query_selector('p[data-e2e="comment-level-1__content"]')
                        if not text_el: text_el = await el.query_selector('p')
                        if text_el:
                            text = await text_el.inner_text()
                            if len(text) > 1 and "Reply" not in text:
                                comments.append(text)
                    break
        except Exception as e:
            logger.warning(f"Comment extraction failed: {e}")

        data['comments'] = comments

        if data['stats']['comments'] == 0 and len(comments) > 0:
            data['stats']['comments'] = len(comments)

        # Fill missing author
        if not data.get('author') or data.get('author') == 'Unknown':
            data['author'] = 'Unknown Author'

        data.setdefault('hashtags', [])
        if not data.get('hashtags') and data.get('description'):
            data['hashtags'] = re.findall(r"#([^\s\.,!?:;\"'()]+)", data['description'])

        print(f"Scraped Data: {data.get('stats')} | Comments: {len(comments)}")
        await page.close()
        return data

    def _parse_stat(self, text):
        """Helper to parse '1.2M', '10K', '100', '1,234', '1.2k views'"""
        if not text: return 0
        text = str(text).strip()
        # Remove common suffixes like "views", "likes", etc.
        text = re.sub(r'\s*(views?|likes?|comments?|shares?)\s*$', '', text, flags=re.IGNORECASE)
        text = text.upper().replace(',', '').replace(' ', '').strip()
        if not text: return 0
        try:
            multiplier = 1
            if text.endswith('K'):
                multiplier = 1000
                text = text[:-1]
            elif text.endswith('M'):
                multiplier = 1000000
                text = text[:-1]
            elif text.endswith('B'):
                multiplier = 1000000000
                text = text[:-1]

            return int(float(text) * multiplier)
        except:
            return 0

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
    """Scrape specific video URLs directly. Tries HTTP first, falls back to browser."""
    scraped_count = 0
    video_ids = []
    browser_needed_urls = []

    # PHASE 1: Try HTTP-only scraping for all URLs first (fast, no CAPTCHA)
    for url in urls:
        logger.info(f"Direct Scraping (HTTP first): {url}")
        tiktok_id = extract_tiktok_id(url)

        # Try HTTP
        video_data = await scrape_video_via_http(url)

        # Enrich with oEmbed
        if not video_data or not video_data.get('description'):
            oembed = await get_oembed_data(url)
            if oembed:
                if not video_data:
                    video_data = {'url': url, 'stats': {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0}}
                video_data.setdefault('description', oembed.get('description', ''))
                if not video_data.get('author') or video_data.get('author') == 'Unknown':
                    video_data['author'] = oembed.get('author', 'Unknown')
                video_data.setdefault('thumbnail', oembed.get('thumbnail', ''))

        if video_data and (video_data.get('stats', {}).get('likes', 0) > 0 or video_data.get('description')):
            # HTTP success
            resolved_url = video_data.get('url', url)
            if not tiktok_id:
                tiktok_id = extract_tiktok_id(resolved_url)
            if not tiktok_id:
                logger.warning(f"Could not extract TikTok ID from {resolved_url}. Skipping.")
                continue

            video_record = {
                "tiktok_id": tiktok_id,
                "url": resolved_url,
                "author_username": video_data.get("author", "Unknown"),
                "description": video_data.get("description", ""),
                "views_count": int(video_data.get("stats", {}).get("views", 0)),
                "likes_count": int(video_data.get("stats", {}).get("likes", 0)),
                "shares_count": int(video_data.get("stats", {}).get("shares", 0)),
                "comments_count": int(video_data.get("stats", {}).get("comments", 0)),
                "hashtags": video_data.get("hashtags", []),
                "screenshot_base64": video_data.get("screenshot_base64"),
                "search_keyword": "Direct Link"
            }

            vid_id = await _save_video_to_db(db_client, video_record, video_data.get("comments", []))
            if vid_id:
                scraped_count += 1
                video_ids.append(vid_id)
                logger.info(f"Saved (HTTP): {tiktok_id}")
        else:
            browser_needed_urls.append(url)

    # PHASE 2: Fall back to browser for URLs that HTTP couldn't handle
    if browser_needed_urls:
        logger.info(f"Falling back to browser for {len(browser_needed_urls)} URLs...")
        close_scraper = False
        if not scraper:
            scraper = TikTokScraper(headless=headless)
            await scraper.start()
            close_scraper = True

        try:
            for url in browser_needed_urls:
                tiktok_id = extract_tiktok_id(url)
                video_data = await scraper.scrape_video_details(url)
                if video_data:
                    resolved_url = video_data.get('url', url)
                    if not tiktok_id:
                        tiktok_id = extract_tiktok_id(resolved_url)
                    if not tiktok_id:
                        continue

                    video_record = {
                        "tiktok_id": tiktok_id,
                        "url": resolved_url,
                        "author_username": video_data.get("author", "Unknown"),
                        "description": video_data.get("description", ""),
                        "views_count": int(video_data.get("stats", {}).get("views", 0)),
                        "likes_count": int(video_data.get("stats", {}).get("likes", 0)),
                        "shares_count": int(video_data.get("stats", {}).get("shares", 0)),
                        "comments_count": int(video_data.get("stats", {}).get("comments", 0)),
                        "hashtags": video_data.get("hashtags", []),
                        "screenshot_base64": video_data.get("screenshot_base64"),
                        "search_keyword": "Direct Link"
                    }

                    vid_id = await _save_video_to_db(db_client, video_record, video_data.get("comments", []))
                    if vid_id:
                        scraped_count += 1
                        video_ids.append(vid_id)
                        logger.info(f"Saved (Browser): {tiktok_id}")
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
        
        # Parallel Processing with Semaphore
        # HTTP scraping can handle more concurrency than browser
        sem_http = asyncio.Semaphore(5)
        sem_browser = asyncio.Semaphore(3)

        async def process_video(url):
            tiktok_id = extract_tiktok_id(url)
            if not tiktok_id: return None

            # Try HTTP first (no browser needed)
            async with sem_http:
                logger.info(f"Scraping video {tiktok_id} (HTTP first)...")
                video_data = await scrape_video_via_http(url)

                # Enrich with oEmbed if needed
                if not video_data or not video_data.get('description'):
                    oembed = await get_oembed_data(url)
                    if oembed:
                        if not video_data:
                            video_data = {'url': url, 'stats': {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0}}
                        video_data.setdefault('description', oembed.get('description', ''))
                        if not video_data.get('author') or video_data.get('author') == 'Unknown':
                            video_data['author'] = oembed.get('author', 'Unknown')
                        video_data.setdefault('thumbnail', oembed.get('thumbnail', ''))

            # Fall back to browser if HTTP failed
            if not video_data or (video_data.get('stats', {}).get('likes', 0) == 0 and not video_data.get('description')):
                async with sem_browser:
                    logger.info(f"Falling back to browser for {tiktok_id}...")
                    video_data = await scraper.scrape_video_details(url)

            if not video_data: return None

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

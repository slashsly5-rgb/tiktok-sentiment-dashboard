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
        import random

        # Resolve short URLs first
        url = await self._resolve_short_url(url)

        page = await self.context.new_page()
        print(f"Scraping {url}")
        
        data = {'url': url}
        max_retries = 2  # Allow more retries for reliability
        
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

                # Wait for load - give TikTok's heavy JS time to render
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    # Fallback: wait for domcontentloaded at minimum
                    try:
                        await page.wait_for_load_state('domcontentloaded', timeout=5000)
                    except: pass
                    await asyncio.sleep(2)  # Extra buffer for JS rendering

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

            def _extract_from_item(item):
                """Helper to extract data from a TikTok item struct"""
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

            json_extracted = False

            # Strategy 1: SIGI_STATE (legacy but still works on some pages)
            sigi_match = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', content)
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
                univ_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', content)
                if univ_match:
                    try:
                        univ_data = json.loads(univ_match.group(1))
                        default_scope = univ_data.get('__DEFAULT_SCOPE__', {})

                        # Try multiple paths - TikTok changes these
                        item_info = None
                        # Path A: webapp.video-detail -> itemInfo -> itemStruct
                        vd = default_scope.get('webapp.video-detail', {})
                        item_info = vd.get('itemInfo', {}).get('itemStruct', None)
                        # Path B: webapp.video-detail -> itemStruct (flat)
                        if not item_info:
                            item_info = vd.get('itemStruct', None)
                        # Path C: webapp.video.detail (dot notation variant)
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

            # Strategy 3: __NEXT_DATA__ (newer SSR pages)
            if not json_extracted:
                next_match = re.search(r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>', content)
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

            # Strategy 4: Scan for any JSON-LD schema with video stats
            if not json_extracted:
                try:
                    ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content)
                    for ld_str in ld_matches:
                        ld_data = json.loads(ld_str)
                        if isinstance(ld_data, dict) and ld_data.get('@type') in ('VideoObject', 'SocialMediaPosting'):
                            interaction_stats = ld_data.get('interactionStatistic', [])
                            if isinstance(interaction_stats, list):
                                for stat in interaction_stats:
                                    stat_type = stat.get('interactionType', {})
                                    type_name = stat_type if isinstance(stat_type, str) else stat_type.get('@type', '')
                                    count = int(stat.get('userInteractionCount', 0))
                                    if 'Watch' in type_name or 'View' in type_name:
                                        if 'stats' not in data: data['stats'] = {}
                                        data['stats']['views'] = count
                                    elif 'Like' in type_name:
                                        if 'stats' not in data: data['stats'] = {}
                                        data['stats']['likes'] = count
                                    elif 'Comment' in type_name:
                                        if 'stats' not in data: data['stats'] = {}
                                        data['stats']['comments'] = count
                                    elif 'Share' in type_name:
                                        if 'stats' not in data: data['stats'] = {}
                                        data['stats']['shares'] = count
                            if data.get('stats', {}).get('views', 0) > 0:
                                data.setdefault('description', ld_data.get('description', ''))
                                data.setdefault('author', ld_data.get('creator', ''))
                                data.setdefault('thumbnail', ld_data.get('thumbnailUrl', ''))
                                json_extracted = True
                                break
                except Exception as e:
                    logger.warning(f"JSON-LD parse failed: {e}")

            if json_extracted:
                logger.info(f"JSON extraction successful. Views: {data.get('stats', {}).get('views', 'N/A')}")
            else:
                logger.warning("All JSON extraction strategies failed, falling back to DOM scraping")

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
                    # DETECT GENERIC PAGE (Login Wall / Home)
                    if "Make Your Day" in title or title.strip() == "TikTok" or "Log in" in title:
                        logger.warning(f"Redirected to Generic Page (Login/Home). Attempting reload of {url}...")
                        # Try one more time with a fresh navigation
                        try:
                            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                            await asyncio.sleep(3)
                            await page.keyboard.press("Escape")
                            await asyncio.sleep(1)
                            title = await page.title()
                            if "Make Your Day" in title or title.strip() == "TikTok" or "Log in" in title:
                                logger.warning(f"Still on generic page after retry. Skipping {url}")
                                await page.close()
                                return None
                        except:
                            await page.close()
                            return None
                        
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
                # Wait for interaction/stats to load (Critical for DOM scraping)
                try:
                    await page.wait_for_selector('[data-e2e="like-count"]', state="visible", timeout=8000)
                except:
                    logger.warning("Timeout waiting for stats selector")

                # Views - TikTok shows views in multiple places on the video page
                view_selectors = [
                    '[data-e2e="video-views"]',
                    'strong[data-e2e="video-views"]',
                    '[data-e2e="browse-video-count"]',
                    'span[class*="SpanVideoPlayCount"]',
                    'div[class*="DivVideoCount"]',
                ]
                for vs in view_selectors:
                    view_el = await page.query_selector(vs)
                    if view_el:
                        dom_stats['views'] = self._parse_stat(await view_el.inner_text())
                        if dom_stats['views'] > 0:
                            break

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
                # Only update with non-zero values to avoid overwriting good JSON data
                for k, v in dom_stats.items():
                    if v > 0 and data['stats'].get(k, 0) == 0:
                        data['stats'][k] = v
            except Exception as e:
                print(f"DOM stats extraction failed: {e}")

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
                # Priority: Data Attributes -> H3 -> UniqueID -> Link with @
                author_selectors = [
                    '[data-e2e="browse-user-detail"] h3',
                    '[data-e2e="browse-username"]', 
                    '[data-e2e="video-author-uniqueid"]',
                    'a[href^="/@"]',
                    'h3'
                ]
                
                for sel in author_selectors:
                    el = await page.query_selector(sel)
                    if el:
                        text = await el.inner_text()
                        if text:
                             # Cleanup (remove @ if present)
                             data['author'] = text.replace('@', '').strip()
                             break
                
                if not data.get('author'): data['author'] = "Unknown Author"
            except: data['author'] = ""

        # Hashtags (DOM Fallback)
        if 'hashtags' not in data:
            try:
                tag_els = await page.query_selector_all('a[href*="/tag/"]')
                data['hashtags'] = [await t.inner_text() for t in tag_els]

                # 4. Try parsing hashtags from description if empty
                if not data['hashtags'] and data.get('description'):
                    import re
                    data['hashtags'] = re.findall(r"#(\w+)", data['description'])
            except: data['hashtags'] = []

        # Stats (DOM Fallback)
        if 'stats' not in data: data['stats'] = {}
        
        # Ensure stats dict exists and has defaults
        for k in ['views', 'likes', 'comments', 'shares']:
            if k not in data['stats']: data['stats'][k] = 0

        # NUCLEAR OPTION: Direct JS Evaluation of all data-e2e attributes
        # This bypasses Playwright's visibility checks and grabs raw text instantly.
        try:
            # Poll for Stats (up to 8s)
            found_stats = {}
            for _ in range(16):
                found_stats = await page.evaluate("""() => {
                    const data = {};
                    const els = document.querySelectorAll('[data-e2e]');
                    els.forEach(el => {
                        const attr = el.getAttribute('data-e2e');
                        // Collect key stats - include all known variants
                        if (['like-count', 'comment-count', 'share-count', 'video-views',
                             'browse-like-count', 'browse-comment-count', 'browse-share-count',
                             'browse-video-count', 'undefined-count'].includes(attr)) {
                             data[attr] = el.innerText;
                        }
                    });

                    // Fallback: Try to find view count from aria-labels or nearby text
                    if (!data['video-views'] && !data['browse-video-count']) {
                        // Some TikTok layouts show views in a span with specific class patterns
                        const viewCandidates = document.querySelectorAll('strong[class*="Count"], span[class*="PlayCount"], span[class*="VideoCount"]');
                        viewCandidates.forEach(el => {
                            const text = el.innerText.trim();
                            if (text && /^[\\d\\.]+[KMBkmb]?$/.test(text)) {
                                if (!data['video-views-fallback']) {
                                    data['video-views-fallback'] = text;
                                }
                            }
                        });
                    }

                    return data;
                }""")

                # Check if we have valid data (non-empty)
                if found_stats.get('comment-count') or found_stats.get('share-count') or found_stats.get('like-count'):
                    break
                await asyncio.sleep(0.5)

            # Assign to data (only overwrite zeros)
            if found_stats.get('like-count') and data['stats'].get('likes', 0) == 0:
                data['stats']['likes'] = self._parse_stat(found_stats['like-count'])
            if found_stats.get('comment-count') and data['stats'].get('comments', 0) == 0:
                data['stats']['comments'] = self._parse_stat(found_stats['comment-count'])
            if found_stats.get('share-count') and data['stats'].get('shares', 0) == 0:
                data['stats']['shares'] = self._parse_stat(found_stats['share-count'])

            # Views: try all possible keys
            if data['stats'].get('views', 0) == 0:
                for vk in ['video-views', 'browse-video-count', 'video-views-fallback']:
                    if found_stats.get(vk):
                        parsed = self._parse_stat(found_stats[vk])
                        if parsed > 0:
                            data['stats']['views'] = parsed
                            break

            # Also try browse- prefixed variants
            if found_stats.get('browse-like-count') and data['stats'].get('likes', 0) == 0:
                data['stats']['likes'] = self._parse_stat(found_stats['browse-like-count'])
            if found_stats.get('browse-comment-count') and data['stats'].get('comments', 0) == 0:
                data['stats']['comments'] = self._parse_stat(found_stats['browse-comment-count'])
            if found_stats.get('browse-share-count') and data['stats'].get('shares', 0) == 0:
                data['stats']['shares'] = self._parse_stat(found_stats['browse-share-count'])

        except Exception as e:
            print(f"JS Stats extraction error: {e}")

        # Comments Text (Scroll and scrape)
        # Scroll down multiple times to trigger loading
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(1)
        
        comments = []
        try:
            # Broad selectors for comment CONTAINERS
            container_selectors = [
                 '[data-e2e="comment-level-1"]', 
                 '[data-e2e="comment-item"]',
                 'div[class*="DivCommentContentContainer"]',
                 'div[class*="CommentItem"]',
                 '.css-1i7ohvi-DivCommentItemContainer'
            ]
            
            comment_elements = []
            for sel in container_selectors:
                els = await page.query_selector_all(sel)
                if els:
                    comment_elements = els
                    break

            if comment_elements:
                # Strategy A: Extract from containers
                for el in comment_elements[:25]: 
                    # Try getting text from P or div specific to content
                    text_el = await el.query_selector('p[data-e2e="comment-level-1__content"]')
                    if not text_el: text_el = await el.query_selector('[data-e2e="comment-level-1__content"]')
                    if not text_el: text_el = await el.query_selector('p')
                    if not text_el: text_el = await el.query_selector('span')
                    
                    if text_el:
                        text = await text_el.inner_text()
                        if len(text) > 1 and "Reply" not in text:
                            comments.append(text)
            else:
                # Strategy B: Direct Text Element Search (Fallback)
                # If containers fail, just grab the text paragraphs directly
                text_els = await page.query_selector_all('[data-e2e="comment-level-1__content"]')
                for el in text_els[:25]:
                    text = await el.inner_text()
                    if len(text) > 1:
                        comments.append(text)

        except Exception as e:
            print(f"Comment extraction error: {e}")
        
        data['comments'] = comments

        
        # --- ULTIMATE FALLBACK: Parse Metadata/Description for Stats ---
        # Often the meta description has: "1.9M Likes, 12.7K Comments. TikTok video from User..."
        try:
            desc_text = ""
            meta_desc = await page.query_selector('meta[name="description"]')
            if meta_desc:
                desc_text = await meta_desc.get_attribute('content')
            elif data.get('description'):
                desc_text = data['description']
            
            if desc_text:
                import re
                # Pattern: "1.2M Likes, 30K Comments" - Ensure Case Insensitivity
                flags = re.IGNORECASE
                
                # Likes
                if data['stats']['likes'] == 0:
                    likes_match = re.search(r'([\d\.]+([KMB])?)\s+Likes', desc_text, flags)
                    if likes_match: data['stats']['likes'] = self._parse_stat(likes_match.group(1))

                # Comments - Handle singular/plural
                if data['stats']['comments'] == 0:
                    comm_match = re.search(r'([\d\.]+([KMB])?)\s+Comment', desc_text, flags)
                    if comm_match: data['stats']['comments'] = self._parse_stat(comm_match.group(1))
                    
                # Views (sometimes "1.2M Views")
                if data['stats']['views'] == 0:
                     views_match = re.search(r'([\d\.]+([KMB])?)\s+View', desc_text, flags)
                     if views_match: data['stats']['views'] = self._parse_stat(views_match.group(1))
                     
                # Shares (Rarely in meta, but checking)
                if data['stats']['shares'] == 0:
                     shares_match = re.search(r'([\d\.]+([KMB])?)\s+Share', desc_text, flags)
                     if shares_match: data['stats']['shares'] = self._parse_stat(shares_match.group(1))

        except Exception as e:
            print(f"Meta stats fallback failed: {e}")

        # --- STRATEGY C: Scorched Earth Comment Text ---
        # If we still have 0 comments text, but we know there SHOULD be comments, grab paragraphs.
        # We also loosen the check: if stats says 0 (because we failed to parse) but we see comment-like text, grab it.
        if not data['comments']:
             try:
                 all_ps = await page.query_selector_all('p')
                 candidates = []
                 for p in all_ps[:80]: 
                     txt = await p.inner_text()
                     if len(txt) > 3 and len(txt) < 300: 
                         bad_words = ["Reply", "View more", "Log in", "Follow", "likes", "comments", "share", "TikTok", "Upload", "original sound"]
                         if not any(bw.lower() in txt.lower() for bw in bad_words):
                             candidates.append(txt)
                 data['comments'] = list(set(candidates))[:25] 
             except: pass

            
        # Fallback for Author parsing using Description
        if data.get('author') == "Unknown Author" and desc_text:
            try:
                # "TikTok video from Name (@handle)"
                match_handle = re.search(r'from\s+(.*?)\s+\(@(.*?)\)', desc_text)
                if match_handle:
                    data['author'] = match_handle.group(2) # Prefer Handle
                else:
                    # Try just "from Name"
                    match_from = re.search(r'from\s+(.*?)\s*(?::|\()', desc_text)
                    if match_from: data['author'] = match_from.group(1)
            except: pass

        # Final Cleanup of Hashtags (Unicode support)
        if not data.get('hashtags') and data.get('description'):
            try:
                # Capture #anything_until_space
                data['hashtags'] = re.findall(r"#([^\s\.,!?:;\"'()]+)", data['description'])
            except: pass

        # Final Debug Log
        if data['stats']['comments'] == 0 and len(comments) > 0:
             # Emergency fill: If we found text, we know count >= len(text)
             data['stats']['comments'] = len(comments)

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
                # May be a short URL - scrape_video_details will resolve it
                logger.info(f"Could not extract ID from URL (may be short URL): {url}")

            video_data = await scraper.scrape_video_details(url)
            if video_data:
                # Re-extract tiktok_id from resolved URL if not found initially
                resolved_url = video_data.get('url', url)
                if not tiktok_id:
                    tiktok_id = extract_tiktok_id(resolved_url)
                if not tiktok_id:
                    logger.warning(f"Still could not extract TikTok ID from {resolved_url}. Skipping.")
                    continue
                # Prepare record
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

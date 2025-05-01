# Scrapy settings for schumaker_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "schumaker_scraper"

SPIDER_MODULES = ["schumaker_scraper.spiders"]
NEWSPIDER_MODULE = "schumaker_scraper.spiders"

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT: 1200000
PLAYWRIGHT_BROWSER_TYPE = "chromium"  # or "firefox" or "webkit" if you want
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": False,  # <--- THIS makes it open visible browser
    "slow_mo": 100,  # Optional: slow down actions for easier viewing (milliseconds)
}
# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "schumaker_scraper (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#     "Accept": "text/plain, */*; q=0.01",
#     "Accept-Language": "en-US,en;q=0.9",
#     "Connection": "keep-alive",
#     "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
#     "HDSUBSTORE1": "akc1UUtEYTgxVWtHVHAwTW8yTnl2OXV2VmtNOW9hMGQ=",
#     "Origin": "https://www.shoemarker.co.kr",
#     "Referer": "https://www.shoemarker.co.kr/ASP/Customer/Store.asp",
#     "Sec-Fetch-Dest": "empty",
#     "Sec-Fetch-Mode": "cors",
#     "Sec-Fetch-Site": "same-origin",
#     "Sec-GPC": "1",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
#     "X-Requested-With": "XMLHttpRequest",
#     "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": '"Windows"',
#     "Cookie": "GuestInfo=ddqAab%2FqlRryH%2FwouEX4MIKIF0vEObsc3O0ixyF2YDM%3D; USESSIONID=lHcq0pH9gzMtkZ8ELYJWIQ%3D%3D; UCARTID=lHcq0pH9gzMtkZ8ELYJWIQ%3D%3D; ASPSESSIONIDAAQQRBST=HMGCFPBDKIOHNHDACLNMKLCG; ASPSESSIONIDCSTCRBRT=BPNBBCBDMDACNGMDLIIEIBIA; shoemarker.co.kr-crema_device_token=Z8rsQqxlqU8pQXlPr0zYwbo2H6oHgdI9; _CHAT_DEVICEID=1967CEE0715; CUR_STAMP=1745852696340; _NB_MHS=1-1745852701; ASPSESSIONIDCASSRDRS=EKIFALODBJNDKAPGBJGJMPHK; ASPSESSIONIDAQRBSBRS=ACMGMNNDEPJGAPNDFANBDKGK; CKSUBSTORE1=akc1UUtEYTgxVWtHVHAwTW8yTnl2OXV2VmtNOW9hMGQ%3D",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "schumaker_scraper.middlewares.SchumakerScraperSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    "schumaker_scraper.middlewares.SchumakerScraperDownloaderMiddleware": 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    "schumaker_scraper.pipelines.SchumakerScraperPipeline": 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8-sig"

# DOWNLOAD_HANDLERS = {
#     "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
# }

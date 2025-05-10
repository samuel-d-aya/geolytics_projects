import scrapy
import datetime
import re


class MixMarktSpider(scrapy.Spider):
    name = 'mixmarkt'
    allowed_domains = ['mixmarkt.eu']
    start_urls = ['https://www.mixmarkt.eu/en/germany/stores/']

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 0.5,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 5,
        'AUTOTHROTTLE_ENABLED': True,
    }

    def parse(self, response):
        stores = response.css('#filal-results-wrap > div.item.filiale-item.map-marker')

        for store in stores:
            relative_url = store.css('a::attr(href)').get()
            if not relative_url:
                continue

            absolute_url = response.urljoin(relative_url)

            yield response.follow(
                absolute_url,
                callback=self.parse_store_detail,
                cb_kwargs={
                    'url': absolute_url,
                    'country': store.attrib.get('data-country'),
                    'city': store.attrib.get('data-city'),
                    'latitude': store.attrib.get('data-latitude'),
                    'longitude': store.attrib.get('data-longitude'),
                    'title': store.attrib.get('data-title'),
                    'id': store.attrib.get('data-uid'),
                    'description': store.attrib.get('data-description'),
                }
            )

    def parse_store_detail(self, response, url, country, city, latitude, longitude, title, id, description):
        # Phone number extraction
        phone = response.css(
            '#main > div > div > aside > div > div:nth-child(3) > p:nth-child(1)::text'
        ).get()
        phone = phone.strip() if phone else None

        # Try first opening time selector
        opening_raw = response.css(
            '#main > div > div > aside > div > div:nth-child(2) > p:nth-child(2)::text'
        ).get()
        if not opening_raw or 'Mo -' not in opening_raw:
            opening_raw = response.css(
                '#main > div > div > aside > div > div:nth-child(2) > p:nth-child(4)::text'
            ).get()
        opening_raw = opening_raw.strip() if opening_raw else None

        opening_hours = self.parse_opening_hours(opening_raw) if opening_raw else None

        yield {
            'addr_full': description,
            'city': city,
            'country': country,
            'brand': "Mix Markt",
            'extras': {
                'brand': "Mix Markt",
                'fascia': "Mix Markt",
                'category': "Retail",
                'edit_date': datetime.datetime.now().strftime("%Y%m%d"),
                'lat_lon_source': "Third Party"
            },
            'lat': latitude,
            'lon': longitude,
            'opening_times': opening_hours,
            'name': title,
            'phone': phone,
            'postcode': None,
            'ref': id,
            'state': None,
            'website': url
        }

    def parse_opening_hours(self, raw_text):
        import re

        # Setup day lists
        german_days = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
        english_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        opening_hours = {day: '' for day in english_days}  # Default: all empty

        if not raw_text:
            return {"opening_hours": opening_hours}

        # Remove HTML tags
        raw_text = re.sub(r'<[^>]+>', '', raw_text)

        raw_text = raw_text.strip()
        raw_text = raw_text.replace('–', '-')  # normalize dash
        raw_text = raw_text.replace('. ', '.')  # fix "Fr. 9.00"
        raw_text = re.sub(r'\s+', ' ', raw_text)  # collapse whitespace

        # Flexible regex for matching day range and time
        pattern = r'([A-Za-z]{2})\.?\s*-\s*([A-Za-z]{2})\.?\s*[:.]?\s*(\d{1,2})[.:](\d{2})\s*-\s*(\d{1,2})[.:](\d{2})'
        match = re.search(pattern, raw_text)

        if match:
            start_day, end_day, sh, sm, eh, em = match.groups()
            start_time = f"{int(sh):02}:{sm}"
            end_time = f"{int(eh):02}:{em}"

            try:
                start_idx = german_days.index(start_day)
                end_idx = german_days.index(end_day)

                if start_idx <= end_idx:
                    selected_days = german_days[start_idx:end_idx + 1]
                else:
                    selected_days = german_days[start_idx:] + german_days[:end_idx + 1]

                for gd in selected_days:
                    en_day = english_days[german_days.index(gd)]
                    opening_hours[en_day] = f"{start_time}-{end_time}"
            except ValueError:
                pass  # Ignore if day names are invalid

        return {"opening_hours": opening_hours}




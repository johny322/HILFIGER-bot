import asyncio
import json
import traceback
from typing import Optional, Any
import re
from asyncio import sleep
from datetime import datetime

from fake_headers import Headers
from loguru import logger
from dateutil.parser import parse
from pydantic import BaseModel, HttpUrl
import aiohttp
from bs4 import BeautifulSoup

from parsers.exceptions import CancelError

from parsers.all import get_proxy
from config import user_agent
from parsers.utils import write_file, get_dict_string, write_json


def get_next_url(url, page):
    if '/p/' not in url:
        "https://www.2dehands.be/l/audio-tv-en-foto/accu-s-en-batterijen/p/2/#Language:all-languages%7CPriceCentsTo:10000"
        url_parts = url.split('/#')

        if url_parts[0][-1] == '/':
            url_parts[0] = url_parts[0] + f'p/{page}/'
        else:
            url_parts[0] = url_parts[0] + f'/p/{page}/'
        url = '/#'.join(url_parts)
    else:
        url = re.sub(r'/p/\d{1,}', f'/p/{page}', url)
    print(url)
    return url


class Post(BaseModel):
    post_id: str
    views: int
    favorited_count: int
    created: datetime
    title: str
    description: str
    price: Optional[float]
    seller_name: str
    seller_reg: datetime
    seller_id: Any
    town: str
    link: HttpUrl
    photo_url: HttpUrl
    seller_rating: int
    seller_posts: int = 1
    seller_phone: Optional[str]
    phone: Optional[str]


async def fetch_post(context) -> Post:
    url = context['url']
    domain = 'https://www.2dehands.be'
    logger.debug(f'fetching post - {url}')

    proxy = get_proxy()

    async with aiohttp.ClientSession() as session:
        async with session.get(
                url,
                headers={"user-agent": user_agent},
                proxy=proxy
        ) as resp:
            html = await resp.text()
    #     write_file('source/2dehands1.html', html)
    #     # return

    soup = BeautifulSoup(html, 'lxml')
    data_script = soup.find('script', text=re.compile('window.__CONFIG__')).getText().split('window.__CONFIG__')[-1]
    data = json.loads(get_dict_string(data_script))
    # write_json('source/2dehands1.json', data)
    data = data['listing']
    post_id = data['itemId']
    title = data['title']
    try:
        price = data['priceInfo']['priceCents']/100
    except:
        price = None
    seller_data = data['seller']
    seller_id = seller_data['id']
    seller_name = seller_data['name']
    seller_url = domain + seller_data['pageUrl']
    seller_reg = parse(seller_data['activeSince'].split('T')[0])

    seller_phone = seller_data.get('phoneNumber')
    if seller_phone:
        seller_phone = seller_phone.replace(' ', '').replace('(0)', '').replace('-', '')
        if seller_phone[0] == '0':
            seller_phone = '+32' + seller_phone[1:]
        # if '+' not in seller_phone:
        #     seller_phone = '+32' + seller_phone
    else:
        seller_phone = None

    town = []
    try:
        town.append(seller_data['location']['countryName'])
    except:
        pass
    try:
        town.append(seller_data['location']['cityName'])
    except:
        pass
    town = ','.join(town)
    photo_url = 'https:' + data['gallery']['imageUrls'][0].replace('$_#.jpg', '$_86.jpg').replace('_#.', '_86.')
    stats = data['stats']
    views = stats['viewCount']
    favorited_count = stats['favoritedCount']
    created = parse(stats['since'].split('T')[0])
    description = soup.find('div', {'data-collapsable': 'description'}).getText(strip=True, separator='\n')
    # description = context['description']

    phone_url = f'https://www.2dehands.be/v/api/call-tracking-phone-number?itemId={post_id}'
    if not seller_phone:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    phone_url,
                    headers={"user-agent": user_agent},
                    proxy=proxy
            ) as resp:
                phone_data = await resp.json()
            phone = phone_data.get('phoneNumber')
            if phone:
                phone = phone.replace(' ', '').replace('(0)', '').replace('-', '')
                if phone[0] == '0':
                    phone = '+32' + phone[1:]
                # if '+' not in seller_phone:
                #     seller_phone = '+32' + seller_phone
            else:
                phone = None

    async with aiohttp.ClientSession() as session:
        async with session.get(
                seller_url,
                headers={
                    "user-agent": user_agent,
                },
                proxy=proxy
        ) as resp:
            seller_html = await resp.text()
        # write_file('source/2dehands_seller2.html', seller_html)
    seller_soup = BeautifulSoup(seller_html, 'lxml')
    seller_json = json.loads(seller_soup.find('script', {'id': '__NEXT_DATA__'}).getText(strip=True))
    seller_info = seller_json['props']['seller']
    try:
        seller_rating = seller_info['reviews']['score']
    except:
        seller_rating = 0
    seller_posts = seller_json['props']['pageProps']['searchRequestAndResponse']['totalResultCount']

    return Post(
        post_id=post_id,
        seller_id=seller_id,
        seller_reg=seller_reg,
        views=views,
        favorited_count=favorited_count,
        created=created,
        title=title,
        description=description,
        price=price,
        seller_name=seller_name,
        town=town,
        link=url,
        photo_url=photo_url,
        seller_posts=seller_posts,
        seller_rating=seller_rating,
        seller_phone=seller_phone,
        phone=seller_phone or phone
    )


async def dehands_parse(url, page_sleep: int = 2):
    page = 1
    get_posts = None
    url = get_next_url(url, page)

    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(
                    url,
                    headers=Headers().generate(),
                    proxy=get_proxy()
            ) as resp:
                print(resp.url)
                html = await resp.text()
            # write_file('source/2dehands1_list.html', html)
            # return

            soup = BeautifulSoup(html, "lxml")
            data = json.loads(soup.find('script', {'id': '__NEXT_DATA__'}).getText(strip=True))
            data = data['props']
            search_results = data['pageProps']['searchRequestAndResponse']['listings']

            if not search_results:
                logger.error("search_results empty!")
                await sleep(1)
                break
            results = []
            domain = 'https://www.2dehands.be'

            for result in search_results:
                context = dict(
                    url=domain + result['vipUrl'],
                    description=result['description']
                )
                results.append(context)
            get_posts = len(results)

            for result in results:
                try:
                    post = await fetch_post(result)
                    # post = None
                    yield (post, get_posts)
                    get_posts = None
                except CancelError as ex:
                    logger.warning(ex)
                    await sleep(5)
                except Exception as ex:
                    logger.exception(ex)
                    await sleep(2)

            page += 1
            url = get_next_url(url, page)


async def main():
    url1 = 'https://www.2dehands.be/l/audio-tv-en-foto/accu-s-en-batterijen/'
    url2 = "https://www.2dehands.be/l/audio-tv-en-foto/accu-s-en-batterijen/#Language:all-languages%7CPriceCentsTo:10000"
    url3 = 'https://www.2dehands.be/l/auto-s/daewoo/'
    url4 = 'https://www.2dehands.be/q/apple/'
    async for post, get_posts in dehands_parse(url4):
        print(post, get_posts)


async def main1():
    url1 = 'https://www.2dehands.be/v/auto-s/mercedes-benz/m1891951903-mercedes-benz-sprinter-dubbel-cabine-lichte-vracht-kipper'
    url2 = 'https://www.2dehands.be/v/huis-en-inrichting/kamerplanten/m1891952261-monstera-deliciosa'
    res = await fetch_post({'url': url1})
    print(res)
    print(hasattr(res, 'name'))
    print(hasattr(res, 'title'))
    print(res.dict())
    print(hasattr(res, 'currency'))



if __name__ == "__main__":
    # print(get_next_url('https://www.2dehands.be/l/audio-tv-en-foto/accu-s-en-batterijen/', 3))
    asyncio.run(main1())

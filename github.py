import contextlib
import json
from enum import Enum

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from util import logger

TRENDING_REPOSITORY_URL = "https://github.com/trending"
TRENDING_DEVELOPER_URL = "https://github.com/trending/developers"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
}

RETRIES = Retry(total=3,
                backoff_factor=1,
                status_forcelist=[k for k in range(400, 600)])


@contextlib.contextmanager
def request_session():
    s = requests.session()
    try:
        s.headers.update(HEADERS)
        s.mount("http://", HTTPAdapter(max_retries=RETRIES))
        s.mount("https://", HTTPAdapter(max_retries=RETRIES))
        yield s
    finally:
        s.close()


class Since(Enum):
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'


class GitHub:

    def get_trending_repository(self, since: Since = Since.daily):
        """热门仓库
        {'href': href, 'url': url, 'description': desc, 'language': language,
        'stars': stars, 'folks': folks, 'recent_stars': recent_stars}
        """
        items = []
        resp = None
        try:
            with request_session() as s:
                params = {'since': since.value}
                resp = s.get(TRENDING_REPOSITORY_URL, params=params)
                soup = BeautifulSoup(resp.text, features='html.parser')
                articles = soup.select('main article.Box-row')
                for article in articles:
                    href = article.select_one('h2.h3 > a')['href']
                    url = 'https://github.com' + href
                    logger.info('%s %s', since, href)

                    # 项目描述
                    description = '无'
                    desc = article.select_one('article > p')
                    if desc:
                        description = desc.text.strip()

                    div = article.select_one('div.f6')
                    spans = div.select('div > span')
                    # 并非每个仓库都有语言标签
                    language = '无'
                    if len(spans) == 3:
                        language = spans[0].text.strip()
                    # 最近关注数
                    recent_stars = spans[-1].text.strip()

                    star_folk = div.select('a')
                    stars = star_folk[0].text.strip()
                    folks = star_folk[1].text.strip()

                    item = {'href': href, 'url': url, 'description': description, 'language': language,
                            'stars': stars, 'folks': folks, 'recent_stars': recent_stars}
                    logger.debug('repo:%s', item)
                    items.append(item)
        except:
            logger.exception('get trending repository failed')

        return (items, resp)

    def get_trending_developer(self):
        """热门话题
        """
        items = []
        resp = None
        try:
            with request_session() as s:
                resp = s.get(TRENDING_DEVELOPER_URL)
                soup = BeautifulSoup(resp.text)
        except:
            logger.exception('get trending developer failed')

        return (items, resp)


if __name__ == "__main__":
    github = GitHub()
    repositories, resp = github.get_trending_repository(Since.weekly)
    logger.info('%s', repositories[0])

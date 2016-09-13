# -*- coding: utf-8 -*-
from requests.sessions import Session
from pyquery import PyQuery
import json
import os
import re
import sys


BASE_URL = 'http://www.pordede.com'
LOGIN_URL = '{}/site/login'.format(BASE_URL)
SERIES_URI = '{}/series'.format(BASE_URL)
MOVIES_URI = '{}/pelis'.format(BASE_URL)
SEARCH_URL = '{value}/search/query/{query}/years/1950/on/title/showlist/all'

CONFIG = {}

CATEGORIES = [
    {'name': 'Series', 'value': SERIES_URI},
    {'name': 'Movies', 'value': MOVIES_URI}
]

CONFIG_FOLDER = os.path.expanduser('~/.pordede')
CONFIG_FILE = os.path.join(CONFIG_FOLDER, 'pordede.json')


def load_config():
    """Loads account configuration or creates a default one
    """
    global CONFIG
    if not os.path.exists(CONFIG_FOLDER):
        os.makedirs(CONFIG_FOLDER)
    if not os.path.exists(CONFIG_FILE):
        CONFIG = {'username': '', 'password': '', 'uploader_filter': 'uploaded', 'folderwatch': '~/folderwatch'}
        save_config()
        print 'An empty config file has been generated on {}'.format(CONFIG_FILE)
        print 'Fill in the username and password of your pordede account and restart'
        sys.exit(1)

    with open(CONFIG_FILE) as _config:
        config = json.load(_config)
        CONFIG = config


def save_config():
    """Saves current config as json
    """
    with open(CONFIG_FILE, 'w') as _config:
        json.dump(CONFIG, _config, indent=4)


def save_response(response):
    """Writes the content of a response to a local file.

    Useful to debug scrapping errors
    """
    open('response.html', 'w').write(response.content)


def main_page(session):
    response = session.get(BASE_URL)
    #save_response(response)
    return response


def choose(what, options):
    """Renders a choose UI based on a list of options.

    The user can choose one option or all of them by typing 'all'
    Returns a list of the selected options.
    """
    print 'Choose {}'.format(what)
    for num, option in enumerate(options, start=1):
        print '{id:>2}. {name}'.format(id=num, **option)

    pos = raw_input('Option? ')
    if pos == 'all':
        return options
    else:
        return options[int(pos) - 1]


def ask(what):
    """Helper to ask user for input
    """
    value = raw_input('{}? '.format(what))
    return value


def login(session):
    """Logs into pordede.com with the user credentials
    """
    response = session.post(LOGIN_URL, data={
        'LoginForm[username]': CONFIG['username'],
        'LoginForm[password]': CONFIG['password'],
    }, headers={'Referer': BASE_URL + '/'})
    #save_response(response)
    return response


def find(html, selector):
    """Helper to select an elements out of a page based on a css selector
    """
    pq = PyQuery(html)
    results = pq(selector)
    return results


def find_one(html, selector):
    """Helper to select ONE element out of a page based on a css selector
    """
    return find(html, selector)[0]


def search(session, category, query):
    """Searchs all results matching a query.

    This search can be a movies or a series query, both of them share the same
    markup, so this is reusable
    """
    response = session.get(SEARCH_URL.format(query=query.replace(' ', '-'), **category))
    html = response.content
    results = find(html, '.ddItemContainer')

    def parse(item):
        return {
            'name': find_one(item, 'span.title').text.encode('utf-8'),
            'value': '{}{}'.format(BASE_URL, find_one(item, 'a.defaultLink').attrib['href'])
        }
    return [parse(result) for result in results]


def check_link(session, link):
    """Checks if the given link is currently online
    """
    response = session.get(link)
    links_container = find_one(response.content, '.nicetry.links')
    links = find(links_container, 'a.episodeText')
    all_ok = True
    for dlink in links:
        response = session.get(BASE_URL + dlink.attrib['href'])
        all_ok = all_ok and response.status_code != 404
        if not all_ok:
            break
    return all_ok


def download_link(session, link_info):
    """Downloads a link

    This method actually follows all the needed link patsh to get to the
    final link which includes filtering, sorting and checking.
    """
    response = session.get(link_info['value'])

    def parse_link(item):
        size, unit = re.search(r'([\d,]+)\s*(MB|GB)', ''.join([a for a in find_one(item, '.linkInfo.size').itertext()])).groups()
        size = float(size.replace(',', '.'))
        if unit == 'GB':
            size = size * 1024

        return {
            'id': item.attrib['href'].split('/')[-1],
            'link': '{}{}'.format(BASE_URL, item.attrib['href']),
            'uploader': re.search(r'popup_(.*?).\w+$', find_one(item, 'img').attrib['src']).groups()[0],
            'size': size
        }

    links = []
    for link in find(response.content, '.linksContainer.download ul a.aporteLink'):
        parsed = parse_link(link) or {}
        if parsed.get('uploader') in CONFIG['uploaders_filter']:
            links.append(parsed)

    links = sorted(links, key=lambda x: x['size'], reverse=True)

    working_link = False
    for pos, link in enumerate(links, start=1):
        print 'Checking Link #{}'.format(pos)
        working_link = check_link(session, link['link'])
        if working_link:
            break

    if not working_link:
        print ' No working link found for "[{}]"'.format(link_info['name'])
        return None

    print 'Found available link!'
    dlc_link = link['link'] + '.dlc'
    folderwatch_folder = os.path.expanduser(CONFIG['folderwatch'])
    filename = '{}/{}.dlc'.format(folderwatch_folder, link['id'])
    print 'Downloading {}'.format(dlc_link)
    response = session.get(dlc_link)
    print 'Saving to {}'.format(filename)
    open(filename, 'w').write(response.content)


def movies_links(session, result):
    """Download a movie
    """
    response = session.get(result['value'])
    links_url = BASE_URL + find_one(response.content, '.defaultPopup.big').attrib['href']
    download_link(session, {'name': result['name'], 'value': links_url})


def series_links(session, result):
    """ Choose and download process for series

    This step includes asking for specific episode dowload
    """
    response = session.get(result['value'])

    def parse_season(item):
        return {
            'name': find_one(item, '.title span').text.encode('utf-8'),
            'value': item.attrib['id'][10:]
        }

    seasons = [parse_season(season) for season in find(response.content, '.seasons a')]
    season = choose(' a season', seasons)

    def parse_episode(item):
        info = find_one(item, '.info .title')
        return {
            'name': [a for a in info.itertext()][1].encode('utf-8'),
            'value': '{}{}'.format(BASE_URL, info.attrib['href'])
        }

    episodes = [parse_episode(episode) for episode in find(response.content, '#episodes-{} .modelContainer'.format(season['value']))]
    result = choose(' an episode', episodes)

    if not isinstance(result, list):
        result = [result]

    for episode in result:
        download_link(session, episode)


def find_links(session, category, result):
    """Starts the find & download process for the given category
    """
    fetcher_method = '{}_links'.format(category['name'].lower())
    fetcher = globals()[fetcher_method]
    return fetcher(session, result)


if __name__ == '__main__':
    load_config()
    session = Session()
    session.headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
    }
    main_page(session)
    login(session)
    main_page(session)

    category = choose('category', CATEGORIES)
    query = ask('What do you want to search on {name}'.format(**category))

    results = search(session, category, query)
    result = choose('one', results)

    find_links(session, category, result)


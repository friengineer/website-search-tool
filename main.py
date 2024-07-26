import requests, urllib.robotparser, time, re, json, cmd
from collections import deque, Counter
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse

index = {}

# crawl the website and build the index file
def build():
    site = 'http://example.python-scraping.com/'
    siteQueue = deque([site])

    # parse robots.txt file and set time between requests
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urljoin(site, 'robots.txt'))
    rp.read()

    crawlDelay = rp.crawl_delay('*')

    # retrieve sitemap, parse it and add URLs that can be fetched to the queue
    try:
        r = requests.get(rp.site_maps()[0], timeout = 20)
    except:
        print('Could not retrieve sitemap.')
    else:
        sitemap = BeautifulSoup(r.text, 'html.parser')

        for url in sitemap.find_all('loc'):
            if rp.can_fetch('*', str(url.string)):
                siteQueue.append(str(url.string))

    # store pages visited and index file
    pages = []
    invertedFile = {}
    i = 0

    # fetch pages, parse them for URLs to add to the queue and for words. Count
    # the frequency of the words and add the words and their frequencies to the index
    while siteQueue:
        url = siteQueue.popleft()

        # display current progress
        if i % 20 == 19:
            print(i, 'pages crawled')

        # check if the page can be crawled
        if rp.can_fetch('*', url):
            time.sleep(crawlDelay)

            try:
                r = requests.get(url, timeout = 20)
            except:
                print('Connection timeout for', url)
                continue

            # if a redirect has occurred, get the redirect URL
            if len(r.history) != 0:
                if re.search('\?', r.url):
                    parsed = urlparse(r.url)
                    parsed = parsed._replace(query = '')
                    url = urlunparse(parsed)
                else:
                    url = r.url

            # if the redirect URL is queued or has already been visited, skip to
            # the next URL
            if url in siteQueue or url in pages:
                continue

            pages.append(url)

            page = BeautifulSoup(r.text, 'html.parser')

            # parse URLs in the page and add unseen ones to the queue
            for link in page.find_all('a'):
                if re.search('\?', link['href']):
                    parsed = urlparse(link['href'])
                    parsed = parsed._replace(query = '')
                    link['href'] = urlunparse(parsed)

                if not urljoin(site, link['href']) in siteQueue and urljoin(site, link['href']) not in pages:
                    siteQueue.append(urljoin(site, link['href']))

            words = []

            # tokenise words in the page that contain an alphabetic character and
            # remove redundant punctuation from the beginning and end
            for text in page.stripped_strings:
                terms = text.split()

                for term in terms:
                    if re.search('[a-zA-Z]', term):
                        if term.endswith((':', ',', ')', '):')):
                            term = term.rstrip(':,)')

                        if term.startswith('('):
                            term = term.lstrip('(')

                        words.append(term)

            # count the frequency of the tokenised words in the page and add them
            # to the index
            counter = Counter(words)

            for word, frequency in counter.items():
                if word in invertedFile:
                    invertedFile[word].append((url, frequency))
                else:
                    invertedFile[word] = [(url, frequency)]

            i += 1

    # save the index file to disk
    with open('index.json', 'w', encoding = 'utf-8') as file:
        file.write(json.dumps(invertedFile))

# load the index file from disk
def load():
    try:
        global index

        with open('index.json', 'r', encoding='utf-8') as file:
            index = json.load(file)

        print('Index successfully loaded.')
    except FileNotFoundError:
        print('Index file not found. Please use the "build" command to create the index file first.' )

# print the inverted index for the specified word in the index file
def display(word):
    global index

    if word in index:
        print('Inverted index for', word)
        print()

        for page, count in index[word]:
            print('Page:', page)
            print('Number of occurrences:', count)
            print()
    else:
        print('No entry in index for term', word)

# find and print pages that contain the specified word(s) ordered by the most relevant
# page first
def find(words):
    print('Search results for your query with the most relevant page first.\n')

    # check if the index contains inverted files for any of the words
    if not any(word in index for word in words):
        print('No documents contain any of those words.')
        return

    # used to store term accumulators
    results = {}

    # caculate page scores
    for word in words:
        for posting in index[word]:
            if not posting[0] in results:
                results[posting[0]] = posting[1]
            else:
                results[posting[0]] += posting[1]

    # sort the result pages by score in descending order and print them
    resultsList = list(results.items())
    resultsList.sort(key = lambda x: x[1], reverse = True)

    for result in resultsList:
        print(result[0])

# shell for entering and parsing commands
class SearchShell(cmd.Cmd):
    intro = 'Welcome to the search tool for the website http://example.python-scraping.com/. Type help or ? to list commands.'
    prompt = '\n(search)> '

    # build command
    def do_build(self, arg):
        'Crawl the website, build the index and save it into a file'
        print('Building index, this may take an hour or more.')
        build()
        print('\nWebsite crawled and index file saved successfully.')

    # load command
    def do_load(self, arg):
        'Load a previously built index file'
        load()

    # print command
    def do_print(self, arg):
        'Print the inverted file for the specified word: print foo'
        global index

        if not index:
            print('Index is empty. Create a new index using the "build" command or load a previously saved index using the "load" command.')
        elif len(arg.split()) == 0:
            print('Enter a word to search for.')
        elif len(arg.split()) > 1:
            print('Too many words supplied. Enter only one word.')
        else:
            display(arg)

    # find command
    def do_find(self, args):
        'Search for a phrase containing one or more words: find foo bar'
        global index

        if not index:
            print('Index is empty. Create a new index using the "build" command or load a previously saved index using the "load" command.')
        else:
            words = args.split()

            if len(words) == 0:
                print('Enter at least one word to search for.')
            else:
                find(words)

    # exit command
    def do_exit(self, arg):
        'Quit the program'
        print('Exiting program')
        return True

# start shell
SearchShell().cmdloop()

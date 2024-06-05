import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, urljoin, unquote, urlsplit, urlunsplit
from concurrent.futures import ThreadPoolExecutor
import time
import re

start_time = time.time()

def download_resource(url, folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = unquote(os.path.basename(urlparse(url).path))
            resource_path = os.path.join(folder, filename)
            with open(resource_path, 'wb') as f:
                f.write(response.content)
            return filename
    except Exception as e:
        print("Error downloading resource:", e)
    return None

def download_page(url, folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            update_references(soup, url, folder)
            with open(os.path.join(folder, 'index.html'), 'wb') as f:
                f.write(soup.prettify('utf-8'))
    except Exception as e:
        print("Error downloading page:", e)

def update_references(soup, base_url, folder):
    for resource in soup.find_all(['img', 'script', 'link', 'a']):
        # print("Resource: ", resource)
        attr = 'src' if resource.name in ['img', 'script'] else 'href'
        # print("Attr: ", attr)
        url = resource.get(attr)
        # print("Url: ", str(url), "\n")
        if str(url).startswith('/') and str(url).endswith('/'):
            if not str(url).startswith('/css') and not str(url).startswith('/js'):
                absolute_url = urljoin(base_url, url)
                parsed_url = urlparse(absolute_url)
                # print("Antes: " + str(url))
                resource[attr] = urljoin(url.lstrip('/'), "index.html")
                # print("Despues: " + str(url).lstrip('/') + "\n")
        else:
            # print("Resource: ", resource)
            # print("Attr: ", attr)
            # print("Url: ", re.sub("/css/","", str(url)), "\n")
            if str(url).startswith('/css/') and str(url).endswith('.css'):
                resource[attr] = re.sub("/css/","", str(url))
            if str(url).startswith('/js/') and str(url).endswith('.js'):
                resource[attr] = re.sub("/js/","", str(url))
            if str(url).startswith('/img/') and str(url).endswith('.png'):
                resource[attr] = re.sub("/img/","", str(url))
            if str(url).startswith('/icons/'):
                resource[attr] = re.sub("/icons/","", str(url))
            
            

def create_directory_structure(url, folder):
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.split('/')
    for segment in path_segments:
        if segment:
            folder = os.path.join(folder, unquote(segment))
            os.makedirs(folder, exist_ok=True)
    return folder

def crawl(url, depth, folder):
    if depth == 0:
        return
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            folder = create_directory_structure(url, folder)
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = []
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and not href.startswith('#'):
                        absolute_url = urljoin(url, href)
                        if urlparse(absolute_url).netloc == urlparse(url).netloc:
                            futures.append(executor.submit(crawl, absolute_url, depth - 1, folder))
                        else:
                            print("Skipping external link:", absolute_url)
                for resource in soup.find_all(['img', 'script', 'link']):
                    src = resource.get('src') or resource.get('href')
                    if src:
                        absolute_src = urljoin(url, src)
                        futures.append(executor.submit(download_resource, absolute_src, folder))
                for resource in soup.find_all('a'):
                    href = resource.get('href')
                    if href:
                        absolute_href = urljoin(url, href)
                        if absolute_href.endswith(('.pdf', '.docx', '.doc', '.zip', '.rar', '.tar')):
                            futures.append(executor.submit(download_resource, absolute_href, folder))
                for future in futures:
                    future.result()
            download_page(url, folder)
    except Exception as e:
        print("Error crawling page:", e)

def main(url, depth):
    folder = urlparse(url).netloc
    os.makedirs(folder, exist_ok=True)
    crawl(url, depth, folder)

if __name__ == "__main__":
    # url = "https://www.chunkbase.com/"
    # url = "https://www.nickelodeon.la/"
    url = "https://148.204.58.221/axel/aplicaciones"
    # url = "https://translate.google.com/"
    # url = "https://www.youtube.com/"
    depth = 3
    main(url, depth)

end_time = time.time()
execution_time = end_time - start_time
# print("Execution time:", execution_time, "seconds")

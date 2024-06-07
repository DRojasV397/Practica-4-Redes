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
        attr = 'src' if resource.name in ['img', 'script'] else 'href'
        url = resource.get(attr)
        if str(url).startswith('/') and str(url).endswith('/'):
            if not str(url).startswith('/css') and not str(url).startswith('/js'):
                absolute_url = urljoin(base_url, url)
                parsed_url = urlparse(absolute_url)
                resource[attr] = urljoin(url.lstrip('/'), "index.html")
        else:
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

def generate_index_html(folder):
    parent_folder = os.path.dirname(folder)
    files = os.listdir(folder)
    with open(os.path.join(folder, 'indice.html'), 'w', encoding='utf-8') as f:
        f.write('<html><body><h1>Index of {}</h1><ul>'.format(folder))
        if parent_folder and parent_folder != folder:
            f.write('<li><a href="../index.html">Parent Directory</a></li>')
        for file in files:
            if file != 'indice.html':

                if not "." in str(file):
                    print(str(file))
                    f.write('<li><a href="{}/indice.html">{}</a></li>'.format(file, file))
                else:
                    f.write('<li><a href="{}">{}</a></li>'.format(file, file))
        f.write('</ul></body></html>')

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
            generate_index_html(folder)
    except Exception as e:
        print("Error crawling page:", e)

def main(url, depth):
    folder = urlparse(url).netloc
    os.makedirs(folder, exist_ok=True)
    crawl(url, depth, folder)

if __name__ == "__main__":
    url = "https://www.chunkbase.com/"
    depth = 2
    main(url, depth)

end_time = time.time()
execution_time = end_time - start_time
# print("Execution time:", execution_time, "seconds")

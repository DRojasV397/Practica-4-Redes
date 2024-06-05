import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, urljoin, unquote
from concurrent.futures import ThreadPoolExecutor
import time

start_time = time.time()

def download_resource(url, folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = unquote(os.path.basename(url))
            with open(os.path.join(folder, filename), 'wb') as f:
                f.write(response.content)
    except Exception as e:
        print("Error downloading resource:", e)

def download_page(url, folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(os.path.join(folder, 'index.html'), 'wb') as f:
                f.write(response.content)
    except Exception as e:
        print("Error downloading page:", e)

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
            with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust the number of workers as needed
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
                    future.result()  # Wait for all tasks to complete
            download_page(url, folder)
    except Exception as e:
        print("Error crawling page:", e)

def main(url, depth):
    folder = urlparse(url).netloc
    os.makedirs(folder, exist_ok=True)
    crawl(url, depth, folder)

if __name__ == "__main__":
    # url = input("Enter the URL to crawl: ")
    url = "https://www.chunkbase.com/"
    # url = "http://148.204.58.221/axel/aplicaciones/"
    # depth = int(input("Enter the depth of crawling: "))
    depth = 2
    main(url, depth)

end_time = time.time()
execution_time = end_time - start_time
print("Execution time:", execution_time, "seconds")    

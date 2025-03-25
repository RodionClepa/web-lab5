import sys
import socket
import ssl
import re
import urllib.parse
import os
import json

CACHE_FILE = 'cache.json'

# Load cache from file
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save cache to file
def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

cache = load_cache()

def show_help():
    print("Usage:")
    print("  go2web -u <URL>         # Make an HTTP request to the specified URL and print the response")
    print("  go2web -s <search-term> # Make an HTTP request to search the term using DuckDuckGo and print top 10 results")
    print("  go2web -h               # Show this help")
    print("  go2web -j or --json     # Request JSON response via content negotiation (works with -u)")

def parse_url(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    protocol, rest = url.split("//", 1)
    host, _, path = rest.partition("/")
    path = "/" + path if path else "/"
    return protocol, host, path

def make_http_request(host, path, use_ssl=True, follow_redirects=True, max_redirects=12, accept="text/html"):
    # Check if the response is already cached
    cache_key = f"{host}{path}{accept}"
    if cache_key in cache:
        print(f"Cache hit for {cache_key}")
        return cache[cache_key]
    
    port = 443 if use_ssl else 80
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: go2web-cli\r\n"
        f"Accept: {accept}\r\n"
        f"Connection: close\r\n\r\n"
    )
    
    sock = socket.create_connection((host, port))
    if use_ssl:
        context = ssl.create_default_context()
        sock = context.wrap_socket(sock, server_hostname=host)
    
    sock.sendall(request.encode())
    response = b""
    while True:
        data = sock.recv(4096)
        if not data:
            break
        response += data
    sock.close()
    
    response = response.decode(errors="ignore")

    if follow_redirects:
        # Check if the response is a redirect (e.g., 301, 302, 303, 307, 308)
        redirect_codes = [301, 302, 303, 307, 308]
        try:
            status_code = int(response.split(" ")[1])
        except (IndexError, ValueError):
            status_code = 0

        if status_code in redirect_codes and max_redirects > 0:
            # Look for the "Location" header to extract the redirect URL
            location_match = re.search(r"Location: (.*?)\r\n", response)
            if location_match:
                new_url = location_match.group(1).strip()
                print(f"Redirecting to {new_url}")
                
                # Handle absolute vs relative URLs
                if new_url.startswith("http://") or new_url.startswith("https://"):
                    # Absolute URL: Parse it fully
                    protocol, new_host, new_path = parse_url(new_url)
                else:
                    # Relative URL: Reuse the original host, update the path
                    new_host = host
                    new_path = new_url if new_url.startswith("/") else f"/{new_url}"
                    protocol = "https:" if use_ssl else "http:"
                
                return make_http_request(new_host, new_path, use_ssl=(protocol == "https:"), 
                                         follow_redirects=follow_redirects, max_redirects=max_redirects-1,
                                         accept=accept)
    
    # Cache the response
    cache[cache_key] = response
    save_cache(cache)

    return response
def extract_text(html):
    text = re.sub(r'<[^>]+>', '', html)  # Remove HTML tags
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    return text.strip()

def extract_body(html):
    # Regex to capture content inside <body>...</body>
    body_match = re.search(r'<body.*?>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
    if body_match:
        body_content = body_match.group(1)
        # Remove <script>, <style> and other unwanted tags from the body content
        body_content = re.sub(r'<script.*?>.*?</script>', '', body_content, flags=re.DOTALL | re.IGNORECASE)  # Remove scripts
        body_content = re.sub(r'<style.*?>.*?</style>', '', body_content, flags=re.DOTALL | re.IGNORECASE)  # Remove styles
        body_content = re.sub(r'<[^>]+>', '', body_content)  # Remove any remaining HTML tags
        body_content = re.sub(r'\s+', ' ', body_content)  # Normalize whitespace
        return body_content.strip()
    return ""


def fetch_url(url, accept="text/html"):
    protocol, host, path = parse_url(url)
    response = make_http_request(host, path, use_ssl=(protocol == "https:"), accept=accept)
    headers, body = response.split("\r\n\r\n", 1)
    # If the response headers indicate JSON, try to parse it
    if "application/json" in headers or accept == "application/json":
        try:
            parsed = json.loads(body)
            print(json.dumps(parsed, indent=2))
        except Exception as e:
            print("Error parsing JSON:", e)
            print(body)
    else:
        print(extract_body(body))

def clean_duckduckgo_link(link):
    match = re.search(r'uddg=([^&]+)', link)
    if match:
        return urllib.parse.unquote(match.group(1))
    return link

def search_query(term):
    query = term.replace(" ", "+")
    protocol, host, path = parse_url(f"https://html.duckduckgo.com/html/?q={query}")
    response = make_http_request(host, path)
    links = re.findall(r'<a rel="nofollow" class="result__a" href="(.*?)">(.*?)</a>', response)
    print(links)

    for i, (link, title) in enumerate(links[:10], 1):
        cleaned_link = clean_duckduckgo_link(link)
        print(f"{i}. {extract_text(title)} - {cleaned_link}")

def main():
    args = []
    accept_header = "text/html"
    for arg in sys.argv[1:]:
        if arg in ("-j", "--json"):
            accept_header = "application/json"
        else:
            args.append(arg)
    
    if len(args) < 1:
        print("Too few arguments, calling help")
        show_help()
        return

    option = args[0]

    if option == "-h":
        show_help()
    elif option == "-u" and len(args) > 1:
        fetch_url(args[1], accept=accept_header)
    elif option == "-s" and len(args) > 1:
        search_query(args[1])
    else:
        print("Invalid command. Use -h for help.")    

if __name__ == "__main__":
    main()
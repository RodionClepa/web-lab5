import sys
import socket
import ssl
import re
import urllib.parse

def show_help():
    print("Usage:")
    print("  go2web -u <URL>         # Make an HTTP request to the specified URL and print the response")
    print("  go2web -s <search-term> # Make an HTTP request to search the term using DuckDuckGo and print top 10 results")
    print("  go2web -h               # Show this help")

def parse_url(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    protocol, rest = url.split("//", 1)
    host, _, path = rest.partition("/")
    path = "/" + path if path else "/"
    return protocol, host, path

def make_http_request(host, path, use_ssl=True):
    port = 443 if use_ssl else 80
    request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: go2web-cli\r\nConnection: close\r\n\r\n"
    
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
    
    return response.decode(errors="ignore")

def extract_text(html):
    text = re.sub(r'<[^>]+>', '', html)  # Remove HTML tags
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    return text.strip()

def fetch_url(url):
    protocol, host, path = parse_url(url)
    response = make_http_request(host, path, use_ssl=(protocol == "https:"))
    headers, body = response.split("\r\n\r\n", 1)
    print(extract_text(body))

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
    if len(sys.argv) < 2:
        print("to low arguments, calling help")
        return

    option = sys.argv[1]

    if option == "-h":
        show_help()
    elif option == "-u" and len(sys.argv) > 2:
        fetch_url(sys.argv[2])
    elif option == "-s" and len(sys.argv) > 2:
        search_query(sys.argv[2])
    else:
        print("Invalid command. Use -h for help.")    

if __name__ == "__main__":
    main()
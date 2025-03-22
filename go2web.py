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

def make_http_request(host, path, use_ssl=True, follow_redirects=True, max_redirects=5):
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
    
    response = response.decode(errors="ignore")

    if follow_redirects:
        # Check if the response is a redirect (e.g., 301, 302, 303, 307, 308)
        redirect_code = [301, 302, 303, 307, 308]
        status_code = int(response.split(" ")[1])
        
        if status_code in redirect_code:
            # Look for the "Location" header to extract the redirect URL
            location_match = re.search(r"Location: (.*?)\r\n", response)
            if location_match:
                new_url = location_match.group(1).strip()
                print(f"Redirecting to {new_url}")
                # Recursively follow the redirect
                protocol, host, path = parse_url(new_url)
                return make_http_request(host, path, use_ssl=(protocol == "https:"), follow_redirects=follow_redirects, max_redirects=max_redirects-1)
    
    return response

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
        print("Too few arguments, calling help")
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
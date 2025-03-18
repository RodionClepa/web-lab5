import sys
import socket
import ssl

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

def fetch_url(url):
    protocol, host, path = parse_url(url)
    response = make_http_request(host, path, use_ssl=(protocol == "https:"))
    print(response)
    

def main():
    if len(sys.argv) < 2:
        print("to low arguments, calling help")
        return

    option = sys.argv[1]

    if option == "-h":
        print("show_help()")
    elif option == "-u" and len(sys.argv) > 2:
        fetch_url(sys.argv[2])
    elif option == "-s" and len(sys.argv) > 2:
        print("search_query(sys.argv[2])")
    else:
        print("Invalid command. Use -h for help.")    

if __name__ == "__main__":
    main()
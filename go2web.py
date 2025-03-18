import sys

def parse_url(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    protocol, rest = url.split("//", 1)
    host, _, path = rest.partition("/")
    path = "/" + path if path else "/"
    return protocol, host, path

def fetch_url(url):
    protocol, host, path = parse_url(url)
    print(protocol)
    print(host)
    print(path)
    

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
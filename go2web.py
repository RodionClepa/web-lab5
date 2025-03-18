import sys

def main():
    if len(sys.argv) < 2:
        print("to low arguments, calling help")
        return

    option = sys.argv[1]

    if option == "-h":
        print("show_help()")
    elif option == "-u" and len(sys.argv) > 2:
        print("fetch_url(sys.argv[2])")
    elif option == "-s" and len(sys.argv) > 2:
        print("search_query(sys.argv[2])")
    else:
        print("Invalid command. Use -h for help.")    

if __name__ == "__main__":
    main()
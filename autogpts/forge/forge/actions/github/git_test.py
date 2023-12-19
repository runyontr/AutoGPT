import github
import pprint

def main():
    # Test the git functions here
    # For example, you can clone a repository

    i = github.fetch_issue(None, "id_1", "docs", "runyontr", 4)
    pprint.pprint(i)


if __name__ == "__main__":
    main()

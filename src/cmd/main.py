import sys
from packages.utils import print_err


def main():
    if len(sys.argv) < 2:
        print_err(
            "Missing config.txt. Pass as python script.py config.txt",
        )
        exit(1)

    config_path = sys.argv[1]
    print(f"config path {config_path}")


if __name__ == "__main__":
    main()

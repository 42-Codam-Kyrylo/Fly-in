import sys
from packages.utils import print_err
from packages.parsing import ParsingError, ConfigParser


def main():
    if len(sys.argv) < 2:
        print_err(
            "Missing config.txt. Pass as python script.py config.txt",
        )
        exit(1)

    config_path = sys.argv[1]
    try:
        parser = ConfigParser(config_path)
        config = parser.parse()
        print(config)
    except ParsingError as e:
        print(str(e))
    except Exception as e:
        print(str(e))
    # print(f"config path {config_path}")


if __name__ == "__main__":
    main()

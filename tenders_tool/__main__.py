import sys
from tenders_tool import snake


def main(msg="Hello from __main__"):
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    snake.say(msg)


if __name__ == "__main__":
    main()

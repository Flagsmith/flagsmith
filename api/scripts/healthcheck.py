import argparse
import socket

parser = argparse.ArgumentParser(
    description="Check if the API is able to accept local TCP connections.",
)
parser.add_argument(
    "--port",
    "-p",
    type=int,
    default=8000,
    help="Port to check the API on (default: 8000)",
)
parser.add_argument(
    "--timeout",
    "-t",
    type=int,
    default=1,
    help="Socket timeout for the connection attempt in seconds (default: 1)",
)


def main() -> None:
    args = parser.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(args.timeout)
    sock.connect(("localhost", args.port))
    sock.close()


if __name__ == "__main__":
    main()

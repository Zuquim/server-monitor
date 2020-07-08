#!/usr/bin/env python3

import argparse
import http.client as hc
import smtplib
import sys
import threading
from distutils import spawn
from re import split
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from subprocess import run
from time import sleep, strftime
from urllib.parse import urlencode


def print_log(string: str, indent: int = 0):
    print(f"[{strftime('%Y-%m-%d %H:%M:%S')}]{''.center(indent)} {string}")


parser = argparse.ArgumentParser(
    description="Check if hosts are up.",
    formatter_class=lambda prog: argparse.HelpFormatter(
        prog, max_help_position=150, width=150
    ),
)
# parser.add_argument("-u", "--smtpuser", help="The SMTP username", default="")
# parser.add_argument("-p", "--smtppass", help="The SMTP password", default="")
# parser.add_argument(
#     "-l",
#     "--smtpsubject",
#     help="The SMTP subject line",
#     default="Service status changed!",
# )
parser.add_argument(
    "-o",
    "--interval",
    help="The interval in minutes between checks (default 5)",
    default=5,
    type=int,
)
parser.add_argument(
    "-r",
    "--retry",
    help="The retry count when a connection fails (default 5)",
    default=5,
    type=int,
)
parser.add_argument(
    "-d",
    "--delay",
    help="The retry delay in seconds when a connection fails (default 10)",
    default=10,
    type=int,
)
parser.add_argument(
    "-t",
    "--timeout",
    help="The connection timeout in seconds (default 3)",
    default=3,
    type=int,
)
# parser.add_argument("-y", "--pushoverapi", help="The pushover.net API key", default="")
# parser.add_argument(
#     "-z", "--pushoveruser", help="The pushover.net user key", default=""
# )
required_arguments = parser.add_argument_group("required arguments")
# required_arguments.add_argument(
#     "-s", "--smtpserver", help="The SMTP server:port", required=True
# )
# required_arguments.add_argument(
#     "-f", "--smtpfrom", help="The FROM email address", required=True
# )
# required_arguments.add_argument(
#     "-k", "--smtpto", help="The TO email address", required=True
# )
required_arguments.add_argument(
    "-m",
    "--monitor",
    nargs="+",
    help='The servers to monitor. Format: "<server>:<port>[:udp]"',
    required=True,
)
args = parser.parse_args()


def check_tcp(ip: str, port: int) -> bool:
    s = socket(AF_INET, SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        s.shutdown(SHUT_RDWR)
        return True
    except:
        return False
    finally:
        s.close()


def check_udp(ip: str, port: int, timeout: int = 1) -> bool:
    cmd = run(
        f"nc -zu -w {timeout} {ip} {port} >/dev/null".split(),
        capture_output=True,
        timeout=2,
    )
    if cmd.returncode == 0:
        return True
    else:
        return False


def check_host(host: dict, retry: int = 1) -> bool:
    host_up = False
    for i in range(retry):
        if host["conntype"] == "udp":
            if check_udp(host["ip"], host["port"]):
                host_up = True
                continue
            else:
                print_log(
                    "No response from "
                    f"{host['ip']}:{host['port']}:{host['conntype']}, "
                    f"retrying in {delay}s..."
                )
                sleep(delay)
        else:
            if check_tcp(host["ip"], host["port"]):
                host_up = True
                continue
            else:
                print_log(
                    "No response from "
                    f"{host['ip']}:{host['port']}:{host['conntype']}, "
                    f"retrying in {delay}s..."
                )
                sleep(delay)
    return host_up


def send_message():
    print_log("Sending SMTP message", 2)
    message = f"Subject: {args.smtpsubject}\r\n"
    message += f"From: {args.smtpfrom}\r\n"
    message += f"To: {args.smtpto}\r\n"
    message += "\r\n"
    for change in changes:
        message += change + ".\r\n"
    server = smtplib.SMTP(args.smtpserver)
    server.starttls()
    if args.smtpuser != "" and args.smtppass != "":
        server.login(args.smtpuser, args.smtppass)
    server.sendmail(args.smtpfrom, args.smtpto, message)
    server.quit()
    if args.pushoverapi != "" and args.pushoveruser != "":
        print_log("Sending Pushover message", 2)
        conn = hc.HTTPSConnection("api.pushover.net:443")
        conn.request(
            "POST",
            "/1/messages.json",
            urlencode(
                {
                    "token": args.pushoverapi,
                    "user": args.pushoveruser,
                    "message": message,
                    "sound": "falling",
                }
            ),
            {"Content-type": "application/x-www-form-urlencoded"},
        )
        conn.getresponse()


def parse_host(host: dict, retry: int):
    prestatus = host["status"]
    print_log(f"Checking {host['ip']}:{host['port']}:{host['conntype']}...")
    if check_host(host, retry):
        host["status"] = "up"
        if prestatus == "down":
            changes.append(
                f"{host['ip']}:{host['port']}:{host['conntype']} = {host['status']}"
            )
    else:
        host["status"] = "down"
        if prestatus == "up":
            changes.append(
                f"{host['ip']}:{host['port']}:{host['conntype']} = {host['status']}"
            )
    print_log(
        f"Status of {host['ip']}:{host['port']}:{host['conntype']} = {host['status'].upper()}"
    )


if __name__ == "__main__":
    nc = spawn.find_executable("nc")
    if not nc:
        print_log("Missing `nc` (NetCat) binary. Exiting...")
        sys.exit(1)

    retry = args.retry
    delay = args.delay
    timeout = args.timeout
    hosts = []
    for host in args.monitor:
        conntype = "tcp"
        ip_port = split("[:]", host)
        ip = ip_port[0]
        port = int(ip_port[1])
        if len(ip_port) > 2:
            conntype = ip_port[2]
        hosts.append(
            {"ip": ip, "port": port, "conntype": conntype, "status": "unknown"}
        )

    try:
        while True:
            changes = []
            threads = []
            for host in hosts:
                t = threading.Thread(target=parse_host, args=(host, retry,))
                threads.append(t)
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            if len(changes) > 0:
                send_message()
                del changes[:]
            del threads[:]
            print_log(f"Waiting {args.interval} minutes for next check.")
            sleep(args.interval * 60)
    except KeyboardInterrupt:
        print_log("Exiting (KeyboardInterrupt)...")

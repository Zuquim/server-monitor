# server-monitor
Checks if `ipv4_addresses:ports` are up and running.

## Usage
```
# curl -O https://raw.githubusercontent.com/Zuquim/server-monitor/master/server-monitor.py
# ./server-monitor.py --help
usage: server-monitor.py [-h] [-o INTERVAL] [-r RETRY] [-d DELAY] [-t TIMEOUT] -m MONITOR [MONITOR ...]

Check if hosts are up.

optional arguments:
  -h, --help                                                 show this help message and exit
 # -u SMTPUSER, --smtpuser SMTPUSER                           [DISABLED] The SMTP username
 # -p SMTPPASS, --smtppass SMTPPASS                           [DISABLED] The SMTP password
 # -l SMTPSUBJECT, --smtpsubject SMTPSUBJECT                  [DISABLED] The SMTP subject line
  -o INTERVAL, --interval INTERVAL                           The interval in minutes between checks (default 60)
  -r RETRY, --retry RETRY                                    The retry count when a connection fails (default 5)
  -d DELAY, --delay DELAY                                    The retry delay in seconds when a connection fails (default 10)
  -t TIMEOUT, --timeout TIMEOUT                              The connection timeout in seconds (default 3)
 # -y PUSHOVERAPI, --pushoverapi PUSHOVERAPI                  [DISABLED] The pushover.net API key
 # -z PUSHOVERUSER, --pushoveruser PUSHOVERUSER               [DISABLED] The pushover.net user key


required arguments:
 # -s SMTPSERVER, --smtpserver SMTPSERVER                     [DISABLED] The SMTP server:port
 # -f SMTPFROM, --smtpfrom SMTPFROM                           [DISABLED] The FROM email address
 # -k SMTPTO, --smtpto SMTPTO                                 [DISABLED] The TO email address
  -m MONITOR [MONITOR ...], --monitor MONITOR [MONITOR ...]  The servers to monitor. Format: "<server>:<port> <server>:<port>[:udp]"
```

## Docker
The following example is for docker-compose.
```
  server-monitor:
    image: nowsci/server-monitor
    container_name: server-monitor
    volumes:
      - /etc/localtime:/etc/localtime:ro
    environment:
      - OPTIONS=--smtpserver mail:25 --smtpfrom user@domain.tld --smtpto user@domain.tld --monitor google.com:443 microsoft.com:443
    restart: "no"
```
---
## Forked from
[Fmstrat/server-monitor](https://github.com/Fmstrat/server-monitor)

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    nmap \
    && rm -rf /var/lib/apt/lists/*

# -F  fast scan (100 most common ports)
# -sT TCP connect scan (no root required)
# -sV service version detection
ENTRYPOINT ["nmap", "-F", "-sT", "-sV", "--open"]

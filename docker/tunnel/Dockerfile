FROM alpine:3.17.1

RUN apk add curl

RUN curl -o cloudflared -L https://github.com/cloudflare/cloudflared/releases/download/2024.6.0/cloudflared-linux-amd64

RUN chmod +x cloudflared && \
    mv cloudflared /bin

CMD cloudflared --no-autoupdate tunnel run

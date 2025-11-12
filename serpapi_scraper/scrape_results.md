Last login: Wed Nov 12 08:59:53 on ttys002
sunsupported shell: "-z"
sh-%                                                                                                                                                                                                                                           (base) homekeepr1@dawons-Mac-Studio Documents % ssh-scraper
Welcome to Ubuntu 24.04.3 LTS (GNU/Linux 6.8.0-87-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Wed Nov 12 07:57:05 PM UTC 2025

  System load:  0.02                Processes:             152
  Usage of /:   11.5% of 149.92GB   Users logged in:       1
  Memory usage: 5%                  IPv4 address for eth0: 178.156.201.152
  Swap usage:   0%                  IPv6 address for eth0: 2a01:4ff:f0:f2ad::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is enabled.

0 updates can be applied immediately.


Last login: Wed Nov 12 19:22:59 2025 from 172.56.202.130
root@documentation-scraper:~# cd documentation-scraper/
root@documentation-scraper:~/documentation-scraper# ./deploy.sh
Agent pid 34298
Enter passphrase for /root/.ssh/scraper:
Identity added: /root/.ssh/scraper (root@ubuntu-s-1vcpu-1gb-nyc3-01)
🚀 Starting deployment...
📥 Pulling latest code...
remote: Enumerating objects: 7, done.
remote: Counting objects: 100% (7/7), done.
remote: Compressing objects: 100% (1/1), done.
remote: Total 4 (delta 3), reused 4 (delta 3), pack-reused 0 (from 0)
Unpacking objects: 100% (4/4), 1.81 KiB | 1.81 MiB/s, done.
From github.com:Homekeepr-Inc/documentation-scraper
   951693a..a039773  main       -> origin/main
Updating 951693a..a039773
Fast-forward
 serpapi_scraper/orchestrator.py | 242 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-------------------------------------------------------
 1 file changed, 176 insertions(+), 66 deletions(-)
🔨 Building new app image...
Compose now can delegate build to bake for better performances
Just set COMPOSE_BAKE=true
[+] Building 2.2s (13/13) FINISHED                                                                                                                                                                                              docker:default
 => [app internal] load build definition from Dockerfile                                                                                                                                                                                  0.0s
 => => transferring dockerfile: 817B                                                                                                                                                                                                      0.0s
 => [app internal] load metadata for docker.io/selenium/standalone-chrome:latest                                                                                                                                                          0.1s
 => [app internal] load .dockerignore                                                                                                                                                                                                     0.0s
 => => transferring context: 2B                                                                                                                                                                                                           0.0s
 => [app internal] load build context                                                                                                                                                                                                     0.1s
 => => transferring context: 117.85kB                                                                                                                                                                                                     0.0s
 => [app 1/7] FROM docker.io/selenium/standalone-chrome:latest@sha256:529b51273aa7020b054fb0b49bbb87e3a68712c15d856f66e1b4a630edcd43c9                                                                                                    0.0s
 => CACHED [app 2/7] RUN apt-get update     && apt-get install -y curl gnupg lsb-release     && mkdir -p /etc/apt/keyrings     && apt-get update     && apt-get install -y python3.11     && apt-get clean     && rm -rf /var/lib/apt/li  0.0s
 => CACHED [app 3/7] WORKDIR /app                                                                                                                                                                                                         0.0s
 => CACHED [app 4/7] COPY requirements.txt .                                                                                                                                                                                              0.0s
 => CACHED [app 5/7] RUN python3 -m pip install --no-cache-dir -r requirements.txt                                                                                                                                                        0.0s
 => [app 6/7] COPY . .                                                                                                                                                                                                                    0.7s
 => [app 7/7] RUN mkdir -p headless-browser-scraper/temp                                                                                                                                                                                  0.1s
 => [app] exporting to image                                                                                                                                                                                                              1.1s
 => => exporting layers                                                                                                                                                                                                                   1.1s
 => => writing image sha256:0c9f19013408e2828293253bb2f5c941ac2259de21ee8e2e6d64cb639481bb87                                                                                                                                              0.0s
 => => naming to docker.io/library/documentation-scraper-app                                                                                                                                                                              0.0s
 => [app] resolving provenance for metadata file                                                                                                                                                                                          0.0s
[+] Building 1/1
 ✔ app  Built                                                                                                                                                                                                                             0.0s
🔄 Scaling up to 8 app instances
WARN[0000] Found orphan containers ([documentation-scraper-db-init-1]) for this project. If you removed or renamed this service in your compose file, you can run this command with the --remove-orphans flag to clean it up.
[+] Running 11/11
 ✔ Network documentation-scraper_app_network  Created                                                                                                                                                                                     0.1s
 ✔ Container documentation-scraper-caddy-1    Started                                                                                                                                                                                     0.3s
 ✔ Container documentation-scraper-squid-1    Started                                                                                                                                                                                     0.3s
 ✔ Container documentation-scraper-app-8      Started                                                                                                                                                                                     0.8s
 ✔ Container documentation-scraper-app-1      Started                                                                                                                                                                                     1.6s
 ✔ Container documentation-scraper-app-3      Started                                                                                                                                                                                     0.6s
 ✔ Container documentation-scraper-app-5      Started                                                                                                                                                                                     0.4s
 ✔ Container documentation-scraper-app-2      Started                                                                                                                                                                                     1.4s
 ✔ Container documentation-scraper-app-6      Started                                                                                                                                                                                     1.1s
 ✔ Container documentation-scraper-app-4      Started                                                                                                                                                                                     1.8s
 ✔ Container documentation-scraper-app-7      Started                                                                                                                                                                                     0.5s
⏳ Waiting for all app containers to be healthy...
Waiting for health checks...
✅ All app containers are healthy
🔄 Scaling down to 4 app instances
WARN[0000] Found orphan containers ([documentation-scraper-db-init-1]) for this project. If you removed or renamed this service in your compose file, you can run this command with the --remove-orphans flag to clean it up.
[+] Running 8/8
 ✔ Container documentation-scraper-app-1  Running                                                                                                                                                                                         0.0s
 ✔ Container documentation-scraper-app-2  Running                                                                                                                                                                                         0.0s
 ✔ Container documentation-scraper-app-3  Running                                                                                                                                                                                         0.0s
 ✔ Container documentation-scraper-app-4  Running                                                                                                                                                                                         0.0s
 ✔ Container documentation-scraper-app-8  Removed                                                                                                                                                                                         0.5s
 ✔ Container documentation-scraper-app-6  Removed                                                                                                                                                                                         0.5s
 ✔ Container documentation-scraper-app-5  Removed                                                                                                                                                                                         0.5s
 ✔ Container documentation-scraper-app-7  Removed                                                                                                                                                                                         0.5s
🧹 Cleaning up old images...
Deleted Images:
deleted: sha256:ae8b06c51b8b6f648fa135683ce9dd3e27e9a250d954a2b352c20a432737ad58

Total reclaimed space: 0B
🎉 Deployment complete!
root@documentation-scraper:~/documentation-scraper# docke rps
Command 'docke' not found, did you mean:
  command 'docker' from deb docker.io (28.2.2-0ubuntu1~24.04.1)
  command 'docker' from deb podman-docker (4.9.3+ds1-1ubuntu0.2)
Try: apt install <deb name>
root@documentation-scraper:~/documentation-scraper# docker ps
CONTAINER ID   IMAGE                         COMMAND                  CREATED          STATUS                    PORTS                                                                NAMES
04fd3a08ba57   documentation-scraper-app     "uvicorn app.main:ap…"   20 seconds ago   Up 19 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-3
9518f55fb734   documentation-scraper-app     "uvicorn app.main:ap…"   20 seconds ago   Up 18 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-2
388edc11e6ca   documentation-scraper-app     "uvicorn app.main:ap…"   20 seconds ago   Up 18 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-1
34f062ba1ed6   documentation-scraper-app     "uvicorn app.main:ap…"   20 seconds ago   Up 18 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-4
a32a30e19f47   caddy:2                       "caddy run --config …"   20 seconds ago   Up 19 seconds             80/tcp, 2019/tcp, 443/udp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp   documentation-scraper-caddy-1
f637ce62ead9   documentation-scraper-squid   "/bin/sh -c 'envsubs…"   20 seconds ago   Up 19 seconds             8888/tcp                                                             documentation-scraper-squid-1
root@documentation-scraper:~/documentation-scraper# docker compose logs -f
app-4    | INFO:     Started server process [1]
app-4    | INFO:     Waiting for application startup.
app-4    | INFO:     Application startup complete.
app-4    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-4    | INFO:     127.0.0.1:43838 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     Started server process [1]
app-2    | INFO:     Waiting for application startup.
app-3    | INFO:     Started server process [1]
app-3    | INFO:     Waiting for application startup.
app-3    | INFO:     Application startup complete.
app-3    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-3    | INFO:     127.0.0.1:43774 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     Application startup complete.
app-2    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-2    | INFO:     127.0.0.1:43816 - "GET /health HTTP/1.1" 200 OK
squid-1  | --- Generated squid.conf ---
squid-1  | # Squid configuration template for round-robin upstream proxy rotation
squid-1  |
squid-1  | http_port 8888
squid-1  |
squid-1  | # Upstream proxies (add more cache_peer lines as needed for additional upstreams)
squid-1  | cache_peer 192.210.251.164 parent 12323 0 proxy-only no-query no-digest login=14a79366c9697:6bbbc49dd3 round-robin name=upstream1
squid-1  | cache_peer 89.106.3.243 parent 12323 0 proxy-only no-query no-digest login=14a50ddfa322c:ae6e621d2a round-robin name=upstream2
squid-1  |
squid-1  | # Allow access to all upstream peers
squid-1  | cache_peer_access upstream1 allow all
squid-1  | cache_peer_access upstream2 allow all
squid-1  |
squid-1  | never_direct allow all
squid-1  |
squid-1  | # Access control
squid-1  | acl localnet src 127.0.0.1
squid-1  | acl localnet src 172.18.0.0/16
squid-1  | http_access allow localnet
squid-1  | http_access deny all
squid-1  |
squid-1  | # Logging
squid-1  | access_log none
squid-1  | cache_log none
squid-1  |
squid-1  | # Disable caching
squid-1  | cache deny all--- End Generated squid.conf ---
squid-1  | 2025/11/12 19:57:18| Processing Configuration File: /etc/squid/squid.conf (depth 0)
squid-1  | 2025/11/12 19:57:18| Created PID file (/var/run/squid.pid)
squid-1  | 2025/11/12 19:57:18| ERROR: Cannot open cache_log (none) for writing;
squid-1  |     fopen(3) error: (13) Permission denied
squid-1  | 2025/11/12 19:57:18| Current Directory is /
caddy-1  | {"level":"info","ts":1762977438.494839,"msg":"maxprocs: Leaving GOMAXPROCS=4: CPU quota undefined"}
caddy-1  | {"level":"info","ts":1762977438.495029,"msg":"GOMEMLIMIT is updated","package":"github.com/KimMachineGun/automemlimit/memlimit","GOMEMLIMIT":7314971443,"previous":9223372036854775807}
caddy-1  | {"level":"info","ts":1762977438.4950578,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
caddy-1  | {"level":"info","ts":1762977438.4961665,"msg":"adapted config to JSON","adapter":"caddyfile"}
caddy-1  | {"level":"warn","ts":1762977438.496191,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":2}
squid-1  | 2025/11/12 19:57:18| Starting Squid Cache version 6.12 for x86_64-alpine-linux-musl...
app-1    | INFO:     Started server process [1]
app-1    | INFO:     Waiting for application startup.
app-1    | INFO:     Application startup complete.
app-1    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-1    | INFO:     127.0.0.1:43830 - "GET /health HTTP/1.1" 200 OK
caddy-1  | {"level":"info","ts":1762977438.4971244,"logger":"admin","msg":"admin endpoint started","address":"localhost:2019","enforce_origin":false,"origins":["//localhost:2019","//[::1]:2019","//127.0.0.1:2019"]}
caddy-1  | {"level":"info","ts":1762977438.497309,"logger":"tls.cache.maintenance","msg":"started background certificate maintenance","cache":"0xc000445a00"}
caddy-1  | {"level":"warn","ts":1762977438.4974458,"logger":"tls","msg":"stapling OCSP","error":"no OCSP stapling for [cloudflare origin certificate *.homekeepr.co homekeepr.co]: no URL to issuing certificate"}
caddy-1  | {"level":"info","ts":1762977438.4975698,"logger":"http.auto_https","msg":"skipping automatic certificate management because one or more matching certificates are already loaded","domain":"api.homekeepr.co","server_name":"srv0"}
caddy-1  | {"level":"info","ts":1762977438.4975913,"logger":"http.auto_https","msg":"enabling automatic HTTP->HTTPS redirects","server_name":"srv0"}
caddy-1  | {"level":"info","ts":1762977438.4978676,"logger":"http","msg":"enabling HTTP/3 listener","addr":":443"}
caddy-1  | {"level":"info","ts":1762977438.4979346,"msg":"failed to sufficiently increase receive buffer size (was: 208 kiB, wanted: 7168 kiB, got: 416 kiB). See https://github.com/quic-go/quic-go/wiki/UDP-Buffer-Sizes for details."}
caddy-1  | {"level":"info","ts":1762977438.4984593,"logger":"http.log","msg":"server running","name":"srv0","protocols":["h1","h2","h3"]}
caddy-1  | {"level":"warn","ts":1762977438.498542,"logger":"http","msg":"HTTP/2 skipped because it requires TLS","network":"tcp","addr":":80"}
caddy-1  | {"level":"warn","ts":1762977438.4985642,"logger":"http","msg":"HTTP/3 skipped because it requires TLS","network":"tcp","addr":":80"}
caddy-1  | {"level":"info","ts":1762977438.4986057,"logger":"http.log","msg":"server running","name":"remaining_auto_https_redirects","protocols":["h1","h2","h3"]}
caddy-1  | {"level":"info","ts":1762977438.5006444,"logger":"http.handlers.reverse_proxy.health_checker.active","msg":"HTTP request failed","host":"app:8000","error":"Get \"http://app:8000/health\": dial tcp: lookup app on 127.0.0.11:53: server misbehaving"}
caddy-1  | {"level":"info","ts":1762977438.5007083,"msg":"autosaved config (load with --resume flag)","file":"/config/caddy/autosave.json"}
caddy-1  | {"level":"info","ts":1762977438.5007184,"msg":"serving initial configuration"}
caddy-1  | {"level":"info","ts":1762977438.5033162,"logger":"tls","msg":"cleaning storage unit","storage":"FileStorage:/data/caddy"}
caddy-1  | {"level":"info","ts":1762977438.504232,"logger":"tls","msg":"finished cleaning storage units"}
squid-1  | 2025/11/12 19:57:18| Service Name: squid
squid-1  | 2025/11/12 19:57:18| Process ID 1
squid-1  | 2025/11/12 19:57:18| Process Roles: master worker
squid-1  | 2025/11/12 19:57:18| With 1024 file descriptors available
squid-1  | 2025/11/12 19:57:18| Initializing IP Cache...
squid-1  | 2025/11/12 19:57:18| DNS IPv6 socket created at [::], FD 7
squid-1  | 2025/11/12 19:57:18| DNS IPv4 socket created at 0.0.0.0, FD 8
squid-1  | 2025/11/12 19:57:18| Adding nameserver 127.0.0.11 from /etc/resolv.conf
squid-1  | 2025/11/12 19:57:18| Adding domain . from /etc/resolv.conf
squid-1  | 2025/11/12 19:57:18| Adding ndots 1 from /etc/resolv.conf
squid-1  | 2025/11/12 19:57:18| Local cache digest enabled; rebuild/rewrite every 3600/3600 sec
squid-1  | 2025/11/12 19:57:18| Store logging disabled
squid-1  | 2025/11/12 19:57:18| Swap maxSize 0 + 262144 KB, estimated 20164 objects
squid-1  | 2025/11/12 19:57:18| Target number of buckets: 1008
squid-1  | 2025/11/12 19:57:18| Using 8192 Store buckets
squid-1  | 2025/11/12 19:57:18| Max Mem  size: 262144 KB
squid-1  | 2025/11/12 19:57:18| Max Swap size: 0 KB
squid-1  | 2025/11/12 19:57:18| Using Least Load store dir selection
squid-1  | 2025/11/12 19:57:18| Current Directory is /
squid-1  | 2025/11/12 19:57:18| Finished loading MIME types and icons.
squid-1  | 2025/11/12 19:57:18| HTCP Disabled.
squid-1  | 2025/11/12 19:57:18| Configuring Parent upstream1
squid-1  | 2025/11/12 19:57:18| Configuring Parent upstream2
squid-1  | 2025/11/12 19:57:18| Squid plugin modules loaded: 0
squid-1  | 2025/11/12 19:57:18| Adaptation support is off.
squid-1  | 2025/11/12 19:57:18| Accepting HTTP Socket connections at conn3 local=[::]:8888 remote=[::] FD 9 flags=9
squid-1  |     listening port: 8888
squid-1  | 2025/11/12 19:57:19| storeLateRelease: released 0 objects
app-3    | INFO:     172.18.0.2:35886 - "GET /health HTTP/1.1" 200 OK
caddy-1  | {"level":"info","ts":1762977468.5110834,"logger":"http.handlers.reverse_proxy.health_checker.active","msg":"host is up","host":"app:8000"}
app-3    | INFO:     127.0.0.1:43264 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43272 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43286 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:43296 - "GET /health HTTP/1.1" 200 OK
app-2    | 2025-11-12 19:58:00 - serpapi.orchestrator - INFO - Starting SerpApi fetch brand=whirlpool model=WRX735SDHZ03
app-2    | 2025-11-12 19:58:00 - serpapi.orchestrator - INFO - Executing 9 SerpApi querie(s) for brand=whirlpool model=WRX735SDHZ03
app-2    | 2025-11-12 19:58:00 - serpapi.orchestrator - INFO - SerpApi query 1/9: Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com
app-2    | 2025-11-12 19:58:00 - serpapi.client - INFO - Issuing SerpApi request query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com location=Austin, Texas, United States num=10
app-2    | 2025-11-12 19:58:00 - serpapi.client - INFO - SerpApi request succeeded query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com search_id=6914d9e4e6590eb0b9aa1313 organic_results=7
app-2    | 2025-11-12 19:58:00 - serpapi.orchestrator - INFO - Collecting candidates for query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com (search_id=6914d9e4e6590eb0b9aa1313)
app-2    | 2025-11-12 19:58:00 - serpapi.orchestrator - INFO - Collected 6 candidate(s) for query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com (search_id=6914d9e4e6590eb0b9aa1313)
app-2    | 2025-11-12 19:58:00 - serpapi.orchestrator - INFO - Attempting candidate url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf score=61 source=organic_results
app-2    | 2025-11-12 19:58:15 - serpapi.orchestrator - INFO - Downloading candidate url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf brand=whirlpool model=WRX735SDHZ03 referer=https://www.whirlpool.com/ read_timeout=45
app-3    | INFO:     172.18.0.2:43416 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:60168 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:60172 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:60180 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:60186 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.2:42814 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:59982 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:59994 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:60010 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:60016 - "GET /health HTTP/1.1" 200 OK
app-2    | 2025-11-12 19:59:00 - serpapi.orchestrator - WARNING - Download timed out while reading url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf host=www.whirlpool.com read_timeout=45 error=HTTPSConnectionPool(host='www.whirlpool.com', port=443): Read timed out. (read timeout=45)
app-2    | 2025-11-12 19:59:00 - serpapi.orchestrator - INFO - Attempting headless fallback download for url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf
app-2    | Using proxy server http://squid:8888
app-2    | 2025-11-12 19:59:00 - undetected_chromedriver.patcher - INFO - patching driver executable /usr/bin/chromedriver
app-2    | 2025-11-12 19:59:00 - uc - WARNING - could not detect version_main.therefore, we are assuming it is chrome 108 or higher
app-2    | 2025-11-12 19:59:01 - serpapi.headless - INFO - Headless download starting url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf referer=https://www.whirlpool.com/ download_dir=/app/headless-browser-scraper/temp/tmpwqxkt9p8
app-4    | INFO:     172.18.0.2:33464 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:48852 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:48866 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:48868 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:48878 - "GET /health HTTP/1.1" 200 OK
^Cexit status 130
root@documentation-scraper:~/documentation-scraper# docker compose down
[+] Running 7/7
 ✔ Container documentation-scraper-caddy-1    Removed                                                                                                                                                                                    10.2s
 ✔ Container documentation-scraper-app-4      Removed                                                                                                                                                                                     0.4s
 ✔ Container documentation-scraper-app-1      Removed                                                                                                                                                                                     0.4s
 ✔ Container documentation-scraper-app-2      Removed                                                                                                                                                                                    10.2s
 ✔ Container documentation-scraper-app-3      Removed                                                                                                                                                                                     0.4s
 ✔ Container documentation-scraper-squid-1    Removed                                                                                                                                                                                    10.1s
 ✔ Network documentation-scraper_app_network  Removed                                                                                                                                                                                     0.1s
root@documentation-scraper:~/documentation-scraper# a
a: command not found
root@documentation-scraper:~/documentation-scraper# git pull
Enter passphrase for key '/root/.ssh/scraper':
remote: Enumerating objects: 9, done.
remote: Counting objects: 100% (9/9), done.
remote: Compressing objects: 100% (1/1), done.
remote: Total 5 (delta 4), reused 5 (delta 4), pack-reused 0 (from 0)
Unpacking objects: 100% (5/5), 1020 bytes | 510.00 KiB/s, done.
From github.com:Homekeepr-Inc/documentation-scraper
   a039773..dc2a45f  main       -> origin/main
Updating a039773..dc2a45f
Fast-forward
 serpapi_scraper/headless_pdf_fetcher.py | 31 ++++++++++++++++++++++++++++++-
 serpapi_scraper/orchestrator.py         |  2 +-
 2 files changed, 31 insertions(+), 2 deletions(-)
root@documentation-scraper:~/documentation-scraper# docker compose up --build
Compose now can delegate build to bake for better performances
Just set COMPOSE_BAKE=true
[+] Building 2.7s (22/22) FINISHED                                                                                                                                                                                              docker:default
 => [squid internal] load build definition from Dockerfile                                                                                                                                                                                0.0s
 => => transferring dockerfile: 409B                                                                                                                                                                                                      0.0s
 => [squid internal] load metadata for docker.io/library/alpine:latest                                                                                                                                                                    0.1s
 => [squid internal] load .dockerignore                                                                                                                                                                                                   0.0s
 => => transferring context: 2B                                                                                                                                                                                                           0.0s
 => [squid 1/3] FROM docker.io/library/alpine:latest@sha256:4b7ce07002c69e8f3d704a9c5d6fd3053be500b7f1c69fc0d80990c2ad8dd412                                                                                                              0.0s
 => [squid internal] load build context                                                                                                                                                                                                   0.0s
 => => transferring context: 41B                                                                                                                                                                                                          0.0s
 => CACHED [squid 2/3] RUN apk add --no-cache squid gettext                                                                                                                                                                               0.0s
 => CACHED [squid 3/3] COPY squid.conf.template /etc/squid/squid.conf.template                                                                                                                                                            0.0s
 => [squid] exporting to image                                                                                                                                                                                                            0.0s
 => => exporting layers                                                                                                                                                                                                                   0.0s
 => => writing image sha256:1848d2aa68385cdae830adf372b846e335ddcd4fdc0ef26ee4f60df8437761b8                                                                                                                                              0.0s
 => => naming to docker.io/library/documentation-scraper-squid                                                                                                                                                                            0.0s
 => [squid] resolving provenance for metadata file                                                                                                                                                                                        0.0s
 => [app internal] load build definition from Dockerfile                                                                                                                                                                                  0.0s
 => => transferring dockerfile: 817B                                                                                                                                                                                                      0.0s
 => [app internal] load metadata for docker.io/selenium/standalone-chrome:latest                                                                                                                                                          0.1s
 => [app internal] load .dockerignore                                                                                                                                                                                                     0.0s
 => => transferring context: 2B                                                                                                                                                                                                           0.0s
 => [app 1/7] FROM docker.io/selenium/standalone-chrome:latest@sha256:529b51273aa7020b054fb0b49bbb87e3a68712c15d856f66e1b4a630edcd43c9                                                                                                    0.0s
 => [app internal] load build context                                                                                                                                                                                                     0.0s
 => => transferring context: 129.40kB                                                                                                                                                                                                     0.0s
 => CACHED [app 2/7] RUN apt-get update     && apt-get install -y curl gnupg lsb-release     && mkdir -p /etc/apt/keyrings     && apt-get update     && apt-get install -y python3.11     && apt-get clean     && rm -rf /var/lib/apt/li  0.0s
 => CACHED [app 3/7] WORKDIR /app                                                                                                                                                                                                         0.0s
 => CACHED [app 4/7] COPY requirements.txt .                                                                                                                                                                                              0.0s
 => CACHED [app 5/7] RUN python3 -m pip install --no-cache-dir -r requirements.txt                                                                                                                                                        0.0s
 => [app 6/7] COPY . .                                                                                                                                                                                                                    0.6s
 => [app 7/7] RUN mkdir -p headless-browser-scraper/temp                                                                                                                                                                                  0.2s
 => [app] exporting to image                                                                                                                                                                                                              1.5s
 => => exporting layers                                                                                                                                                                                                                   1.5s
 => => writing image sha256:7c8518f888c33021f2f408808c7bcea3de213e6db72ef89f73f87617a3eed41d                                                                                                                                              0.0s
 => => naming to docker.io/library/documentation-scraper-app                                                                                                                                                                              0.0s
 => [app] resolving provenance for metadata file                                                                                                                                                                                          0.0s
[+] Running 2/3
[+] Running 9/9                               Built                                                                                                                                                                                       0.0s
 ✔ app                                        Built                                                                                                                                                                                       0.0s
 ✔ squid                                      Built                                                                                                                                                                                       0.0s
 ✔ Network documentation-scraper_app_network  Created                                                                                                                                                                                     0.0s
 ✔ Container documentation-scraper-caddy-1    Created                                                                                                                                                                                     0.0s
 ✔ Container documentation-scraper-squid-1    Created                                                                                                                                                                                     0.0s
 ✔ Container documentation-scraper-app-4      Created                                                                                                                                                                                     0.0s
 ✔ Container documentation-scraper-app-2      Created                                                                                                                                                                                     0.0s
 ✔ Container documentation-scraper-app-3      Created                                                                                                                                                                                     0.0s
 ✔ Container documentation-scraper-app-1      Created                                                                                                                                                                                     0.0s
Attaching to app-1, app-2, app-3, app-4, caddy-1, squid-1
squid-1  | --- Generated squid.conf ---
squid-1  | # Squid configuration template for round-robin upstream proxy rotation
squid-1  |
squid-1  | http_port 8888
squid-1  |
squid-1  | # Upstream proxies (add more cache_peer lines as needed for additional upstreams)
squid-1  | cache_peer 192.210.251.164 parent 12323 0 proxy-only no-query no-digest login=14a79366c9697:6bbbc49dd3 round-robin name=upstream1
squid-1  | cache_peer 89.106.3.243 parent 12323 0 proxy-only no-query no-digest login=14a50ddfa322c:ae6e621d2a round-robin name=upstream2
squid-1  |
squid-1  | # Allow access to all upstream peers
squid-1  | cache_peer_access upstream1 allow all
squid-1  | cache_peer_access upstream2 allow all
squid-1  |
squid-1  | never_direct allow all
squid-1  |
squid-1  | # Access control
squid-1  | acl localnet src 127.0.0.1
squid-1  | acl localnet src 172.18.0.0/16
squid-1  | http_access allow localnet
squid-1  | http_access deny all
squid-1  |
squid-1  | # Logging
squid-1  | access_log none
squid-1  | cache_log none
squid-1  |
squid-1  | # Disable caching
squid-1  | cache deny all--- End Generated squid.conf ---
squid-1  | 2025/11/12 20:12:27| Processing Configuration File: /etc/squid/squid.conf (depth 0)
squid-1  | 2025/11/12 20:12:27| Created PID file (/var/run/squid.pid)
squid-1  | 2025/11/12 20:12:27| ERROR: Cannot open cache_log (none) for writing;
squid-1  |     fopen(3) error: (13) Permission denied
squid-1  | 2025/11/12 20:12:27| Current Directory is /
squid-1  | 2025/11/12 20:12:27| Starting Squid Cache version 6.12 for x86_64-alpine-linux-musl...
squid-1  | 2025/11/12 20:12:27| Service Name: squid
squid-1  | 2025/11/12 20:12:27| Process ID 1
squid-1  | 2025/11/12 20:12:27| Process Roles: master worker
squid-1  | 2025/11/12 20:12:27| With 1024 file descriptors available
squid-1  | 2025/11/12 20:12:27| Initializing IP Cache...
squid-1  | 2025/11/12 20:12:27| DNS IPv6 socket created at [::], FD 7
squid-1  | 2025/11/12 20:12:27| DNS IPv4 socket created at 0.0.0.0, FD 8
squid-1  | 2025/11/12 20:12:27| Adding nameserver 127.0.0.11 from /etc/resolv.conf
squid-1  | 2025/11/12 20:12:27| Adding domain . from /etc/resolv.conf
squid-1  | 2025/11/12 20:12:27| Adding ndots 1 from /etc/resolv.conf
squid-1  | 2025/11/12 20:12:27| Local cache digest enabled; rebuild/rewrite every 3600/3600 sec
squid-1  | 2025/11/12 20:12:27| Store logging disabled
squid-1  | 2025/11/12 20:12:27| Swap maxSize 0 + 262144 KB, estimated 20164 objects
squid-1  | 2025/11/12 20:12:27| Target number of buckets: 1008
squid-1  | 2025/11/12 20:12:27| Using 8192 Store buckets
squid-1  | 2025/11/12 20:12:27| Max Mem  size: 262144 KB
squid-1  | 2025/11/12 20:12:27| Max Swap size: 0 KB
squid-1  | 2025/11/12 20:12:27| Using Least Load store dir selection
squid-1  | 2025/11/12 20:12:27| Current Directory is /
squid-1  | 2025/11/12 20:12:27| Finished loading MIME types and icons.
squid-1  | 2025/11/12 20:12:27| HTCP Disabled.
squid-1  | 2025/11/12 20:12:27| Configuring Parent upstream1
squid-1  | 2025/11/12 20:12:27| Configuring Parent upstream2
squid-1  | 2025/11/12 20:12:27| Squid plugin modules loaded: 0
squid-1  | 2025/11/12 20:12:27| Adaptation support is off.
squid-1  | 2025/11/12 20:12:27| Accepting HTTP Socket connections at conn3 local=[::]:8888 remote=[::] FD 9 flags=9
squid-1  |     listening port: 8888
caddy-1  | {"level":"info","ts":1762978347.4724717,"msg":"maxprocs: Leaving GOMAXPROCS=4: CPU quota undefined"}
caddy-1  | {"level":"info","ts":1762978347.4736893,"msg":"GOMEMLIMIT is updated","package":"github.com/KimMachineGun/automemlimit/memlimit","GOMEMLIMIT":7314971443,"previous":9223372036854775807}
caddy-1  | {"level":"info","ts":1762978347.4737935,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
caddy-1  | {"level":"info","ts":1762978347.4773152,"msg":"adapted config to JSON","adapter":"caddyfile"}
caddy-1  | {"level":"warn","ts":1762978347.4774473,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":2}
caddy-1  | {"level":"info","ts":1762978347.4801724,"logger":"admin","msg":"admin endpoint started","address":"localhost:2019","enforce_origin":false,"origins":["//[::1]:2019","//127.0.0.1:2019","//localhost:2019"]}
caddy-1  | {"level":"warn","ts":1762978347.4807181,"logger":"tls","msg":"stapling OCSP","error":"no OCSP stapling for [cloudflare origin certificate *.homekeepr.co homekeepr.co]: no URL to issuing certificate"}
caddy-1  | {"level":"info","ts":1762978347.4808133,"logger":"http.auto_https","msg":"skipping automatic certificate management because one or more matching certificates are already loaded","domain":"api.homekeepr.co","server_name":"srv0"}
caddy-1  | {"level":"info","ts":1762978347.4808218,"logger":"http.auto_https","msg":"enabling automatic HTTP->HTTPS redirects","server_name":"srv0"}
caddy-1  | {"level":"info","ts":1762978347.4818354,"logger":"tls.cache.maintenance","msg":"started background certificate maintenance","cache":"0xc0007f8c00"}
caddy-1  | {"level":"info","ts":1762978347.4825134,"logger":"http","msg":"enabling HTTP/3 listener","addr":":443"}
caddy-1  | {"level":"info","ts":1762978347.4828084,"msg":"failed to sufficiently increase receive buffer size (was: 208 kiB, wanted: 7168 kiB, got: 416 kiB). See https://github.com/quic-go/quic-go/wiki/UDP-Buffer-Sizes for details."}
caddy-1  | {"level":"info","ts":1762978347.4831247,"logger":"http.log","msg":"server running","name":"srv0","protocols":["h1","h2","h3"]}
caddy-1  | {"level":"warn","ts":1762978347.483393,"logger":"http","msg":"HTTP/2 skipped because it requires TLS","network":"tcp","addr":":80"}
caddy-1  | {"level":"warn","ts":1762978347.4834328,"logger":"http","msg":"HTTP/3 skipped because it requires TLS","network":"tcp","addr":":80"}
caddy-1  | {"level":"info","ts":1762978347.4835563,"logger":"http.log","msg":"server running","name":"remaining_auto_https_redirects","protocols":["h1","h2","h3"]}
caddy-1  | {"level":"info","ts":1762978347.4926388,"msg":"autosaved config (load with --resume flag)","file":"/config/caddy/autosave.json"}
caddy-1  | {"level":"info","ts":1762978347.4932637,"msg":"serving initial configuration"}
caddy-1  | {"level":"info","ts":1762978347.4930928,"logger":"tls","msg":"cleaning storage unit","storage":"FileStorage:/data/caddy"}
caddy-1  | {"level":"info","ts":1762978347.4919796,"logger":"http.handlers.reverse_proxy.health_checker.active","msg":"HTTP request failed","host":"app:8000","error":"Get \"http://app:8000/health\": dial tcp: lookup app on 127.0.0.11:53: server misbehaving"}
caddy-1  | {"level":"info","ts":1762978347.4949634,"logger":"tls","msg":"finished cleaning storage units"}
app-2    | INFO:     Started server process [1]
app-2    | INFO:     Waiting for application startup.
app-2    | INFO:     Application startup complete.
app-2    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
squid-1  | 2025/11/12 20:12:28| storeLateRelease: released 0 objects
app-1    | INFO:     Started server process [1]
app-1    | INFO:     Waiting for application startup.
app-1    | INFO:     Application startup complete.
app-1    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-4    | INFO:     Started server process [1]
app-4    | INFO:     Waiting for application startup.
app-4    | INFO:     Application startup complete.
app-4    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-3    | INFO:     Started server process [1]
app-3    | INFO:     Waiting for application startup.
app-3    | INFO:     Application startup complete.
app-3    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-2    | INFO:     127.0.0.1:32772 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:32782 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:32786 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:32798 - "GET /health HTTP/1.1" 200 OK
caddy-1  | {"level":"error","ts":1762978358.2482638,"logger":"http.log.error.log0","msg":"no upstreams available","request":{"remote_ip":"172.68.174.166","remote_port":"10719","client_ip":"172.68.174.166","proto":"HTTP/2.0","method":"GET","host":"api.homekeepr.co","uri":"/scrape/whirlpool/WRX735SDHZ03","headers":{"Cf-Ipcountry":["US"],"X-Forwarded-For":["2600:1f14:1537:609:db4b:9dd6:4a68:1f58"],"Content-Type":["application/json"],"X-Homekeepr-Scraper":["noqdih-nafjYt-4dejqa--gg2ef-h3gszv-aarg"],"Accept-Encoding":["gzip, br"],"X-Forwarded-Proto":["https"],"Accept":["*/*"],"User-Agent":["Deno/2.1.4 (variant; SupabaseEdgeRuntime/1.69.22)"],"Accept-Language":["*"],"Cf-Visitor":["{\"scheme\":\"https\"}"],"Cf-Ray":["99d8af70cdf03416-PDX"],"Cdn-Loop":["cloudflare; loops=1"],"Cf-Connecting-Ip":["2600:1f14:1537:609:db4b:9dd6:4a68:1f58"]},"tls":{"resumed":false,"version":772,"cipher_suite":4865,"proto":"h2","server_name":"api.homekeepr.co"}},"duration":0.000104145,"status":503,"err_id":"c4w4y6se0","err_trace":"reverseproxy.(*Handler).proxyLoopIteration (reverseproxy.go:524)"}
app-2    | INFO:     172.18.0.3:53704 - "GET /health HTTP/1.1" 200 OK
caddy-1  | {"level":"info","ts":1762978377.4955075,"logger":"http.handlers.reverse_proxy.health_checker.active","msg":"host is up","host":"app:8000"}
app-2    | INFO:     127.0.0.1:38938 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:38948 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:38950 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:38952 - "GET /health HTTP/1.1" 200 OK
app-1    | 2025-11-12 20:13:23 - serpapi.orchestrator - INFO - Starting SerpApi fetch brand=whirlpool model=WRX735SDHZ03
app-1    | 2025-11-12 20:13:23 - serpapi.orchestrator - INFO - Executing 9 SerpApi querie(s) for brand=whirlpool model=WRX735SDHZ03
app-1    | 2025-11-12 20:13:23 - serpapi.orchestrator - INFO - SerpApi query 1/9: Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com
app-1    | 2025-11-12 20:13:23 - serpapi.client - INFO - Issuing SerpApi request query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com location=Austin, Texas, United States num=10
app-1    | 2025-11-12 20:13:25 - serpapi.client - INFO - SerpApi request succeeded query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com search_id=6914ea63ab28c66433482469 organic_results=7
app-1    | 2025-11-12 20:13:25 - serpapi.orchestrator - INFO - Collecting candidates for query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com (search_id=6914ea63ab28c66433482469)
app-1    | 2025-11-12 20:13:25 - serpapi.orchestrator - INFO - Collected 6 candidate(s) for query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com (search_id=6914ea63ab28c66433482469)
app-1    | 2025-11-12 20:13:25 - serpapi.orchestrator - INFO - Attempting candidate url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf score=61 source=organic_results
app-4    | INFO:     172.18.0.3:44834 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:51198 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:51206 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:51218 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:51230 - "GET /health HTTP/1.1" 200 OK
app-1    | 2025-11-12 20:13:40 - serpapi.orchestrator - INFO - Downloading candidate url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf brand=whirlpool model=WRX735SDHZ03 referer=https://www.whirlpool.com/ read_timeout=15
app-1    | 2025-11-12 20:13:55 - serpapi.orchestrator - WARNING - Download timed out while reading url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf host=www.whirlpool.com read_timeout=15 error=HTTPSConnectionPool(host='www.whirlpool.com', port=443): Read timed out. (read timeout=15)
app-1    | 2025-11-12 20:13:55 - serpapi.orchestrator - INFO - Attempting headless fallback download for url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf
app-1    | Using proxy server http://squid:8888
app-1    | 2025-11-12 20:13:55 - undetected_chromedriver.patcher - INFO - patching driver executable /usr/bin/chromedriver
app-1    | 2025-11-12 20:13:55 - uc - WARNING - could not detect version_main.therefore, we are assuming it is chrome 108 or higher
app-1    | 2025-11-12 20:13:55 - serpapi.headless - INFO - Headless download starting url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf referer=https://www.whirlpool.com/ download_dir=/app/headless-browser-scraper/temp/tmpramusyq7
app-1    | INFO:     172.18.0.3:41590 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:48826 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:48832 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:48848 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:48854 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:37002 - "GET /health HTTP/1.1" 200 OK
app-1    | 2025-11-12 20:14:31 - serpapi.headless - WARNING - Headless download produced no PDF url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf
app-1    | 2025-11-12 20:14:31 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf brand=whirlpool model=WRX735SDHZ03
app-1    | 2025-11-12 20:14:31 - serpapi.orchestrator - INFO - Attempting candidate url=https://www.whirlpool.com/content/dam/global/documents/201910/owners-manual-w11304737-revb.pdf score=60 source=organic_results
app-2    | INFO:     127.0.0.1:39256 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:39258 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:39266 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:39280 - "GET /health HTTP/1.1" 200 OK
Gracefully stopping... (press Ctrl+C again to force)
[+] Stopping 6/6
 ✔ Container documentation-scraper-app-3    Stopped                                                                                                                                                                                       0.4s
 ✔ Container documentation-scraper-app-1    Stopped                                                                                                                                                                                       0.8s
 ✔ Container documentation-scraper-caddy-1  Stopped                                                                                                                                                                                       0.7s
 ✔ Container documentation-scraper-app-2    Stopped                                                                                                                                                                                       0.5s
 ✔ Container documentation-scraper-app-4    Stopped                                                                                                                                                                                       0.4s
 ✔ Container documentation-scraper-squid-1  Stopped                                                                                                                                                                                       0.0s
exit status 130
root@documentation-scraper:~/documentation-scraper# ^C
root@documentation-scraper:~/documentation-scraper# ^C
root@documentation-scraper:~/documentation-scraper# git pull
Enter passphrase for key '/root/.ssh/scraper':
remote: Enumerating objects: 7, done.
remote: Counting objects: 100% (7/7), done.
remote: Compressing objects: 100% (2/2), done.
remote: Total 4 (delta 2), reused 4 (delta 2), pack-reused 0 (from 0)
Unpacking objects: 100% (4/4), 2.40 KiB | 2.40 MiB/s, done.
From github.com:Homekeepr-Inc/documentation-scraper
   dc2a45f..0a14f1f  main       -> origin/main
Updating dc2a45f..0a14f1f
Fast-forward
 serpapi_scraper/headless_pdf_fetcher.py | 292 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-----------------------------------------------------------------------------------------------------------
 1 file changed, 129 insertions(+), 163 deletions(-)
root@documentation-scraper:~/documentation-scraper# docker compose up --build -d
Compose now can delegate build to bake for better performances
Just set COMPOSE_BAKE=true
[+] Building 2.3s (22/22) FINISHED                                                                                                                                                                                              docker:default
 => [squid internal] load build definition from Dockerfile                                                                                                                                                                                0.0s
 => => transferring dockerfile: 409B                                                                                                                                                                                                      0.0s
 => [squid internal] load metadata for docker.io/library/alpine:latest                                                                                                                                                                    0.1s
 => [squid internal] load .dockerignore                                                                                                                                                                                                   0.0s
 => => transferring context: 2B                                                                                                                                                                                                           0.0s
 => [squid 1/3] FROM docker.io/library/alpine:latest@sha256:4b7ce07002c69e8f3d704a9c5d6fd3053be500b7f1c69fc0d80990c2ad8dd412                                                                                                              0.0s
 => [squid internal] load build context                                                                                                                                                                                                   0.0s
 => => transferring context: 41B                                                                                                                                                                                                          0.0s
 => CACHED [squid 2/3] RUN apk add --no-cache squid gettext                                                                                                                                                                               0.0s
 => CACHED [squid 3/3] COPY squid.conf.template /etc/squid/squid.conf.template                                                                                                                                                            0.0s
 => [squid] exporting to image                                                                                                                                                                                                            0.0s
 => => exporting layers                                                                                                                                                                                                                   0.0s
 => => writing image sha256:1848d2aa68385cdae830adf372b846e335ddcd4fdc0ef26ee4f60df8437761b8                                                                                                                                              0.0s
 => => naming to docker.io/library/documentation-scraper-squid                                                                                                                                                                            0.0s
 => [squid] resolving provenance for metadata file                                                                                                                                                                                        0.0s
 => [app internal] load build definition from Dockerfile                                                                                                                                                                                  0.0s
 => => transferring dockerfile: 817B                                                                                                                                                                                                      0.0s
 => [app internal] load metadata for docker.io/selenium/standalone-chrome:latest                                                                                                                                                          0.1s
 => [app internal] load .dockerignore                                                                                                                                                                                                     0.0s
 => => transferring context: 2B                                                                                                                                                                                                           0.0s
 => [app 1/7] FROM docker.io/selenium/standalone-chrome:latest@sha256:529b51273aa7020b054fb0b49bbb87e3a68712c15d856f66e1b4a630edcd43c9                                                                                                    0.0s
 => [app internal] load build context                                                                                                                                                                                                     0.1s
 => => transferring context: 106.17kB                                                                                                                                                                                                     0.0s
 => CACHED [app 2/7] RUN apt-get update     && apt-get install -y curl gnupg lsb-release     && mkdir -p /etc/apt/keyrings     && apt-get update     && apt-get install -y python3.11     && apt-get clean     && rm -rf /var/lib/apt/li  0.0s
 => CACHED [app 3/7] WORKDIR /app                                                                                                                                                                                                         0.0s
 => CACHED [app 4/7] COPY requirements.txt .                                                                                                                                                                                              0.0s
 => CACHED [app 5/7] RUN python3 -m pip install --no-cache-dir -r requirements.txt                                                                                                                                                        0.0s
 => [app 6/7] COPY . .                                                                                                                                                                                                                    0.6s
 => [app 7/7] RUN mkdir -p headless-browser-scraper/temp                                                                                                                                                                                  0.2s
 => [app] exporting to image                                                                                                                                                                                                              1.2s
 => => exporting layers                                                                                                                                                                                                                   1.1s
 => => writing image sha256:063e59dc670541e7e1623abe0c1ffc6487fe4faa9c43d1a1eddc8f300bdf0238                                                                                                                                              0.0s
 => => naming to docker.io/library/documentation-scraper-app                                                                                                                                                                              0.0s
 => [app] resolving provenance for metadata file                                                                                                                                                                                          0.0s
WARN[0002] Found orphan containers ([documentation-scraper-db-init-1]) for this project. If you removed or renamed this service in your compose file, you can run this command with the --remove-orphans flag to clean it up.
[+] Running 8/8
 ✔ app                                      Built                                                                                                                                                                                         0.0s
 ✔ squid                                    Built                                                                                                                                                                                         0.0s
 ✔ Container documentation-scraper-squid-1  Started                                                                                                                                                                                       0.2s
 ✔ Container documentation-scraper-caddy-1  Started                                                                                                                                                                                       0.2s
 ✔ Container documentation-scraper-app-2    Started                                                                                                                                                                                       0.4s
 ✔ Container documentation-scraper-app-1    Started                                                                                                                                                                                       0.5s
 ✔ Container documentation-scraper-app-4    Started                                                                                                                                                                                       0.8s
 ✔ Container documentation-scraper-app-3    Started                                                                                                                                                                                       0.6s
root@documentation-scraper:~/documentation-scraper# docke rps
Command 'docke' not found, did you mean:
  command 'docker' from deb docker.io (28.2.2-0ubuntu1~24.04.1)
  command 'docker' from deb podman-docker (4.9.3+ds1-1ubuntu0.2)
Try: apt install <deb name>
root@documentation-scraper:~/documentation-scraper# docker ps
CONTAINER ID   IMAGE                       COMMAND                  CREATED         STATUS                            PORTS                                                                NAMES
4bb9c521e98f   documentation-scraper-app   "uvicorn app.main:ap…"   5 seconds ago   Up 4 seconds (health: starting)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-2
088fa9e949ee   documentation-scraper-app   "uvicorn app.main:ap…"   5 seconds ago   Up 4 seconds (health: starting)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-1
756a652c61b4   documentation-scraper-app   "uvicorn app.main:ap…"   5 seconds ago   Up 4 seconds (health: starting)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-3
52e13cc04c31   documentation-scraper-app   "uvicorn app.main:ap…"   5 seconds ago   Up 4 seconds (health: starting)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-4
f2e5f97f4f8c   caddy:2                     "caddy run --config …"   2 hours ago     Up 4 seconds                      80/tcp, 2019/tcp, 443/udp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp   documentation-scraper-caddy-1
root@documentation-scraper:~/documentation-scraper# docker ps
CONTAINER ID   IMAGE                       COMMAND                  CREATED          STATUS                    PORTS                                                                NAMES
4bb9c521e98f   documentation-scraper-app   "uvicorn app.main:ap…"   13 seconds ago   Up 12 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-2
088fa9e949ee   documentation-scraper-app   "uvicorn app.main:ap…"   13 seconds ago   Up 12 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-1
756a652c61b4   documentation-scraper-app   "uvicorn app.main:ap…"   13 seconds ago   Up 12 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-3
52e13cc04c31   documentation-scraper-app   "uvicorn app.main:ap…"   13 seconds ago   Up 12 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-4
f2e5f97f4f8c   caddy:2                     "caddy run --config …"   2 hours ago      Up 13 seconds             80/tcp, 2019/tcp, 443/udp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp   documentation-scraper-caddy-1
root@documentation-scraper:~/documentation-scraper# docker compose up -d
WARN[0000] Found orphan containers ([documentation-scraper-db-init-1]) for this project. If you removed or renamed this service in your compose file, you can run this command with the --remove-orphans flag to clean it up.
[+] Running 6/6
 ✔ Container documentation-scraper-caddy-1  Running                                                                                                                                                                                       0.0s
 ✔ Container documentation-scraper-squid-1  Started                                                                                                                                                                                       0.1s
 ✔ Container documentation-scraper-app-1    Running                                                                                                                                                                                       0.0s
 ✔ Container documentation-scraper-app-2    Running                                                                                                                                                                                       0.0s
 ✔ Container documentation-scraper-app-3    Running                                                                                                                                                                                       0.0s
 ✔ Container documentation-scraper-app-4    Running                                                                                                                                                                                       0.0s
root@documentation-scraper:~/documentation-scraper# docker ps
CONTAINER ID   IMAGE                       COMMAND                  CREATED          STATUS                    PORTS                                                                NAMES
4bb9c521e98f   documentation-scraper-app   "uvicorn app.main:ap…"   21 seconds ago   Up 20 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-2
088fa9e949ee   documentation-scraper-app   "uvicorn app.main:ap…"   21 seconds ago   Up 20 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-1
756a652c61b4   documentation-scraper-app   "uvicorn app.main:ap…"   21 seconds ago   Up 20 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-3
52e13cc04c31   documentation-scraper-app   "uvicorn app.main:ap…"   21 seconds ago   Up 19 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-4
f2e5f97f4f8c   caddy:2                     "caddy run --config …"   2 hours ago      Up 20 seconds             80/tcp, 2019/tcp, 443/udp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp   documentation-scraper-caddy-1
root@documentation-scraper:~/documentation-scraper# docker compose up squid -d
WARN[0000] Found orphan containers ([documentation-scraper-db-init-1]) for this project. If you removed or renamed this service in your compose file, you can run this command with the --remove-orphans flag to clean it up.
[+] Running 1/1
 ✔ Container documentation-scraper-squid-1  Started                                                                                                                                                                                       0.1s
root@documentation-scraper:~/documentation-scraper# docler ps
Command 'docler' not found, did you mean:
  command 'docker' from snap docker (28.4.0)
  command 'docker' from snap docker (28.1.1+1)
  command 'docker' from deb docker.io (28.2.2-0ubuntu1~24.04.1)
  command 'docker' from deb podman-docker (4.9.3+ds1-1ubuntu0.2)
See 'snap info <snapname>' for additional versions.
root@documentation-scraper:~/documentation-scraper# docker ps
CONTAINER ID   IMAGE                       COMMAND                  CREATED          STATUS                    PORTS                                                                NAMES
4bb9c521e98f   documentation-scraper-app   "uvicorn app.main:ap…"   33 seconds ago   Up 32 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-2
088fa9e949ee   documentation-scraper-app   "uvicorn app.main:ap…"   33 seconds ago   Up 32 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-1
756a652c61b4   documentation-scraper-app   "uvicorn app.main:ap…"   33 seconds ago   Up 32 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-3
52e13cc04c31   documentation-scraper-app   "uvicorn app.main:ap…"   33 seconds ago   Up 31 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-4
f2e5f97f4f8c   caddy:2                     "caddy run --config …"   2 hours ago      Up 32 seconds             80/tcp, 2019/tcp, 443/udp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp   documentation-scraper-caddy-1
root@documentation-scraper:~/documentation-scraper# docker compose logs squid
squid-1  | --- Generated squid.conf ---
squid-1  | # Squid configuration template for round-robin upstream proxy rotation
squid-1  |
squid-1  | http_port 8888
squid-1  |
squid-1  | # Upstream proxies (add more cache_peer lines as needed for additional upstreams)
squid-1  | cache_peer 192.210.251.164 parent 12323 0 proxy-only no-query no-digest login=14a79366c9697:6bbbc49dd3 round-robin name=upstream1
squid-1  | cache_peer 89.106.3.243 parent 12323 0 proxy-only no-query no-digest login=14a50ddfa322c:ae6e621d2a round-robin name=upstream2
squid-1  |
squid-1  | # Allow access to all upstream peers
squid-1  | cache_peer_access upstream1 allow all
squid-1  | cache_peer_access upstream2 allow all
squid-1  |
squid-1  | never_direct allow all
squid-1  |
squid-1  | # Access control
squid-1  | acl localnet src 127.0.0.1
squid-1  | acl localnet src 172.18.0.0/16
squid-1  | http_access allow localnet
squid-1  | http_access deny all
squid-1  |
squid-1  | # Logging
squid-1  | access_log none
squid-1  | cache_log none
squid-1  |
squid-1  | # Disable caching
squid-1  | cache deny all--- End Generated squid.conf ---
squid-1  | 2025/11/12 20:12:27| Processing Configuration File: /etc/squid/squid.conf (depth 0)
squid-1  | 2025/11/12 20:12:27| Created PID file (/var/run/squid.pid)
squid-1  | 2025/11/12 20:12:27| ERROR: Cannot open cache_log (none) for writing;
squid-1  |     fopen(3) error: (13) Permission denied
squid-1  | 2025/11/12 20:12:27| Current Directory is /
squid-1  | 2025/11/12 20:12:27| Starting Squid Cache version 6.12 for x86_64-alpine-linux-musl...
squid-1  | 2025/11/12 20:12:27| Service Name: squid
squid-1  | 2025/11/12 20:12:27| Process ID 1
squid-1  | 2025/11/12 20:12:27| Process Roles: master worker
squid-1  | 2025/11/12 20:12:27| With 1024 file descriptors available
squid-1  | 2025/11/12 20:12:27| Initializing IP Cache...
squid-1  | 2025/11/12 20:12:27| DNS IPv6 socket created at [::], FD 7
squid-1  | 2025/11/12 20:12:27| DNS IPv4 socket created at 0.0.0.0, FD 8
squid-1  | 2025/11/12 20:12:27| Adding nameserver 127.0.0.11 from /etc/resolv.conf
squid-1  | 2025/11/12 20:12:27| Adding domain . from /etc/resolv.conf
squid-1  | 2025/11/12 20:12:27| Adding ndots 1 from /etc/resolv.conf
squid-1  | 2025/11/12 20:12:27| Local cache digest enabled; rebuild/rewrite every 3600/3600 sec
squid-1  | 2025/11/12 20:12:27| Store logging disabled
squid-1  | 2025/11/12 20:12:27| Swap maxSize 0 + 262144 KB, estimated 20164 objects
squid-1  | 2025/11/12 20:12:27| Target number of buckets: 1008
squid-1  | 2025/11/12 20:12:27| Using 8192 Store buckets
squid-1  | 2025/11/12 20:12:27| Max Mem  size: 262144 KB
squid-1  | 2025/11/12 20:12:27| Max Swap size: 0 KB
squid-1  | 2025/11/12 20:12:27| Using Least Load store dir selection
squid-1  | 2025/11/12 20:12:27| Current Directory is /
squid-1  | 2025/11/12 20:12:27| Finished loading MIME types and icons.
squid-1  | 2025/11/12 20:12:27| HTCP Disabled.
squid-1  | 2025/11/12 20:12:27| Configuring Parent upstream1
squid-1  | 2025/11/12 20:12:27| Configuring Parent upstream2
squid-1  | 2025/11/12 20:12:27| Squid plugin modules loaded: 0
squid-1  | 2025/11/12 20:12:27| Adaptation support is off.
squid-1  | 2025/11/12 20:12:27| Accepting HTTP Socket connections at conn3 local=[::]:8888 remote=[::] FD 9 flags=9
squid-1  |     listening port: 8888
squid-1  | 2025/11/12 20:12:28| storeLateRelease: released 0 objects
squid-1  | --- Generated squid.conf ---
squid-1  | # Squid configuration template for round-robin upstream proxy rotation
squid-1  |
squid-1  | http_port 8888
squid-1  |
squid-1  | # Upstream proxies (add more cache_peer lines as needed for additional upstreams)
squid-1  | cache_peer 192.210.251.164 parent 12323 0 proxy-only no-query no-digest login=14a79366c9697:6bbbc49dd3 round-robin name=upstream1
squid-1  | cache_peer 89.106.3.243 parent 12323 0 proxy-only no-query no-digest login=14a50ddfa322c:ae6e621d2a round-robin name=upstream2
squid-1  |
squid-1  | # Allow access to all upstream peers
squid-1  | cache_peer_access upstream1 allow all
squid-1  | cache_peer_access upstream2 allow all
squid-1  |
squid-1  | never_direct allow all
squid-1  |
squid-1  | # Access control
squid-1  | acl localnet src 127.0.0.1
squid-1  | acl localnet src 172.18.0.0/16
squid-1  | http_access allow localnet
squid-1  | http_access deny all
squid-1  |
squid-1  | # Logging
squid-1  | access_log none
squid-1  | cache_log none
squid-1  |
squid-1  | # Disable caching
squid-1  | cache deny all--- End Generated squid.conf ---
squid-1  | 2025/11/12 22:04:06| Processing Configuration File: /etc/squid/squid.conf (depth 0)
squid-1  | 2025/11/12 22:04:06| FATAL: Squid is already running: Found fresh instance PID file (/var/run/squid.pid) with PID 1
squid-1  |     exception location: Instance.cc(122) ThrowIfAlreadyRunningWith
squid-1  | --- Generated squid.conf ---
squid-1  | # Squid configuration template for round-robin upstream proxy rotation
squid-1  |
squid-1  | http_port 8888
squid-1  |
squid-1  | # Upstream proxies (add more cache_peer lines as needed for additional upstreams)
squid-1  | cache_peer 192.210.251.164 parent 12323 0 proxy-only no-query no-digest login=14a79366c9697:6bbbc49dd3 round-robin name=upstream1
squid-1  | cache_peer 89.106.3.243 parent 12323 0 proxy-only no-query no-digest login=14a50ddfa322c:ae6e621d2a round-robin name=upstream2
squid-1  |
squid-1  | # Allow access to all upstream peers
squid-1  | cache_peer_access upstream1 allow all
squid-1  | cache_peer_access upstream2 allow all
squid-1  |
squid-1  | never_direct allow all
squid-1  |
squid-1  | # Access control
squid-1  | acl localnet src 127.0.0.1
squid-1  | acl localnet src 172.18.0.0/16
squid-1  | http_access allow localnet
squid-1  | http_access deny all
squid-1  |
squid-1  | # Logging
squid-1  | access_log none
squid-1  | cache_log none
squid-1  |
squid-1  | # Disable caching
squid-1  | cache deny all--- End Generated squid.conf ---
squid-1  | 2025/11/12 22:04:24| Processing Configuration File: /etc/squid/squid.conf (depth 0)
squid-1  | 2025/11/12 22:04:24| FATAL: Squid is already running: Found fresh instance PID file (/var/run/squid.pid) with PID 1
squid-1  |     exception location: Instance.cc(122) ThrowIfAlreadyRunningWith
squid-1  | --- Generated squid.conf ---
squid-1  | # Squid configuration template for round-robin upstream proxy rotation
squid-1  |
squid-1  | http_port 8888
squid-1  |
squid-1  | # Upstream proxies (add more cache_peer lines as needed for additional upstreams)
squid-1  | cache_peer 192.210.251.164 parent 12323 0 proxy-only no-query no-digest login=14a79366c9697:6bbbc49dd3 round-robin name=upstream1
squid-1  | cache_peer 89.106.3.243 parent 12323 0 proxy-only no-query no-digest login=14a50ddfa322c:ae6e621d2a round-robin name=upstream2
squid-1  |
squid-1  | # Allow access to all upstream peers
squid-1  | cache_peer_access upstream1 allow all
squid-1  | cache_peer_access upstream2 allow all
squid-1  |
squid-1  | never_direct allow all
squid-1  |
squid-1  | # Access control
squid-1  | acl localnet src 127.0.0.1
squid-1  | acl localnet src 172.18.0.0/16
squid-1  | http_access allow localnet
squid-1  | http_access deny all
squid-1  |
squid-1  | # Logging
squid-1  | access_log none
squid-1  | cache_log none
squid-1  |
squid-1  | # Disable caching
squid-1  | cache deny all--- End Generated squid.conf ---
squid-1  | 2025/11/12 22:04:33| Processing Configuration File: /etc/squid/squid.conf (depth 0)
squid-1  | 2025/11/12 22:04:33| FATAL: Squid is already running: Found fresh instance PID file (/var/run/squid.pid) with PID 1
squid-1  |     exception location: Instance.cc(122) ThrowIfAlreadyRunningWith
root@documentation-scraper:~/documentation-scraper# docker compose down squid
[+] Running 2/2
 ✔ Container documentation-scraper-squid-1    Removed                                                                                                                                                                                     0.0s
 ! Network documentation-scraper_app_network  Resource is still in use                                                                                                                                                                    0.0s
root@documentation-scraper:~/documentation-scraper# docker compose down squid
[+] Running 1/1
 ! Network documentation-scraper_app_network  Resource is still in use                                                                                                                                                                    0.0s
root@documentation-scraper:~/documentation-scraper# docker compose up squid -d
WARN[0000] Found orphan containers ([documentation-scraper-db-init-1]) for this project. If you removed or renamed this service in your compose file, you can run this command with the --remove-orphans flag to clean it up.
[+] Running 1/1
 ✔ Container documentation-scraper-squid-1  Started                                                                                                                                                                                       0.2s
root@documentation-scraper:~/documentation-scraper# docker compose logs squid
squid-1  | --- Generated squid.conf ---
squid-1  | # Squid configuration template for round-robin upstream proxy rotation
squid-1  |
squid-1  | http_port 8888
squid-1  |
squid-1  | # Upstream proxies (add more cache_peer lines as needed for additional upstreams)
squid-1  | cache_peer 192.210.251.164 parent 12323 0 proxy-only no-query no-digest login=14a79366c9697:6bbbc49dd3 round-robin name=upstream1
squid-1  | cache_peer 89.106.3.243 parent 12323 0 proxy-only no-query no-digest login=14a50ddfa322c:ae6e621d2a round-robin name=upstream2
squid-1  |
squid-1  | # Allow access to all upstream peers
squid-1  | cache_peer_access upstream1 allow all
squid-1  | cache_peer_access upstream2 allow all
squid-1  |
squid-1  | never_direct allow all
squid-1  |
squid-1  | # Access control
squid-1  | acl localnet src 127.0.0.1
squid-1  | acl localnet src 172.18.0.0/16
squid-1  | http_access allow localnet
squid-1  | http_access deny all
squid-1  |
squid-1  | # Logging
squid-1  | access_log none
squid-1  | cache_log none
squid-1  |
squid-1  | # Disable caching
squid-1  | cache deny all--- End Generated squid.conf ---
squid-1  | 2025/11/12 22:05:00| Processing Configuration File: /etc/squid/squid.conf (depth 0)
squid-1  | 2025/11/12 22:05:00| Created PID file (/var/run/squid.pid)
squid-1  | 2025/11/12 22:05:00| ERROR: Cannot open cache_log (none) for writing;
squid-1  |     fopen(3) error: (13) Permission denied
squid-1  | 2025/11/12 22:05:00| Current Directory is /
squid-1  | 2025/11/12 22:05:00| Starting Squid Cache version 6.12 for x86_64-alpine-linux-musl...
squid-1  | 2025/11/12 22:05:00| Service Name: squid
squid-1  | 2025/11/12 22:05:00| Process ID 1
squid-1  | 2025/11/12 22:05:00| Process Roles: master worker
squid-1  | 2025/11/12 22:05:00| With 1024 file descriptors available
squid-1  | 2025/11/12 22:05:00| Initializing IP Cache...
squid-1  | 2025/11/12 22:05:00| DNS IPv6 socket created at [::], FD 7
squid-1  | 2025/11/12 22:05:00| DNS IPv4 socket created at 0.0.0.0, FD 8
squid-1  | 2025/11/12 22:05:00| Adding nameserver 127.0.0.11 from /etc/resolv.conf
squid-1  | 2025/11/12 22:05:00| Adding domain . from /etc/resolv.conf
squid-1  | 2025/11/12 22:05:00| Adding ndots 1 from /etc/resolv.conf
squid-1  | 2025/11/12 22:05:00| Local cache digest enabled; rebuild/rewrite every 3600/3600 sec
squid-1  | 2025/11/12 22:05:00| Store logging disabled
squid-1  | 2025/11/12 22:05:00| Swap maxSize 0 + 262144 KB, estimated 20164 objects
squid-1  | 2025/11/12 22:05:00| Target number of buckets: 1008
squid-1  | 2025/11/12 22:05:00| Using 8192 Store buckets
squid-1  | 2025/11/12 22:05:00| Max Mem  size: 262144 KB
squid-1  | 2025/11/12 22:05:00| Max Swap size: 0 KB
squid-1  | 2025/11/12 22:05:00| Using Least Load store dir selection
squid-1  | 2025/11/12 22:05:00| Current Directory is /
squid-1  | 2025/11/12 22:05:00| Finished loading MIME types and icons.
squid-1  | 2025/11/12 22:05:00| HTCP Disabled.
squid-1  | 2025/11/12 22:05:00| Configuring Parent upstream1
squid-1  | 2025/11/12 22:05:00| Configuring Parent upstream2
squid-1  | 2025/11/12 22:05:00| Squid plugin modules loaded: 0
squid-1  | 2025/11/12 22:05:00| Adaptation support is off.
squid-1  | 2025/11/12 22:05:00| Accepting HTTP Socket connections at conn3 local=[::]:8888 remote=[::] FD 9 flags=9
squid-1  |     listening port: 8888
squid-1  | 2025/11/12 22:05:01| storeLateRelease: released 0 objects
root@documentation-scraper:~/documentation-scraper# docker ps
CONTAINER ID   IMAGE                         COMMAND                  CREATED          STATUS                    PORTS                                                                NAMES
030d6e449c55   documentation-scraper-squid   "/bin/sh -c 'envsubs…"   4 seconds ago    Up 4 seconds              8888/tcp                                                             documentation-scraper-squid-1
4bb9c521e98f   documentation-scraper-app     "uvicorn app.main:ap…"   58 seconds ago   Up 58 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-2
088fa9e949ee   documentation-scraper-app     "uvicorn app.main:ap…"   58 seconds ago   Up 58 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-1
756a652c61b4   documentation-scraper-app     "uvicorn app.main:ap…"   58 seconds ago   Up 57 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-3
52e13cc04c31   documentation-scraper-app     "uvicorn app.main:ap…"   58 seconds ago   Up 57 seconds (healthy)   4444/tcp, 5900/tcp, 8000/tcp, 9000/tcp                               documentation-scraper-app-4
f2e5f97f4f8c   caddy:2                       "caddy run --config …"   2 hours ago      Up 58 seconds             80/tcp, 2019/tcp, 443/udp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp   documentation-scraper-caddy-1
root@documentation-scraper:~/documentation-scraper# docker compose logs -f
caddy-1  | {"level":"info","ts":1762978347.4724717,"msg":"maxprocs: Leaving GOMAXPROCS=4: CPU quota undefined"}
caddy-1  | {"level":"info","ts":1762978347.4736893,"msg":"GOMEMLIMIT is updated","package":"github.com/KimMachineGun/automemlimit/memlimit","GOMEMLIMIT":7314971443,"previous":9223372036854775807}
caddy-1  | {"level":"info","ts":1762978347.4737935,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
caddy-1  | {"level":"info","ts":1762978347.4773152,"msg":"adapted config to JSON","adapter":"caddyfile"}
caddy-1  | {"level":"warn","ts":1762978347.4774473,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":2}
caddy-1  | {"level":"info","ts":1762978347.4801724,"logger":"admin","msg":"admin endpoint started","address":"localhost:2019","enforce_origin":false,"origins":["//[::1]:2019","//127.0.0.1:2019","//localhost:2019"]}
caddy-1  | {"level":"warn","ts":1762978347.4807181,"logger":"tls","msg":"stapling OCSP","error":"no OCSP stapling for [cloudflare origin certificate *.homekeepr.co homekeepr.co]: no URL to issuing certificate"}
caddy-1  | {"level":"info","ts":1762978347.4808133,"logger":"http.auto_https","msg":"skipping automatic certificate management because one or more matching certificates are already loaded","domain":"api.homekeepr.co","server_name":"srv0"}
caddy-1  | {"level":"info","ts":1762978347.4808218,"logger":"http.auto_https","msg":"enabling automatic HTTP->HTTPS redirects","server_name":"srv0"}
caddy-1  | {"level":"info","ts":1762978347.4818354,"logger":"tls.cache.maintenance","msg":"started background certificate maintenance","cache":"0xc0007f8c00"}
caddy-1  | {"level":"info","ts":1762978347.4825134,"logger":"http","msg":"enabling HTTP/3 listener","addr":":443"}
caddy-1  | {"level":"info","ts":1762978347.4828084,"msg":"failed to sufficiently increase receive buffer size (was: 208 kiB, wanted: 7168 kiB, got: 416 kiB). See https://github.com/quic-go/quic-go/wiki/UDP-Buffer-Sizes for details."}
caddy-1  | {"level":"info","ts":1762978347.4831247,"logger":"http.log","msg":"server running","name":"srv0","protocols":["h1","h2","h3"]}
caddy-1  | {"level":"warn","ts":1762978347.483393,"logger":"http","msg":"HTTP/2 skipped because it requires TLS","network":"tcp","addr":":80"}
caddy-1  | {"level":"warn","ts":1762978347.4834328,"logger":"http","msg":"HTTP/3 skipped because it requires TLS","network":"tcp","addr":":80"}
caddy-1  | {"level":"info","ts":1762978347.4835563,"logger":"http.log","msg":"server running","name":"remaining_auto_https_redirects","protocols":["h1","h2","h3"]}
caddy-1  | {"level":"info","ts":1762978347.4926388,"msg":"autosaved config (load with --resume flag)","file":"/config/caddy/autosave.json"}
caddy-1  | {"level":"info","ts":1762978347.4932637,"msg":"serving initial configuration"}
caddy-1  | {"level":"info","ts":1762978347.4930928,"logger":"tls","msg":"cleaning storage unit","storage":"FileStorage:/data/caddy"}
caddy-1  | {"level":"info","ts":1762978347.4919796,"logger":"http.handlers.reverse_proxy.health_checker.active","msg":"HTTP request failed","host":"app:8000","error":"Get \"http://app:8000/health\": dial tcp: lookup app on 127.0.0.11:53: server misbehaving"}
caddy-1  | {"level":"info","ts":1762978347.4949634,"logger":"tls","msg":"finished cleaning storage units"}
caddy-1  | {"level":"error","ts":1762978358.2482638,"logger":"http.log.error.log0","msg":"no upstreams available","request":{"remote_ip":"172.68.174.166","remote_port":"10719","client_ip":"172.68.174.166","proto":"HTTP/2.0","method":"GET","host":"api.homekeepr.co","uri":"/scrape/whirlpool/WRX735SDHZ03","headers":{"Cf-Ipcountry":["US"],"X-Forwarded-For":["2600:1f14:1537:609:db4b:9dd6:4a68:1f58"],"Content-Type":["application/json"],"X-Homekeepr-Scraper":["noqdih-nafjYt-4dejqa--gg2ef-h3gszv-aarg"],"Accept-Encoding":["gzip, br"],"X-Forwarded-Proto":["https"],"Accept":["*/*"],"User-Agent":["Deno/2.1.4 (variant; SupabaseEdgeRuntime/1.69.22)"],"Accept-Language":["*"],"Cf-Visitor":["{\"scheme\":\"https\"}"],"Cf-Ray":["99d8af70cdf03416-PDX"],"Cdn-Loop":["cloudflare; loops=1"],"Cf-Connecting-Ip":["2600:1f14:1537:609:db4b:9dd6:4a68:1f58"]},"tls":{"resumed":false,"version":772,"cipher_suite":4865,"proto":"h2","server_name":"api.homekeepr.co"}},"duration":0.000104145,"status":503,"err_id":"c4w4y6se0","err_trace":"reverseproxy.(*Handler).proxyLoopIteration (reverseproxy.go:524)"}
caddy-1  | {"level":"info","ts":1762978377.4955075,"logger":"http.handlers.reverse_proxy.health_checker.active","msg":"host is up","host":"app:8000"}
caddy-1  | {"level":"info","ts":1762978474.5709636,"msg":"shutting down apps, then terminating","signal":"SIGTERM"}
caddy-1  | {"level":"warn","ts":1762978474.571029,"msg":"exiting; byeee!! 👋","signal":"SIGTERM"}
caddy-1  | {"level":"info","ts":1762978474.5711057,"logger":"http","msg":"servers shutting down with eternal grace period"}
caddy-1  | {"level":"info","ts":1762985046.8421297,"msg":"maxprocs: Leaving GOMAXPROCS=4: CPU quota undefined"}
caddy-1  | {"level":"info","ts":1762985046.842306,"msg":"GOMEMLIMIT is updated","package":"github.com/KimMachineGun/automemlimit/memlimit","GOMEMLIMIT":7314971443,"previous":9223372036854775807}
caddy-1  | {"level":"info","ts":1762985046.84239,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
caddy-1  | {"level":"info","ts":1762985046.8439867,"msg":"adapted config to JSON","adapter":"caddyfile"}
squid-1  | --- Generated squid.conf ---
squid-1  | # Squid configuration template for round-robin upstream proxy rotation
squid-1  |
squid-1  | http_port 8888
squid-1  |
caddy-1  | {"level":"warn","ts":1762985046.844022,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":2}
caddy-1  | {"level":"info","ts":1762985046.8449473,"logger":"admin","msg":"admin endpoint started","address":"localhost:2019","enforce_origin":false,"origins":["//localhost:2019","//[::1]:2019","//127.0.0.1:2019"]}
caddy-1  | {"level":"warn","ts":1762985046.8453941,"logger":"tls","msg":"stapling OCSP","error":"no OCSP stapling for [cloudflare origin certificate *.homekeepr.co homekeepr.co]: no URL to issuing certificate"}
caddy-1  | {"level":"info","ts":1762985046.84577,"logger":"tls.cache.maintenance","msg":"started background certificate maintenance","cache":"0xc000445680"}
app-2    | INFO:     Started server process [1]
app-2    | INFO:     Waiting for application startup.
app-2    | INFO:     Application startup complete.
caddy-1  | {"level":"info","ts":1762985046.8460052,"logger":"http.auto_https","msg":"skipping automatic certificate management because one or more matching certificates are already loaded","domain":"api.homekeepr.co","server_name":"srv0"}
caddy-1  | {"level":"info","ts":1762985046.8460593,"logger":"http.auto_https","msg":"enabling automatic HTTP->HTTPS redirects","server_name":"srv0"}
squid-1  | # Upstream proxies (add more cache_peer lines as needed for additional upstreams)
squid-1  | cache_peer 192.210.251.164 parent 12323 0 proxy-only no-query no-digest login=14a79366c9697:6bbbc49dd3 round-robin name=upstream1
squid-1  | cache_peer 89.106.3.243 parent 12323 0 proxy-only no-query no-digest login=14a50ddfa322c:ae6e621d2a round-robin name=upstream2
squid-1  |
squid-1  | # Allow access to all upstream peers
squid-1  | cache_peer_access upstream1 allow all
squid-1  | cache_peer_access upstream2 allow all
squid-1  |
app-2    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-4    | INFO:     Started server process [1]
app-2    | INFO:     127.0.0.1:33722 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:45012 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:41990 - "GET /health HTTP/1.1" 200 OK
squid-1  | never_direct allow all
squid-1  |
squid-1  | # Access control
caddy-1  | {"level":"info","ts":1762985046.848023,"logger":"http","msg":"enabling HTTP/3 listener","addr":":443"}
caddy-1  | {"level":"info","ts":1762985046.8480926,"msg":"failed to sufficiently increase receive buffer size (was: 208 kiB, wanted: 7168 kiB, got: 416 kiB). See https://github.com/quic-go/quic-go/wiki/UDP-Buffer-Sizes for details."}
squid-1  | acl localnet src 127.0.0.1
squid-1  | acl localnet src 172.18.0.0/16
squid-1  | http_access allow localnet
squid-1  | http_access deny all
squid-1  |
squid-1  | # Logging
squid-1  | access_log none
squid-1  | cache_log none
squid-1  |
squid-1  | # Disable caching
squid-1  | cache deny all--- End Generated squid.conf ---
squid-1  | 2025/11/12 22:05:00| Processing Configuration File: /etc/squid/squid.conf (depth 0)
squid-1  | 2025/11/12 22:05:00| Created PID file (/var/run/squid.pid)
squid-1  | 2025/11/12 22:05:00| ERROR: Cannot open cache_log (none) for writing;
squid-1  |     fopen(3) error: (13) Permission denied
squid-1  | 2025/11/12 22:05:00| Current Directory is /
squid-1  | 2025/11/12 22:05:00| Starting Squid Cache version 6.12 for x86_64-alpine-linux-musl...
squid-1  | 2025/11/12 22:05:00| Service Name: squid
squid-1  | 2025/11/12 22:05:00| Process ID 1
squid-1  | 2025/11/12 22:05:00| Process Roles: master worker
squid-1  | 2025/11/12 22:05:00| With 1024 file descriptors available
squid-1  | 2025/11/12 22:05:00| Initializing IP Cache...
squid-1  | 2025/11/12 22:05:00| DNS IPv6 socket created at [::], FD 7
caddy-1  | {"level":"info","ts":1762985046.8481722,"logger":"http.log","msg":"server running","name":"srv0","protocols":["h1","h2","h3"]}
caddy-1  | {"level":"warn","ts":1762985046.848215,"logger":"http","msg":"HTTP/2 skipped because it requires TLS","network":"tcp","addr":":80"}
caddy-1  | {"level":"warn","ts":1762985046.8482182,"logger":"http","msg":"HTTP/3 skipped because it requires TLS","network":"tcp","addr":":80"}
caddy-1  | {"level":"info","ts":1762985046.84822,"logger":"http.log","msg":"server running","name":"remaining_auto_https_redirects","protocols":["h1","h2","h3"]}
caddy-1  | {"level":"info","ts":1762985046.8483517,"msg":"autosaved config (load with --resume flag)","file":"/config/caddy/autosave.json"}
caddy-1  | {"level":"info","ts":1762985046.8483586,"msg":"serving initial configuration"}
caddy-1  | {"level":"info","ts":1762985046.8488553,"logger":"http.handlers.reverse_proxy.health_checker.active","msg":"HTTP request failed","host":"app:8000","error":"Get \"http://app:8000/health\": dial tcp: lookup app on 127.0.0.11:53: server misbehaving"}
caddy-1  | {"level":"info","ts":1762985046.849388,"logger":"tls","msg":"storage cleaning happened too recently; skipping for now","storage":"FileStorage:/data/caddy","instance":"5efd450d-fd9d-4c4d-8dc7-e9efc7f00bbf","try_again":1763071446.84938,"try_again_in":86399.999999659}
caddy-1  | {"level":"info","ts":1762985046.8494425,"logger":"tls","msg":"finished cleaning storage units"}
caddy-1  | {"level":"info","ts":1762985076.8593771,"logger":"http.handlers.reverse_proxy.health_checker.active","msg":"host is up","host":"app:8000"}
app-1    | INFO:     Started server process [1]
app-1    | INFO:     Waiting for application startup.
app-1    | INFO:     Application startup complete.
app-1    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-1    | INFO:     127.0.0.1:33736 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:45026 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:52454 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:41992 - "GET /health HTTP/1.1" 200 OK
squid-1  | 2025/11/12 22:05:00| DNS IPv4 socket created at 0.0.0.0, FD 8
squid-1  | 2025/11/12 22:05:00| Adding nameserver 127.0.0.11 from /etc/resolv.conf
squid-1  | 2025/11/12 22:05:00| Adding domain . from /etc/resolv.conf
squid-1  | 2025/11/12 22:05:00| Adding ndots 1 from /etc/resolv.conf
squid-1  | 2025/11/12 22:05:00| Local cache digest enabled; rebuild/rewrite every 3600/3600 sec
squid-1  | 2025/11/12 22:05:00| Store logging disabled
squid-1  | 2025/11/12 22:05:00| Swap maxSize 0 + 262144 KB, estimated 20164 objects
squid-1  | 2025/11/12 22:05:00| Target number of buckets: 1008
squid-1  | 2025/11/12 22:05:00| Using 8192 Store buckets
squid-1  | 2025/11/12 22:05:00| Max Mem  size: 262144 KB
squid-1  | 2025/11/12 22:05:00| Max Swap size: 0 KB
squid-1  | 2025/11/12 22:05:00| Using Least Load store dir selection
squid-1  | 2025/11/12 22:05:00| Current Directory is /
squid-1  | 2025/11/12 22:05:00| Finished loading MIME types and icons.
squid-1  | 2025/11/12 22:05:00| HTCP Disabled.
squid-1  | 2025/11/12 22:05:00| Configuring Parent upstream1
squid-1  | 2025/11/12 22:05:00| Configuring Parent upstream2
squid-1  | 2025/11/12 22:05:00| Squid plugin modules loaded: 0
squid-1  | 2025/11/12 22:05:00| Adaptation support is off.
squid-1  | 2025/11/12 22:05:00| Accepting HTTP Socket connections at conn3 local=[::]:8888 remote=[::] FD 9 flags=9
squid-1  |     listening port: 8888
squid-1  | 2025/11/12 22:05:01| storeLateRelease: released 0 objects
app-4    | INFO:     Waiting for application startup.
app-4    | INFO:     Application startup complete.
app-4    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-4    | INFO:     127.0.0.1:33744 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:45032 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:42012 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     Started server process [1]
app-3    | INFO:     Waiting for application startup.
app-3    | INFO:     Application startup complete.
app-3    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-3    | INFO:     127.0.0.1:33738 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:32862 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:45028 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:42006 - "GET /health HTTP/1.1" 200 OK
app-2    | 2025-11-12 22:05:20 - serpapi.orchestrator - INFO - Starting SerpApi fetch brand=whirlpool model=WRX735SDHZ03
app-2    | 2025-11-12 22:05:20 - serpapi.orchestrator - INFO - Executing 9 SerpApi querie(s) for brand=whirlpool model=WRX735SDHZ03
app-2    | 2025-11-12 22:05:20 - serpapi.orchestrator - INFO - SerpApi query 1/9: Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com
app-2    | 2025-11-12 22:05:20 - serpapi.client - INFO - Issuing SerpApi request query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com location=Austin, Texas, United States num=10
app-2    | 2025-11-12 22:05:20 - serpapi.client - INFO - SerpApi request succeeded query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com search_id=6914fdf70e4be0c6b4015796 organic_results=7
app-2    | 2025-11-12 22:05:20 - serpapi.orchestrator - INFO - Collecting candidates for query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com (search_id=6914fdf70e4be0c6b4015796)
app-2    | 2025-11-12 22:05:20 - serpapi.orchestrator - INFO - Collected 6 candidate(s) for query=Whirlpool WRX735SDHZ03 owner's manual filetype:pdf site:whirlpool.com (search_id=6914fdf70e4be0c6b4015796)
app-2    | 2025-11-12 22:05:20 - serpapi.orchestrator - INFO - Attempting candidate url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf score=61 source=organic_results
app-2    | 2025-11-12 22:05:35 - serpapi.orchestrator - INFO - Downloading candidate url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf brand=whirlpool model=WRX735SDHZ03 referer=https://www.whirlpool.com/ read_timeout=15
app-1    | INFO:     172.18.0.3:48946 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43016 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43032 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:43042 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:43058 - "GET /health HTTP/1.1" 200 OK
app-2    | 2025-11-12 22:05:50 - serpapi.orchestrator - WARNING - Download timed out while reading url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf host=www.whirlpool.com read_timeout=15 error=HTTPSConnectionPool(host='www.whirlpool.com', port=443): Read timed out. (read timeout=15)
app-2    | 2025-11-12 22:05:50 - serpapi.orchestrator - INFO - Attempting headless fallback download for url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf
app-2    | Using proxy server http://squid:8888
app-2    | 2025-11-12 22:05:50 - undetected_chromedriver.patcher - INFO - patching driver executable /usr/bin/chromedriver
app-2    | 2025-11-12 22:05:50 - uc - WARNING - could not detect version_main.therefore, we are assuming it is chrome 108 or higher
app-2    | 2025-11-12 22:05:56 - serpapi.headless_pdf_fetcher - INFO - Headless PDF navigation url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf host=www.whirlpool.com
squid-1  | 2025/11/12 22:05:57| ERROR: Connection to upstream1 failed
squid-1  |     current master transaction: master353
squid-1  | 2025/11/12 22:05:57| ERROR: Connection to upstream2 failed
squid-1  |     current master transaction: master353
app-4    | INFO:     172.18.0.3:52730 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:46600 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:46604 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:46608 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:46616 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:40410 - "GET /health HTTP/1.1" 200 OK
app-2    | 2025-11-12 22:06:38 - serpapi.headless_pdf_fetcher - INFO - Fetch-based download succeeded url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf path=/app/headless-browser-scraper/temp/tmpi6rtgfqf/use-and-care-w10422734-revB.pdf
app-2    | 2025-11-12 22:06:38 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpi6rtgfqf/use-and-care-w10422734-revB.pdf doc_type=owner accept=True manual_signal=0 manual_tokens=2 marketing_hits=0 page_count=47 contains_model=False
app-2    | 2025-11-12 22:06:38 - serpapi.orchestrator - INFO - Validation passed for candidate url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf doc_type=owner score=61
app-2    | 2025-11-12 22:06:38 - serpapi.orchestrator - INFO - Candidate accepted url=https://www.whirlpool.com/content/dam/global/documents/201809/use-and-care-w10422734-revB.pdf brand=whirlpool model=WRX735SDHZ03
app-2    | 2025-11-12 22:06:38 - ingest - INFO - Ingesting PDF from local path: /app/headless-browser-scraper/temp/tmpi6rtgfqf/use-and-care-w10422734-revB.pdf
app-2    | Cleaned up temp dir: /app/headless-browser-scraper/temp/tmpi6rtgfqf
app-2    | INFO:     172.18.0.3:35430 - "GET /scrape/whirlpool/WRX735SDHZ03 HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:57622 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:57632 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:57638 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:57652 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:46714 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:59746 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:59754 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:59762 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:59768 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:40090 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:57140 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:57144 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:57148 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:57150 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:39152 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:38964 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:38974 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:38988 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:38990 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:58198 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:38312 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:38324 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:38330 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:38336 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:46368 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:34850 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:34860 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:34862 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:34868 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:33220 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:33268 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:33282 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:33290 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:33306 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:60124 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:48858 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:48860 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:48872 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:48876 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:57822 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:44416 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:44426 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:44438 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:44446 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:43458 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:42224 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:42238 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:42248 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:42256 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:49612 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:54306 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:54318 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:54326 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:54328 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:50126 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:50158 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:50164 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:50168 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:50174 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:57912 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:55264 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:55276 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:55278 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:55290 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:54004 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:35474 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:35484 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:35500 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:35502 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:32992 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:57828 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:57840 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:57848 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:57856 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:35156 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:57098 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:57108 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:57110 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:57120 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:51400 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:42922 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:42928 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:42934 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:42938 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:53824 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:44112 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:44128 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:44130 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:44144 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:40416 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:38336 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:38348 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:38360 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:38368 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:58564 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:39682 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:39698 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:39708 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:39718 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:48292 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:36448 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:36464 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:36478 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:36484 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:55640 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:57610 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:57616 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:57626 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:57628 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:58914 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:40118 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:40130 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:40144 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:40152 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:35016 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:35340 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:35346 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:35358 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:35370 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:39010 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:34858 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:34860 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:34862 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:34876 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:49234 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:48864 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:48870 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:48880 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:48890 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:59770 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:57532 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:57542 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:57546 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:57562 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:60536 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:46320 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:46336 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:46342 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:46354 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:60486 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:35488 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:35494 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:35498 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:35510 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:53708 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:60730 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:60738 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:60742 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:60756 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:33356 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:53598 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:53608 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:53622 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:53638 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:60974 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:51846 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:51852 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:51860 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:51870 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:39326 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43192 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43208 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:43214 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:43226 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:51508 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:60456 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:60458 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:60472 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:60478 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:37220 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:46490 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:46502 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:46518 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:46524 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:50052 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:45156 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:45166 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:45174 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:45182 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:38222 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:35704 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:35716 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:35722 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:35738 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:35362 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:52748 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:52758 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:52766 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:52772 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:46756 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:47896 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:47906 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:47920 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:47924 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:50180 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:39302 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:39308 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:39314 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:39322 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:60718 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:33472 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:33486 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:33494 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:33498 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:51766 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:40202 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:40206 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:40216 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:40228 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:34654 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:51294 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:51300 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:51308 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:51312 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:60682 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:56466 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:56476 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:56490 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:56504 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:55934 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:33388 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:33404 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:33418 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:33430 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:44992 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:37564 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:37568 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:37570 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:37572 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:49156 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:49370 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:49384 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:49398 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:49412 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:48962 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:57682 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:57688 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:57694 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:57706 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:34898 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:45270 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:45274 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:45286 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:45288 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:52190 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:42058 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:42074 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:42084 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:42098 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:55770 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:54764 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:54772 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:54786 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:54800 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:36972 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43324 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43334 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:43348 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:43364 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:36798 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:37854 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:37862 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:37878 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:37894 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:48300 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:38762 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:38772 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:38784 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:38796 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:41566 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:40722 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:40732 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:40746 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:40760 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:43572 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:56660 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:56674 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:56684 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:56696 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:33996 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:58844 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:58850 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:58860 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:58870 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:51532 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:39962 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:39974 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:39986 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:40000 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:40266 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:60004 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:60020 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:60036 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:60046 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:33916 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:33858 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:33860 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:33862 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:33864 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:44470 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:49472 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:49484 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:49498 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:49506 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:38890 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:41466 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:41476 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:41482 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:41490 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:57728 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:45470 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:45476 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:45484 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:45500 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:56978 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:41690 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:41692 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:41696 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:41710 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:38848 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:49356 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:49358 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:49362 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:49372 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:39708 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:35898 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:35908 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:35910 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:35920 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:32994 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:52568 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:52570 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:52580 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:52594 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:60902 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:48332 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:48342 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:48348 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:48364 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:53102 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:41582 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:41592 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:41606 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:41614 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:47188 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:36708 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:36712 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:36724 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:36730 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:43090 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:54750 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:54758 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:54762 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:54778 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:33028 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43354 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43358 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:43374 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:43384 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:46328 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:53584 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:53598 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:53612 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:53614 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:43906 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:41744 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:41756 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:41772 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:41786 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:54572 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:34822 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:34830 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:34846 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:34862 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:35284 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:54694 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:54708 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:54722 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:54728 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:57740 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:44274 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:44278 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:44292 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:44304 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:40982 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43124 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43134 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:43140 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:43146 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:53620 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:52642 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:52648 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:52656 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:52668 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:53514 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:54366 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:54368 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:54380 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:54390 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:34042 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:40864 - "GET /scrape/testbrand/TESMODEL HTTP/1.1" 400 Bad Request
app-3    | INFO:     172.18.0.3:40864 - "GET /scrape/electrolux/FGID2468UF1A HTTP/1.1" 400 Bad Request
app-3    | 2025-11-12 22:46:43 - serpapi.orchestrator - INFO - Starting SerpApi fetch brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:46:43 - serpapi.orchestrator - INFO - Executing 10 SerpApi querie(s) for brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:46:43 - serpapi.orchestrator - INFO - SerpApi query 1/10: LG WM4270HWA owner's manual filetype:pdf site:lg.com
app-3    | 2025-11-12 22:46:43 - serpapi.client - INFO - Issuing SerpApi request query=LG WM4270HWA owner's manual filetype:pdf site:lg.com location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:44 - serpapi.orchestrator - INFO - Starting SerpApi fetch brand=whirlpool model=LE7680XSH2
app-1    | 2025-11-12 22:46:44 - serpapi.orchestrator - INFO - Executing 9 SerpApi querie(s) for brand=whirlpool model=LE7680XSH2
app-1    | 2025-11-12 22:46:44 - serpapi.orchestrator - INFO - SerpApi query 1/9: Whirlpool LE7680XSH2 owner's manual filetype:pdf site:whirlpool.com
app-1    | 2025-11-12 22:46:44 - serpapi.client - INFO - Issuing SerpApi request query=Whirlpool LE7680XSH2 owner's manual filetype:pdf site:whirlpool.com location=Austin, Texas, United States num=10
app-1    | INFO:     172.18.0.3:33324 - "GET /scrape/gsw%20water%20heating%20company/JWF-507 HTTP/1.1" 400 Bad Request
app-3    | 2025-11-12 22:46:45 - serpapi.client - INFO - SerpApi request succeeded query=LG WM4270HWA owner's manual filetype:pdf site:lg.com search_id=69150e53cc56d3a9605d6cc7 organic_results=1
app-3    | 2025-11-12 22:46:45 - serpapi.orchestrator - INFO - Collecting candidates for query=LG WM4270HWA owner's manual filetype:pdf site:lg.com (search_id=69150e53cc56d3a9605d6cc7)
app-3    | 2025-11-12 22:46:45 - serpapi.orchestrator - INFO - Collected 1 candidate(s) for query=LG WM4270HWA owner's manual filetype:pdf site:lg.com (search_id=69150e53cc56d3a9605d6cc7)
app-3    | 2025-11-12 22:46:45 - serpapi.orchestrator - INFO - Attempting candidate url=https://www.lg.com/us/support/products/documents/DLEX4270%20DLGX4271%20Spec%20Sheet.pdf score=21 source=organic_results
app-3    | 2025-11-12 22:46:45 - serpapi.orchestrator - INFO - Downloading candidate url=https://www.lg.com/us/support/products/documents/DLEX4270%20DLGX4271%20Spec%20Sheet.pdf brand=lg model=WM4270HWA referer=https://www.lg.com/ read_timeout=15
app-1    | INFO:     172.18.0.3:33324 - "GET /scrape/danby/DDR050BJPWDB HTTP/1.1" 400 Bad Request
app-3    | 2025-11-12 22:46:45 - serpapi.orchestrator - INFO - Successfully downloaded url=https://www.lg.com/us/support/products/documents/DLEX4270%20DLGX4271%20Spec%20Sheet.pdf to /app/headless-browser-scraper/temp/tmp926fkwh9/DLEX4270 DLGX4271 Spec Sheet.pdf
app-3    | 2025-11-12 22:46:45 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmp926fkwh9/DLEX4270 DLGX4271 Spec Sheet.pdf doc_type=spec accept=False manual_signal=0 manual_tokens=1 marketing_hits=0 page_count=2 contains_model=True
app-3    | 2025-11-12 22:46:45 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmp926fkwh9/DLEX4270 DLGX4271 Spec Sheet.pdf reason=disallowed_doc_type:spec
app-3    | 2025-11-12 22:46:45 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://www.lg.com/us/support/products/documents/DLEX4270%20DLGX4271%20Spec%20Sheet.pdf brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:46:45 - serpapi.orchestrator - INFO - SerpApi query 2/10: LG WM4270HWA manual filetype:pdf site:lg.com
app-3    | 2025-11-12 22:46:45 - serpapi.client - INFO - Issuing SerpApi request query=LG WM4270HWA manual filetype:pdf site:lg.com location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:46:46 - serpapi.client - INFO - SerpApi request succeeded query=LG WM4270HWA manual filetype:pdf site:lg.com search_id=69150e55d3982ce8cbe7cf67 organic_results=1
app-3    | 2025-11-12 22:46:46 - serpapi.orchestrator - INFO - Collecting candidates for query=LG WM4270HWA manual filetype:pdf site:lg.com (search_id=69150e55d3982ce8cbe7cf67)
app-3    | 2025-11-12 22:46:46 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=LG WM4270HWA manual filetype:pdf site:lg.com (search_id=69150e55d3982ce8cbe7cf67)
app-3    | 2025-11-12 22:46:46 - serpapi.orchestrator - INFO - No PDF candidates returned for query=LG WM4270HWA manual filetype:pdf site:lg.com
app-3    | 2025-11-12 22:46:46 - serpapi.orchestrator - INFO - SerpApi query 3/10: LG WM4270HWA owner's manual filetype:pdf site:lge.com
app-3    | 2025-11-12 22:46:46 - serpapi.client - INFO - Issuing SerpApi request query=LG WM4270HWA owner's manual filetype:pdf site:lge.com location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:47 - serpapi.client - ERROR - SerpApi reported error for query=Whirlpool LE7680XSH2 owner's manual filetype:pdf site:whirlpool.com: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:47 - serpapi.orchestrator - WARNING - SerpApi search error for query=Whirlpool LE7680XSH2 owner's manual filetype:pdf site:whirlpool.com: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:47 - serpapi.orchestrator - INFO - SerpApi query 2/9: Whirlpool LE7680XSH2 manual filetype:pdf site:whirlpool.com
app-1    | 2025-11-12 22:46:47 - serpapi.client - INFO - Issuing SerpApi request query=Whirlpool LE7680XSH2 manual filetype:pdf site:whirlpool.com location=Austin, Texas, United States num=10
app-2    | INFO:     127.0.0.1:59574 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:59576 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:33324 - "GET /scrape/sub-zero/650/F HTTP/1.1" 400 Bad Request
app-3    | INFO:     127.0.0.1:59586 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:45950 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:33324 - "GET /scrape/bosch/SHP68T55UC/07 HTTP/1.1" 400 Bad Request
app-1    | 2025-11-12 22:46:48 - serpapi.client - ERROR - SerpApi reported error for query=Whirlpool LE7680XSH2 manual filetype:pdf site:whirlpool.com: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:48 - serpapi.orchestrator - WARNING - SerpApi search error for query=Whirlpool LE7680XSH2 manual filetype:pdf site:whirlpool.com: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:48 - serpapi.orchestrator - INFO - SerpApi query 3/9: Whirlpool LE7680XSH2 tech sheet filetype:pdf
app-1    | 2025-11-12 22:46:48 - serpapi.client - INFO - Issuing SerpApi request query=Whirlpool LE7680XSH2 tech sheet filetype:pdf location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:48 - serpapi.orchestrator - INFO - Starting SerpApi fetch brand=samsung model=dc68-03172b-03
app-1    | 2025-11-12 22:46:48 - serpapi.orchestrator - INFO - Executing 10 SerpApi querie(s) for brand=samsung model=dc68-03172b-03
app-1    | 2025-11-12 22:46:48 - serpapi.orchestrator - INFO - SerpApi query 1/10: Samsung dc68-03172b-03 owner's manual filetype:pdf site:samsung.com
app-1    | 2025-11-12 22:46:48 - serpapi.client - INFO - Issuing SerpApi request query=Samsung dc68-03172b-03 owner's manual filetype:pdf site:samsung.com location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - Starting SerpApi fetch brand=samsung model=DVE45T3400W/A3
app-3    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - Executing 10 SerpApi querie(s) for brand=samsung model=DVE45T3400W/A3
app-3    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - SerpApi query 1/10: Samsung DVE45T3400W/A3 owner's manual filetype:pdf site:samsung.com
app-3    | 2025-11-12 22:46:49 - serpapi.client - INFO - Issuing SerpApi request query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf site:samsung.com location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:46:49 - serpapi.client - ERROR - SerpApi reported error for query=LG WM4270HWA owner's manual filetype:pdf site:lge.com: Google hasn't returned any results for this query.
app-3    | 2025-11-12 22:46:49 - serpapi.orchestrator - WARNING - SerpApi search error for query=LG WM4270HWA owner's manual filetype:pdf site:lge.com: Google hasn't returned any results for this query.
app-3    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - SerpApi query 4/10: LG WM4270HWA manual filetype:pdf site:lge.com
app-3    | 2025-11-12 22:46:49 - serpapi.client - INFO - Issuing SerpApi request query=LG WM4270HWA manual filetype:pdf site:lge.com location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:49 - serpapi.client - INFO - SerpApi request succeeded query=Samsung dc68-03172b-03 owner's manual filetype:pdf site:samsung.com search_id=69150e58a2897182260931fd organic_results=1
app-1    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - Collecting candidates for query=Samsung dc68-03172b-03 owner's manual filetype:pdf site:samsung.com (search_id=69150e58a2897182260931fd)
app-1    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - Collected 1 candidate(s) for query=Samsung dc68-03172b-03 owner's manual filetype:pdf site:samsung.com (search_id=69150e58a2897182260931fd)
app-1    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - Attempting candidate url=https://image-us.samsung.com/SamsungUS/tv-ci-resources/2018-user-manuals/2018_UserManual_Q9FNSeries.pdf score=61 source=organic_results
app-1    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - Downloading candidate url=https://image-us.samsung.com/SamsungUS/tv-ci-resources/2018-user-manuals/2018_UserManual_Q9FNSeries.pdf brand=samsung model=dc68-03172b-03 referer=https://image-us.samsung.com/ read_timeout=15
app-1    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - Successfully downloaded url=https://image-us.samsung.com/SamsungUS/tv-ci-resources/2018-user-manuals/2018_UserManual_Q9FNSeries.pdf to /app/headless-browser-scraper/temp/tmpkosqa298/2018_UserManual_Q9FNSeries.pdf
app-1    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpkosqa298/2018_UserManual_Q9FNSeries.pdf doc_type=owner accept=True manual_signal=1 manual_tokens=3 marketing_hits=0 page_count=24 contains_model=False
app-1    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - Validation passed for candidate url=https://image-us.samsung.com/SamsungUS/tv-ci-resources/2018-user-manuals/2018_UserManual_Q9FNSeries.pdf doc_type=owner score=61
app-1    | 2025-11-12 22:46:49 - serpapi.orchestrator - INFO - Candidate accepted url=https://image-us.samsung.com/SamsungUS/tv-ci-resources/2018-user-manuals/2018_UserManual_Q9FNSeries.pdf brand=samsung model=dc68-03172b-03
app-1    | 2025-11-12 22:46:50 - ingest - INFO - Ingesting PDF from local path: /app/headless-browser-scraper/temp/tmpkosqa298/2018_UserManual_Q9FNSeries.pdf
app-3    | 2025-11-12 22:46:50 - serpapi.client - ERROR - SerpApi reported error for query=LG WM4270HWA manual filetype:pdf site:lge.com: Google hasn't returned any results for this query.
app-3    | 2025-11-12 22:46:50 - serpapi.orchestrator - WARNING - SerpApi search error for query=LG WM4270HWA manual filetype:pdf site:lge.com: Google hasn't returned any results for this query.
app-3    | 2025-11-12 22:46:50 - serpapi.orchestrator - INFO - SerpApi query 5/10: LG WM4270HWA manual filetype:pdf
app-3    | 2025-11-12 22:46:50 - serpapi.client - INFO - Issuing SerpApi request query=LG WM4270HWA manual filetype:pdf location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:46:50 - serpapi.orchestrator - INFO - Starting SerpApi fetch brand=whirlpool model=WEG750H0H
app-3    | 2025-11-12 22:46:50 - serpapi.orchestrator - INFO - Executing 9 SerpApi querie(s) for brand=whirlpool model=WEG750H0H
app-3    | 2025-11-12 22:46:50 - serpapi.orchestrator - INFO - SerpApi query 1/9: Whirlpool WEG750H0H owner's manual filetype:pdf site:whirlpool.com
app-3    | 2025-11-12 22:46:50 - serpapi.client - INFO - Issuing SerpApi request query=Whirlpool WEG750H0H owner's manual filetype:pdf site:whirlpool.com location=Austin, Texas, United States num=10
app-1    | Cleaned up temp dir: /app/headless-browser-scraper/temp/tmpkosqa298
app-1    | INFO:     172.18.0.3:33324 - "GET /scrape/samsung/dc68-03172b-03 HTTP/1.1" 200 OK
app-3    | 2025-11-12 22:46:50 - serpapi.client - INFO - SerpApi request succeeded query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf site:samsung.com search_id=69150e5980f30e600cbd9899 organic_results=2
app-3    | 2025-11-12 22:46:50 - serpapi.orchestrator - INFO - Collecting candidates for query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf site:samsung.com (search_id=69150e5980f30e600cbd9899)
app-3    | 2025-11-12 22:46:50 - serpapi.orchestrator - INFO - Collected 2 candidate(s) for query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf site:samsung.com (search_id=69150e5980f30e600cbd9899)
app-3    | 2025-11-12 22:46:50 - serpapi.orchestrator - INFO - Attempting candidate url=https://image-us.samsung.com/SamsungUS/home/shop/promotions/mlk-pd-buymore-savemore-offer/03032023/PL018443_Samsung-HA-MLK-PD-Buy-More-Save-more-Offer_Full_TCs_V7_12.16.22.pdf score=80 source=organic_results
app-3    | 2025-11-12 22:46:50 - serpapi.orchestrator - INFO - Downloading candidate url=https://image-us.samsung.com/SamsungUS/home/shop/promotions/mlk-pd-buymore-savemore-offer/03032023/PL018443_Samsung-HA-MLK-PD-Buy-More-Save-more-Offer_Full_TCs_V7_12.16.22.pdf brand=samsung model=DVE45T3400W/A3 referer=https://image-us.samsung.com/ read_timeout=15
app-1    | INFO:     172.18.0.3:33324 - "GET /scrape/moen/GXP33cc HTTP/1.1" 400 Bad Request
app-3    | 2025-11-12 22:46:51 - serpapi.client - INFO - SerpApi request succeeded query=LG WM4270HWA manual filetype:pdf search_id=69150e5abadf0b90a3fc86b4 organic_results=5
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Collecting candidates for query=LG WM4270HWA manual filetype:pdf (search_id=69150e5abadf0b90a3fc86b4)
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Collected 4 candidate(s) for query=LG WM4270HWA manual filetype:pdf (search_id=69150e5abadf0b90a3fc86b4)
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Attempting candidate url=https://research.encompass.com/ZEN/sm/WM4270HWA.pdf score=41 source=organic_results
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Downloading candidate url=https://research.encompass.com/ZEN/sm/WM4270HWA.pdf brand=lg model=WM4270HWA referer=https://research.encompass.com/ read_timeout=15
app-3    | 2025-11-12 22:46:51 - serpapi.client - INFO - SerpApi request succeeded query=Whirlpool WEG750H0H owner's manual filetype:pdf site:whirlpool.com search_id=69150e5ad10c6ad5c2b2b241 organic_results=5
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Collecting candidates for query=Whirlpool WEG750H0H owner's manual filetype:pdf site:whirlpool.com (search_id=69150e5ad10c6ad5c2b2b241)
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Collected 5 candidate(s) for query=Whirlpool WEG750H0H owner's manual filetype:pdf site:whirlpool.com (search_id=69150e5ad10c6ad5c2b2b241)
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Attempting candidate url=https://www.whirlpool.com/content/dam/business-unit/whirlpool/en-us/marketing-content/site-assets/global-assets/documents/whirlpool-brand-catalog-2019-Q2.pdf score=77 source=organic_results
app-1    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Starting SerpApi fetch brand=rheem model=PROG50-38N RH60
app-1    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Executing 10 SerpApi querie(s) for brand=rheem model=PROG50-38N RH60
app-1    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - SerpApi query 1/10: Rheem PROG50-38N RH60 owner's manual filetype:pdf site:rheem.com
app-1    | 2025-11-12 22:46:51 - serpapi.client - INFO - Issuing SerpApi request query=Rheem PROG50-38N RH60 owner's manual filetype:pdf site:rheem.com location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Successfully downloaded url=https://image-us.samsung.com/SamsungUS/home/shop/promotions/mlk-pd-buymore-savemore-offer/03032023/PL018443_Samsung-HA-MLK-PD-Buy-More-Save-more-Offer_Full_TCs_V7_12.16.22.pdf to /app/headless-browser-scraper/temp/tmpixuknw45/PL018443_Samsung-HA-MLK-PD-Buy-More-Save-more-Offer_Full_TCs_V7_12.16.22.pdf
app-1    | 2025-11-12 22:46:51 - serpapi.client - ERROR - SerpApi reported error for query=Whirlpool LE7680XSH2 tech sheet filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:51 - serpapi.orchestrator - WARNING - SerpApi search error for query=Whirlpool LE7680XSH2 tech sheet filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - SerpApi query 4/9: Whirlpool LE7680XSH2 installation instructions filetype:pdf
app-1    | 2025-11-12 22:46:51 - serpapi.client - INFO - Issuing SerpApi request query=Whirlpool LE7680XSH2 installation instructions filetype:pdf location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpixuknw45/PL018443_Samsung-HA-MLK-PD-Buy-More-Save-more-Offer_Full_TCs_V7_12.16.22.pdf doc_type=owner accept=False manual_signal=0 manual_tokens=2 marketing_hits=1 page_count=37 contains_model=False
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpixuknw45/PL018443_Samsung-HA-MLK-PD-Buy-More-Save-more-Offer_Full_TCs_V7_12.16.22.pdf reason=marketing_signals
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://image-us.samsung.com/SamsungUS/home/shop/promotions/mlk-pd-buymore-savemore-offer/03032023/PL018443_Samsung-HA-MLK-PD-Buy-More-Save-more-Offer_Full_TCs_V7_12.16.22.pdf brand=samsung model=DVE45T3400W/A3
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Attempting candidate url=https://image-us.samsung.com/SamsungUS/home/home-appliances/11-25-20/DVE45T3400W_V4.pdf score=61 source=organic_results
app-3    | 2025-11-12 22:46:51 - serpapi.orchestrator - INFO - Downloading candidate url=https://image-us.samsung.com/SamsungUS/home/home-appliances/11-25-20/DVE45T3400W_V4.pdf brand=samsung model=DVE45T3400W/A3 referer=https://image-us.samsung.com/ read_timeout=15
app-3    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - Successfully downloaded url=https://image-us.samsung.com/SamsungUS/home/home-appliances/11-25-20/DVE45T3400W_V4.pdf to /app/headless-browser-scraper/temp/tmpf6o030oa/DVE45T3400W_V4.pdf
app-4    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - Starting SerpApi fetch brand=frigidaire model=FGRF1097
app-4    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - Executing 10 SerpApi querie(s) for brand=frigidaire model=FGRF1097
app-4    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - SerpApi query 1/10: Frigidaire FGRF1097 owner's manual filetype:pdf site:frigidaire.com
app-4    | 2025-11-12 22:46:52 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGRF1097 owner's manual filetype:pdf site:frigidaire.com location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:52 - serpapi.client - INFO - SerpApi request succeeded query=Rheem PROG50-38N RH60 owner's manual filetype:pdf site:rheem.com search_id=69150e5b71a41d446044712c organic_results=3
app-1    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - Collecting candidates for query=Rheem PROG50-38N RH60 owner's manual filetype:pdf site:rheem.com (search_id=69150e5b71a41d446044712c)
app-1    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - Collected 4 candidate(s) for query=Rheem PROG50-38N RH60 owner's manual filetype:pdf site:rheem.com (search_id=69150e5b71a41d446044712c)
app-1    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - Attempting candidate url=https://files.rheem.com/blobazrheem/wp-content/uploads/sites/2/AP23657-Rev-01-Manual-HPWH-GEN-V-UNIVERSAL-CONNECT-ENGLISH_HALF-SIZE-3.pdf score=61 source=organic_results
app-1    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - Downloading candidate url=https://files.rheem.com/blobazrheem/wp-content/uploads/sites/2/AP23657-Rev-01-Manual-HPWH-GEN-V-UNIVERSAL-CONNECT-ENGLISH_HALF-SIZE-3.pdf brand=rheem model=PROG50-38N RH60 referer=https://files.rheem.com/ read_timeout=15
app-3    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpf6o030oa/DVE45T3400W_V4.pdf doc_type=owner accept=False manual_signal=1 manual_tokens=1 marketing_hits=0 page_count=2 contains_model=False
app-3    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpf6o030oa/DVE45T3400W_V4.pdf reason=owner_manual_too_short
app-3    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://image-us.samsung.com/SamsungUS/home/home-appliances/11-25-20/DVE45T3400W_V4.pdf brand=samsung model=DVE45T3400W/A3
app-3    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - SerpApi query 2/10: Samsung DVE45T3400W/A3 manual filetype:pdf site:samsung.com
app-3    | 2025-11-12 22:46:52 - serpapi.client - INFO - Issuing SerpApi request query=Samsung DVE45T3400W/A3 manual filetype:pdf site:samsung.com location=Austin, Texas, United States num=10
app-4    | INFO:     172.18.0.3:60270 - "GET /scrape/carrier/CAPMP2417ALAEAA HTTP/1.1" 400 Bad Request
app-1    | 2025-11-12 22:46:52 - serpapi.client - ERROR - SerpApi reported error for query=Whirlpool LE7680XSH2 installation instructions filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:52 - serpapi.orchestrator - WARNING - SerpApi search error for query=Whirlpool LE7680XSH2 installation instructions filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:52 - serpapi.orchestrator - INFO - SerpApi query 5/9: Whirlpool LE7680XSH2 owner's manual filetype:pdf
app-1    | 2025-11-12 22:46:52 - serpapi.client - INFO - Issuing SerpApi request query=Whirlpool LE7680XSH2 owner's manual filetype:pdf location=Austin, Texas, United States num=10
app-4    | INFO:     172.18.0.3:60270 - "GET /scrape/zipply/XS-010X-Q HTTP/1.1" 400 Bad Request
app-4    | INFO:     172.18.0.3:60270 - "GET /scrape/first%20alert/Sc9120b HTTP/1.1" 400 Bad Request
app-3    | 2025-11-12 22:46:53 - serpapi.client - INFO - SerpApi request succeeded query=Samsung DVE45T3400W/A3 manual filetype:pdf site:samsung.com search_id=69150e5c22abf7932d9fe36d organic_results=2
app-3    | 2025-11-12 22:46:53 - serpapi.orchestrator - INFO - Collecting candidates for query=Samsung DVE45T3400W/A3 manual filetype:pdf site:samsung.com (search_id=69150e5c22abf7932d9fe36d)
app-3    | 2025-11-12 22:46:53 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=Samsung DVE45T3400W/A3 manual filetype:pdf site:samsung.com (search_id=69150e5c22abf7932d9fe36d)
app-3    | 2025-11-12 22:46:53 - serpapi.orchestrator - INFO - No PDF candidates returned for query=Samsung DVE45T3400W/A3 manual filetype:pdf site:samsung.com
app-3    | 2025-11-12 22:46:53 - serpapi.orchestrator - INFO - SerpApi query 3/10: Samsung DVE45T3400W/A3 owner's manual filetype:pdf site:downloadcenter.samsung.com
app-3    | 2025-11-12 22:46:53 - serpapi.client - INFO - Issuing SerpApi request query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf site:downloadcenter.samsung.com location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:46:53 - serpapi.orchestrator - INFO - Starting SerpApi fetch brand=frigidaire model=FGMV175QFA
app-4    | 2025-11-12 22:46:53 - serpapi.orchestrator - INFO - Executing 10 SerpApi querie(s) for brand=frigidaire model=FGMV175QFA
app-4    | 2025-11-12 22:46:53 - serpapi.orchestrator - INFO - SerpApi query 1/10: Frigidaire FGMV175QFA owner's manual filetype:pdf site:frigidaire.com
app-4    | 2025-11-12 22:46:53 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGMV175QFA owner's manual filetype:pdf site:frigidaire.com location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:54 - serpapi.client - ERROR - SerpApi reported error for query=Whirlpool LE7680XSH2 owner's manual filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:54 - serpapi.orchestrator - WARNING - SerpApi search error for query=Whirlpool LE7680XSH2 owner's manual filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:54 - serpapi.orchestrator - INFO - SerpApi query 6/9: Whirlpool LE7680XSH2 manual filetype:pdf
app-1    | 2025-11-12 22:46:54 - serpapi.client - INFO - Issuing SerpApi request query=Whirlpool LE7680XSH2 manual filetype:pdf location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:54 - serpapi.orchestrator - INFO - Successfully downloaded url=https://files.rheem.com/blobazrheem/wp-content/uploads/sites/2/AP23657-Rev-01-Manual-HPWH-GEN-V-UNIVERSAL-CONNECT-ENGLISH_HALF-SIZE-3.pdf to /app/headless-browser-scraper/temp/tmp5he783jd/AP23657-Rev-01-Manual-HPWH-GEN-V-UNIVERSAL-CONNECT-ENGLISH_HALF-SIZE-3.pdf
app-1    | 2025-11-12 22:46:54 - serpapi.orchestrator - INFO - Validation failed for candidate url=https://files.rheem.com/blobazrheem/wp-content/uploads/sites/2/AP23657-Rev-01-Manual-HPWH-GEN-V-UNIVERSAL-CONNECT-ENGLISH_HALF-SIZE-3.pdf
app-1    | 2025-11-12 22:46:54 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://files.rheem.com/blobazrheem/wp-content/uploads/sites/2/AP23657-Rev-01-Manual-HPWH-GEN-V-UNIVERSAL-CONNECT-ENGLISH_HALF-SIZE-3.pdf brand=rheem model=PROG50-38N RH60
app-1    | 2025-11-12 22:46:54 - serpapi.orchestrator - INFO - Attempting candidate url=https://files.rheem.com/blobazrheem/wp-content/uploads/sites/2/AP21831-Rev-2-SHEG-TriBrand-UC.pdf score=60 source=organic_results
app-1    | 2025-11-12 22:46:54 - serpapi.orchestrator - INFO - Downloading candidate url=https://files.rheem.com/blobazrheem/wp-content/uploads/sites/2/AP21831-Rev-2-SHEG-TriBrand-UC.pdf brand=rheem model=PROG50-38N RH60 referer=https://files.rheem.com/ read_timeout=15
app-3    | 2025-11-12 22:46:54 - serpapi.client - ERROR - SerpApi reported error for query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf site:downloadcenter.samsung.com: Google hasn't returned any results for this query.
app-3    | 2025-11-12 22:46:54 - serpapi.orchestrator - WARNING - SerpApi search error for query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf site:downloadcenter.samsung.com: Google hasn't returned any results for this query.
app-3    | 2025-11-12 22:46:54 - serpapi.orchestrator - INFO - SerpApi query 4/10: Samsung DVE45T3400W/A3 manual filetype:pdf site:downloadcenter.samsung.com
app-3    | 2025-11-12 22:46:54 - serpapi.client - INFO - Issuing SerpApi request query=Samsung DVE45T3400W/A3 manual filetype:pdf site:downloadcenter.samsung.com location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:55 - serpapi.client - ERROR - SerpApi reported error for query=Whirlpool LE7680XSH2 manual filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:55 - serpapi.orchestrator - WARNING - SerpApi search error for query=Whirlpool LE7680XSH2 manual filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:55 - serpapi.orchestrator - INFO - SerpApi query 7/9: Whirlpool LE7680XSH2 installation manual filetype:pdf
app-1    | 2025-11-12 22:46:55 - serpapi.client - INFO - Issuing SerpApi request query=Whirlpool LE7680XSH2 installation manual filetype:pdf location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:46:55 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGMV175QFA owner's manual filetype:pdf site:frigidaire.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:55 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGMV175QFA owner's manual filetype:pdf site:frigidaire.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:55 - serpapi.orchestrator - INFO - SerpApi query 2/10: Frigidaire FGMV175QFA manual filetype:pdf site:frigidaire.com
app-4    | 2025-11-12 22:46:55 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGMV175QFA manual filetype:pdf site:frigidaire.com location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:46:56 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGMV175QFA manual filetype:pdf site:frigidaire.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:56 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGMV175QFA manual filetype:pdf site:frigidaire.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:56 - serpapi.orchestrator - INFO - SerpApi query 3/10: Frigidaire FGMV175QFA owner's manual filetype:pdf site:electroluxmedia.com
app-4    | 2025-11-12 22:46:56 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGMV175QFA owner's manual filetype:pdf site:electroluxmedia.com location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:56 - serpapi.client - ERROR - SerpApi reported error for query=Whirlpool LE7680XSH2 installation manual filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:56 - serpapi.orchestrator - WARNING - SerpApi search error for query=Whirlpool LE7680XSH2 installation manual filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:56 - serpapi.orchestrator - INFO - SerpApi query 8/9: LE7680XSH2 owner's manual filetype:pdf
app-1    | 2025-11-12 22:46:56 - serpapi.client - INFO - Issuing SerpApi request query=LE7680XSH2 owner's manual filetype:pdf location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:56 - serpapi.orchestrator - INFO - Successfully downloaded url=https://files.rheem.com/blobazrheem/wp-content/uploads/sites/2/AP21831-Rev-2-SHEG-TriBrand-UC.pdf to /app/headless-browser-scraper/temp/tmprd7h9ban/AP21831-Rev-2-SHEG-TriBrand-UC.pdf
app-4    | 2025-11-12 22:46:56 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGRF1097 owner's manual filetype:pdf site:frigidaire.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:56 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGRF1097 owner's manual filetype:pdf site:frigidaire.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:56 - serpapi.orchestrator - INFO - SerpApi query 2/10: Frigidaire FGRF1097 manual filetype:pdf site:frigidaire.com
app-4    | 2025-11-12 22:46:56 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGRF1097 manual filetype:pdf site:frigidaire.com location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:46:57 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGRF1097 manual filetype:pdf site:frigidaire.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:57 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGRF1097 manual filetype:pdf site:frigidaire.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:57 - serpapi.orchestrator - INFO - SerpApi query 3/10: Frigidaire FGRF1097 owner's manual filetype:pdf site:electroluxmedia.com
app-4    | 2025-11-12 22:46:57 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGRF1097 owner's manual filetype:pdf site:electroluxmedia.com location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:57 - serpapi.client - ERROR - SerpApi reported error for query=LE7680XSH2 owner's manual filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:57 - serpapi.orchestrator - WARNING - SerpApi search error for query=LE7680XSH2 owner's manual filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:46:57 - serpapi.orchestrator - INFO - SerpApi query 9/9: LE7680XSH2 manual filetype:pdf
app-1    | 2025-11-12 22:46:57 - serpapi.client - INFO - Issuing SerpApi request query=LE7680XSH2 manual filetype:pdf location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:46:58 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGMV175QFA owner's manual filetype:pdf site:electroluxmedia.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:58 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGMV175QFA owner's manual filetype:pdf site:electroluxmedia.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:58 - serpapi.orchestrator - INFO - SerpApi query 4/10: Frigidaire FGMV175QFA manual filetype:pdf site:electroluxmedia.com
app-4    | 2025-11-12 22:46:58 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGMV175QFA manual filetype:pdf site:electroluxmedia.com location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:46:58 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmprd7h9ban/AP21831-Rev-2-SHEG-TriBrand-UC.pdf doc_type=owner accept=True manual_signal=2 manual_tokens=5 marketing_hits=0 page_count=52 contains_model=False
app-1    | 2025-11-12 22:46:58 - serpapi.orchestrator - INFO - Validation passed for candidate url=https://files.rheem.com/blobazrheem/wp-content/uploads/sites/2/AP21831-Rev-2-SHEG-TriBrand-UC.pdf doc_type=owner score=60
app-1    | 2025-11-12 22:46:58 - serpapi.orchestrator - INFO - Candidate accepted url=https://files.rheem.com/blobazrheem/wp-content/uploads/sites/2/AP21831-Rev-2-SHEG-TriBrand-UC.pdf brand=rheem model=PROG50-38N RH60
app-1    | 2025-11-12 22:46:58 - ingest - INFO - Ingesting PDF from local path: /app/headless-browser-scraper/temp/tmprd7h9ban/AP21831-Rev-2-SHEG-TriBrand-UC.pdf
app-3    | 2025-11-12 22:46:58 - serpapi.client - ERROR - SerpApi reported error for query=Samsung DVE45T3400W/A3 manual filetype:pdf site:downloadcenter.samsung.com: Google hasn't returned any results for this query.
app-3    | 2025-11-12 22:46:58 - serpapi.orchestrator - WARNING - SerpApi search error for query=Samsung DVE45T3400W/A3 manual filetype:pdf site:downloadcenter.samsung.com: Google hasn't returned any results for this query.
app-3    | 2025-11-12 22:46:58 - serpapi.orchestrator - INFO - SerpApi query 5/10: Samsung DVE45T3400W/A3 user manual filetype:pdf
app-3    | 2025-11-12 22:46:58 - serpapi.client - INFO - Issuing SerpApi request query=Samsung DVE45T3400W/A3 user manual filetype:pdf location=Austin, Texas, United States num=10
app-1    | Cleaned up temp dir: /app/headless-browser-scraper/temp/tmprd7h9ban
app-1    | INFO:     172.18.0.3:33324 - "GET /scrape/rheem/PROG50-38N%20RH60 HTTP/1.1" 200 OK
app-4    | 2025-11-12 22:46:58 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGRF1097 owner's manual filetype:pdf site:electroluxmedia.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:58 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGRF1097 owner's manual filetype:pdf site:electroluxmedia.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:46:58 - serpapi.orchestrator - INFO - SerpApi query 4/10: Frigidaire FGRF1097 manual filetype:pdf site:electroluxmedia.com
app-4    | 2025-11-12 22:46:58 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGRF1097 manual filetype:pdf site:electroluxmedia.com location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:46:59 - serpapi.orchestrator - INFO - Successfully downloaded url=https://research.encompass.com/ZEN/sm/WM4270HWA.pdf to /app/headless-browser-scraper/temp/tmpu_peo_cj/WM4270HWA.pdf
app-3    | 2025-11-12 22:46:59 - pypdf._cmap - ERROR - Advanced encoding /UniKS-UTF16-H not implemented yet
app-3    | 2025-11-12 22:46:59 - pypdf._cmap - ERROR - Advanced encoding /UniKS-UTF16-H not implemented yet
app-3    | 2025-11-12 22:46:59 - pypdf._cmap - ERROR - Advanced encoding /UniKS-UTF16-H not implemented yet
app-3    | 2025-11-12 22:46:59 - pypdf._cmap - ERROR - Advanced encoding /UniKS-UTF16-H not implemented yet
app-3    | 2025-11-12 22:46:59 - pypdf._cmap - ERROR - Advanced encoding /UniKS-UTF16-H not implemented yet
app-3    | 2025-11-12 22:46:59 - pypdf._cmap - ERROR - Advanced encoding /UniKS-UTF16-H not implemented yet
app-3    | 2025-11-12 22:46:59 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpu_peo_cj/WM4270HWA.pdf doc_type=tech accept=False manual_signal=0 manual_tokens=3 marketing_hits=0 page_count=58 contains_model=False
app-3    | 2025-11-12 22:46:59 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpu_peo_cj/WM4270HWA.pdf reason=disallowed_doc_type:tech
app-3    | 2025-11-12 22:46:59 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://research.encompass.com/ZEN/sm/WM4270HWA.pdf brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:46:59 - serpapi.orchestrator - INFO - Attempting candidate url=https://media.flixcar.com/f360cdn/LG_Electronics-1479157310-WM4270HVA.pdf score=40 source=organic_results
app-3    | 2025-11-12 22:46:59 - serpapi.orchestrator - INFO - Downloading candidate url=https://media.flixcar.com/f360cdn/LG_Electronics-1479157310-WM4270HVA.pdf brand=lg model=WM4270HWA referer=https://media.flixcar.com/ read_timeout=15
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Successfully downloaded url=https://media.flixcar.com/f360cdn/LG_Electronics-1479157310-WM4270HVA.pdf to /app/headless-browser-scraper/temp/tmpfd7vzhpq/LG_Electronics-1479157310-WM4270HVA.pdf
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpfd7vzhpq/LG_Electronics-1479157310-WM4270HVA.pdf doc_type=owner accept=False manual_signal=0 manual_tokens=0 marketing_hits=0 page_count=92 contains_model=False
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpfd7vzhpq/LG_Electronics-1479157310-WM4270HVA.pdf reason=no_manual_keywords
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://media.flixcar.com/f360cdn/LG_Electronics-1479157310-WM4270HVA.pdf brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Attempting candidate url=https://www.energystar.gov/sites/default/files/tools/ENERGY%20STAR%20Dryer%20Webinar.pdf score=38 source=organic_results
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Downloading candidate url=https://www.energystar.gov/sites/default/files/tools/ENERGY%20STAR%20Dryer%20Webinar.pdf brand=lg model=WM4270HWA referer=https://www.energystar.gov/ read_timeout=15
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - WARNING - Download failed for url=https://www.energystar.gov/sites/default/files/tools/ENERGY%20STAR%20Dryer%20Webinar.pdf: HTTPSConnectionPool(host='www.energystar.gov', port=443): Max retries exceeded with url: /sites/default/files/tools/ENERGY%20STAR%20Dryer%20Webinar.pdf (Caused by ProxyError('Unable to connect to proxy', OSError('Tunnel connection failed: 403 Forbidden')))
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://www.energystar.gov/sites/default/files/tools/ENERGY%20STAR%20Dryer%20Webinar.pdf brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Attempting candidate url=https://research.encompass.com/ZEN/sm/WM3700HWA.pdf score=-3 source=organic_results
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Downloading candidate url=https://research.encompass.com/ZEN/sm/WM3700HWA.pdf brand=lg model=WM4270HWA referer=https://research.encompass.com/ read_timeout=15
app-3    | 2025-11-12 22:47:00 - serpapi.client - INFO - SerpApi request succeeded query=Samsung DVE45T3400W/A3 user manual filetype:pdf search_id=69150e6268386319115fa50d organic_results=6
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Collecting candidates for query=Samsung DVE45T3400W/A3 user manual filetype:pdf (search_id=69150e6268386319115fa50d)
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Collected 5 candidate(s) for query=Samsung DVE45T3400W/A3 user manual filetype:pdf (search_id=69150e6268386319115fa50d)
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Attempting candidate url=https://s1.img-b.com/build.com/mediabase/specifications/samsung/1753869/samsung-dvg45t3400-owners-manual.pdf score=41 source=organic_results
app-3    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - Downloading candidate url=https://s1.img-b.com/build.com/mediabase/specifications/samsung/1753869/samsung-dvg45t3400-owners-manual.pdf brand=samsung model=DVE45T3400W/A3 referer=https://s1.img-b.com/ read_timeout=15
app-4    | 2025-11-12 22:47:00 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGMV175QFA manual filetype:pdf site:electroluxmedia.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:00 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGMV175QFA manual filetype:pdf site:electroluxmedia.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:00 - serpapi.orchestrator - INFO - SerpApi query 5/10: Frigidaire FGMV175QFA owners manual filetype:pdf
app-4    | 2025-11-12 22:47:00 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGMV175QFA owners manual filetype:pdf location=Austin, Texas, United States num=10
app-1    | 2025-11-12 22:47:01 - serpapi.client - ERROR - SerpApi reported error for query=LE7680XSH2 manual filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:47:01 - serpapi.orchestrator - WARNING - SerpApi search error for query=LE7680XSH2 manual filetype:pdf: Google hasn't returned any results for this query.
app-1    | 2025-11-12 22:47:01 - serpapi.orchestrator - INFO - No valid SerpApi manual found for brand=whirlpool model=LE7680XSH2
app-1    | Fetching page for model LE7680XSH2...
app-1    | Using proxy server http://squid:8888
app-1    | 2025-11-12 22:47:01 - undetected_chromedriver.patcher - INFO - patching driver executable /usr/bin/chromedriver
app-1    | 2025-11-12 22:47:01 - uc - WARNING - could not detect version_main.therefore, we are assuming it is chrome 108 or higher
app-4    | 2025-11-12 22:47:01 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGRF1097 manual filetype:pdf site:electroluxmedia.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:01 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGRF1097 manual filetype:pdf site:electroluxmedia.com: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:01 - serpapi.orchestrator - INFO - SerpApi query 5/10: Frigidaire FGRF1097 owners manual filetype:pdf
app-4    | 2025-11-12 22:47:01 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGRF1097 owners manual filetype:pdf location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:47:01 - serpapi.orchestrator - INFO - Successfully downloaded url=https://s1.img-b.com/build.com/mediabase/specifications/samsung/1753869/samsung-dvg45t3400-owners-manual.pdf to /app/headless-browser-scraper/temp/tmpfquj2xan/samsung-dvg45t3400-owners-manual.pdf
app-3    | 2025-11-12 22:47:01 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpfquj2xan/samsung-dvg45t3400-owners-manual.pdf doc_type=owner accept=False manual_signal=0 manual_tokens=0 marketing_hits=0 page_count=60 contains_model=False
app-3    | 2025-11-12 22:47:01 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpfquj2xan/samsung-dvg45t3400-owners-manual.pdf reason=no_manual_keywords
app-3    | 2025-11-12 22:47:01 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://s1.img-b.com/build.com/mediabase/specifications/samsung/1753869/samsung-dvg45t3400-owners-manual.pdf brand=samsung model=DVE45T3400W/A3
app-3    | 2025-11-12 22:47:01 - serpapi.orchestrator - INFO - Attempting candidate url=https://images.webfronts.com/cache/fravodpewtxq.pdf score=40 source=organic_results
app-3    | 2025-11-12 22:47:01 - serpapi.orchestrator - INFO - Downloading candidate url=https://images.webfronts.com/cache/fravodpewtxq.pdf brand=samsung model=DVE45T3400W/A3 referer=https://images.webfronts.com/ read_timeout=15
app-3    | 2025-11-12 22:47:02 - serpapi.orchestrator - INFO - Successfully downloaded url=https://images.webfronts.com/cache/fravodpewtxq.pdf to /app/headless-browser-scraper/temp/tmp7u8dt9ga/fravodpewtxq.pdf
app-3    | 2025-11-12 22:47:02 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmp7u8dt9ga/fravodpewtxq.pdf doc_type=owner accept=False manual_signal=1 manual_tokens=1 marketing_hits=0 page_count=2 contains_model=False
app-3    | 2025-11-12 22:47:02 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmp7u8dt9ga/fravodpewtxq.pdf reason=owner_manual_too_short
app-3    | 2025-11-12 22:47:02 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://images.webfronts.com/cache/fravodpewtxq.pdf brand=samsung model=DVE45T3400W/A3
app-3    | 2025-11-12 22:47:02 - serpapi.orchestrator - INFO - Attempting candidate url=https://assets.ajmadison.com/ajmadison/itemdocs/DVE45T3400W-warranty.pdf score=39 source=organic_results
app-3    | 2025-11-12 22:47:02 - serpapi.orchestrator - INFO - Downloading candidate url=https://assets.ajmadison.com/ajmadison/itemdocs/DVE45T3400W-warranty.pdf brand=samsung model=DVE45T3400W/A3 referer=https://assets.ajmadison.com/ read_timeout=15
app-3    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - Successfully downloaded url=https://assets.ajmadison.com/ajmadison/itemdocs/DVE45T3400W-warranty.pdf to /app/headless-browser-scraper/temp/tmpvkh30mdb/DVE45T3400W-warranty.pdf
app-3    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpvkh30mdb/DVE45T3400W-warranty.pdf doc_type=parts accept=False manual_signal=0 manual_tokens=1 marketing_hits=0 page_count=2 contains_model=True
app-3    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpvkh30mdb/DVE45T3400W-warranty.pdf reason=disallowed_doc_type:parts
app-3    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://assets.ajmadison.com/ajmadison/itemdocs/DVE45T3400W-warranty.pdf brand=samsung model=DVE45T3400W/A3
app-3    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - Attempting candidate url=https://s3.amazonaws.com/productuploader-uploads/rebate/dealer_v2/staging/1716171301_2403019SA_60CU.pdf score=36 source=organic_results
app-3    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - Downloading candidate url=https://s3.amazonaws.com/productuploader-uploads/rebate/dealer_v2/staging/1716171301_2403019SA_60CU.pdf brand=samsung model=DVE45T3400W/A3 referer=https://s3.amazonaws.com/ read_timeout=15
app-4    | 2025-11-12 22:47:03 - serpapi.client - INFO - SerpApi request succeeded query=Frigidaire FGMV175QFA owners manual filetype:pdf search_id=69150e64d1a72b19de5eaa68 organic_results=8
app-4    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - Collecting candidates for query=Frigidaire FGMV175QFA owners manual filetype:pdf (search_id=69150e64d1a72b19de5eaa68)
app-4    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - Collected 8 candidate(s) for query=Frigidaire FGMV175QFA owners manual filetype:pdf (search_id=69150e64d1a72b19de5eaa68)
app-4    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - Attempting candidate url=https://device.report/m/b3b8a13a8e8cf3324846928e7d757a18a251d4ecdfa5a3ae76dedc53fa9bc9b6.pdf score=60 source=organic_results
app-4    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - Downloading candidate url=https://device.report/m/b3b8a13a8e8cf3324846928e7d757a18a251d4ecdfa5a3ae76dedc53fa9bc9b6.pdf brand=frigidaire model=FGMV175QFA referer=https://device.report/ read_timeout=15
app-4    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - Successfully downloaded url=https://device.report/m/b3b8a13a8e8cf3324846928e7d757a18a251d4ecdfa5a3ae76dedc53fa9bc9b6.pdf to /app/headless-browser-scraper/temp/tmpu8d3e1tt/b3b8a13a8e8cf3324846928e7d757a18a251d4ecdfa5a3ae76dedc53fa9bc9b6.pdf
app-3    | 2025-11-12 22:47:03 - serpapi.orchestrator - INFO - Successfully downloaded url=https://s3.amazonaws.com/productuploader-uploads/rebate/dealer_v2/staging/1716171301_2403019SA_60CU.pdf to /app/headless-browser-scraper/temp/tmp713yxehv/1716171301_2403019SA_60CU.pdf
app-3    | 2025-11-12 22:47:04 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmp713yxehv/1716171301_2403019SA_60CU.pdf doc_type=owner accept=False manual_signal=0 manual_tokens=1 marketing_hits=1 page_count=11 contains_model=False
app-3    | 2025-11-12 22:47:04 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmp713yxehv/1716171301_2403019SA_60CU.pdf reason=marketing_signals
app-3    | 2025-11-12 22:47:04 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://s3.amazonaws.com/productuploader-uploads/rebate/dealer_v2/staging/1716171301_2403019SA_60CU.pdf brand=samsung model=DVE45T3400W/A3
app-3    | 2025-11-12 22:47:04 - serpapi.orchestrator - INFO - Attempting candidate url=https://m.media-amazon.com/images/I/C1LWlz+5QOL.pdf score=-42 source=organic_results
app-3    | 2025-11-12 22:47:04 - serpapi.orchestrator - INFO - Downloading candidate url=https://m.media-amazon.com/images/I/C1LWlz+5QOL.pdf brand=samsung model=DVE45T3400W/A3 referer=https://m.media-amazon.com/ read_timeout=15
app-3    | 2025-11-12 22:47:05 - serpapi.orchestrator - INFO - Successfully downloaded url=https://research.encompass.com/ZEN/sm/WM3700HWA.pdf to /app/headless-browser-scraper/temp/tmpgisvvhsj/WM3700HWA.pdf
app-3    | 2025-11-12 22:47:05 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpgisvvhsj/WM3700HWA.pdf doc_type=tech accept=False manual_signal=0 manual_tokens=3 marketing_hits=0 page_count=54 contains_model=False
app-3    | 2025-11-12 22:47:05 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpgisvvhsj/WM3700HWA.pdf reason=disallowed_doc_type:tech
app-3    | 2025-11-12 22:47:05 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://research.encompass.com/ZEN/sm/WM3700HWA.pdf brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:47:05 - serpapi.orchestrator - INFO - SerpApi query 6/10: LG WM4270HWA owners manual filetype:pdf
app-3    | 2025-11-12 22:47:05 - serpapi.client - INFO - Issuing SerpApi request query=LG WM4270HWA owners manual filetype:pdf location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:47:06 - serpapi.orchestrator - INFO - Downloading candidate url=https://www.whirlpool.com/content/dam/business-unit/whirlpool/en-us/marketing-content/site-assets/global-assets/documents/whirlpool-brand-catalog-2019-Q2.pdf brand=whirlpool model=WEG750H0H referer=https://www.whirlpool.com/ read_timeout=15
app-4    | 2025-11-12 22:47:06 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGRF1097 owners manual filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:06 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGRF1097 owners manual filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:06 - serpapi.orchestrator - INFO - SerpApi query 6/10: Frigidaire FGRF1097 installation instructions filetype:pdf
app-4    | 2025-11-12 22:47:06 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGRF1097 installation instructions filetype:pdf location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:47:06 - serpapi.client - INFO - SerpApi request succeeded query=LG WM4270HWA owners manual filetype:pdf search_id=69150e69d3fb85d4cbd17aa0 organic_results=9
app-3    | 2025-11-12 22:47:06 - serpapi.orchestrator - INFO - Collecting candidates for query=LG WM4270HWA owners manual filetype:pdf (search_id=69150e69d3fb85d4cbd17aa0)
app-3    | 2025-11-12 22:47:06 - serpapi.orchestrator - INFO - Collected 5 candidate(s) for query=LG WM4270HWA owners manual filetype:pdf (search_id=69150e69d3fb85d4cbd17aa0)
app-3    | 2025-11-12 22:47:06 - serpapi.orchestrator - INFO - Attempting candidate url=https://cdn.avbportal.com/magento-media/promotions/2015_promos/pdf/09_lg_0915_b.pdf score=54 source=organic_results
app-3    | 2025-11-12 22:47:06 - serpapi.orchestrator - INFO - Downloading candidate url=https://cdn.avbportal.com/magento-media/promotions/2015_promos/pdf/09_lg_0915_b.pdf brand=lg model=WM4270HWA referer=https://cdn.avbportal.com/ read_timeout=15
app-3    | INFO:     172.18.0.3:38224 - "GET /health HTTP/1.1" 200 OK
app-3    | 2025-11-12 22:47:07 - serpapi.orchestrator - INFO - Successfully downloaded url=https://cdn.avbportal.com/magento-media/promotions/2015_promos/pdf/09_lg_0915_b.pdf to /app/headless-browser-scraper/temp/tmpoxror942/09_lg_0915_b.pdf
app-3    | 2025-11-12 22:47:07 - serpapi.orchestrator - INFO - Validation failed for candidate url=https://cdn.avbportal.com/magento-media/promotions/2015_promos/pdf/09_lg_0915_b.pdf
app-3    | 2025-11-12 22:47:07 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://cdn.avbportal.com/magento-media/promotions/2015_promos/pdf/09_lg_0915_b.pdf brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:47:07 - serpapi.orchestrator - INFO - Attempting candidate url=https://www.aafa.org/wp-content/uploads/2022/08/freshaair-asthma-allergy-magazine-spring-2021.pdf score=37 source=organic_results
app-3    | 2025-11-12 22:47:07 - serpapi.orchestrator - INFO - Downloading candidate url=https://www.aafa.org/wp-content/uploads/2022/08/freshaair-asthma-allergy-magazine-spring-2021.pdf brand=lg model=WM4270HWA referer=https://www.aafa.org/ read_timeout=15
app-3    | 2025-11-12 22:47:07 - serpapi.orchestrator - INFO - Successfully downloaded url=https://www.aafa.org/wp-content/uploads/2022/08/freshaair-asthma-allergy-magazine-spring-2021.pdf to /app/headless-browser-scraper/temp/tmpwtl4a16r/freshaair-asthma-allergy-magazine-spring-2021.pdf
app-4    | 2025-11-12 22:47:08 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGRF1097 installation instructions filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:08 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGRF1097 installation instructions filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - SerpApi query 7/10: Frigidaire FGRF1097 owner's manual filetype:pdf
app-4    | 2025-11-12 22:47:08 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGRF1097 owner's manual filetype:pdf location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpu8d3e1tt/b3b8a13a8e8cf3324846928e7d757a18a251d4ecdfa5a3ae76dedc53fa9bc9b6.pdf doc_type=owner accept=False manual_signal=0 manual_tokens=2 marketing_hits=1 page_count=8 contains_model=True
app-4    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpu8d3e1tt/b3b8a13a8e8cf3324846928e7d757a18a251d4ecdfa5a3ae76dedc53fa9bc9b6.pdf reason=marketing_signals
app-4    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://device.report/m/b3b8a13a8e8cf3324846928e7d757a18a251d4ecdfa5a3ae76dedc53fa9bc9b6.pdf brand=frigidaire model=FGMV175QFA
app-4    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Attempting candidate url=https://www.classaction.org/media/mauro-v-electrolux-home-products-inc-et-al.pdf score=55 source=organic_results
app-4    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Downloading candidate url=https://www.classaction.org/media/mauro-v-electrolux-home-products-inc-et-al.pdf brand=frigidaire model=FGMV175QFA referer=https://www.classaction.org/ read_timeout=15
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpwtl4a16r/freshaair-asthma-allergy-magazine-spring-2021.pdf doc_type=owner accept=False manual_signal=0 manual_tokens=1 marketing_hits=1 page_count=16 contains_model=False
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpwtl4a16r/freshaair-asthma-allergy-magazine-spring-2021.pdf reason=marketing_signals
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://www.aafa.org/wp-content/uploads/2022/08/freshaair-asthma-allergy-magazine-spring-2021.pdf brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Attempting candidate url=https://cdn.avbportal.com/magento-media/promotions/2016_promos/pdf/11_lg_1116ped.pdf score=35 source=organic_results
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Downloading candidate url=https://cdn.avbportal.com/magento-media/promotions/2016_promos/pdf/11_lg_1116ped.pdf brand=lg model=WM4270HWA referer=https://cdn.avbportal.com/ read_timeout=15
squid-1  | 2025/11/12 22:47:08| ERROR: Connection to upstream1 failed
squid-1  |     current master transaction: master821
squid-1  | 2025/11/12 22:47:08| ERROR: Connection to upstream2 failed
squid-1  |     current master transaction: master821
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Successfully downloaded url=https://cdn.avbportal.com/magento-media/promotions/2016_promos/pdf/11_lg_1116ped.pdf to /app/headless-browser-scraper/temp/tmpwy_5j617/11_lg_1116ped.pdf
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Validation failed for candidate url=https://cdn.avbportal.com/magento-media/promotions/2016_promos/pdf/11_lg_1116ped.pdf
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://cdn.avbportal.com/magento-media/promotions/2016_promos/pdf/11_lg_1116ped.pdf brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Attempting candidate url=https://cdn.avbportal.com/magento-media/promotions/2016_promos/pdf/02_lg_0216_a.pdf score=33 source=organic_results
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Downloading candidate url=https://cdn.avbportal.com/magento-media/promotions/2016_promos/pdf/02_lg_0216_a.pdf brand=lg model=WM4270HWA referer=https://cdn.avbportal.com/ read_timeout=15
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Successfully downloaded url=https://cdn.avbportal.com/magento-media/promotions/2016_promos/pdf/02_lg_0216_a.pdf to /app/headless-browser-scraper/temp/tmpgnu3jwv6/02_lg_0216_a.pdf
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Validation failed for candidate url=https://cdn.avbportal.com/magento-media/promotions/2016_promos/pdf/02_lg_0216_a.pdf
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://cdn.avbportal.com/magento-media/promotions/2016_promos/pdf/02_lg_0216_a.pdf brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Attempting candidate url=https://pdf.lowes.com/productdocuments/31b62af6-6e7f-4f37-9213-6f50433a0c68/04026568.pdf score=30 source=inline_images
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Downloading candidate url=https://pdf.lowes.com/productdocuments/31b62af6-6e7f-4f37-9213-6f50433a0c68/04026568.pdf brand=lg model=WM4270HWA referer=https://pdf.lowes.com/ read_timeout=15
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - WARNING - Download failed for url=https://pdf.lowes.com/productdocuments/31b62af6-6e7f-4f37-9213-6f50433a0c68/04026568.pdf: HTTPSConnectionPool(host='pdf.lowes.com', port=443): Max retries exceeded with url: /productdocuments/31b62af6-6e7f-4f37-9213-6f50433a0c68/04026568.pdf (Caused by ProxyError('Unable to connect to proxy', OSError('Tunnel connection failed: 403 Forbidden')))
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://pdf.lowes.com/productdocuments/31b62af6-6e7f-4f37-9213-6f50433a0c68/04026568.pdf brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:47:08 - serpapi.orchestrator - INFO - SerpApi query 7/10: LG WM4270HWA owner's manual filetype:pdf
app-3    | 2025-11-12 22:47:08 - serpapi.client - INFO - Issuing SerpApi request query=LG WM4270HWA owner's manual filetype:pdf location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:47:09 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGRF1097 owner's manual filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:09 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGRF1097 owner's manual filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:09 - serpapi.orchestrator - INFO - SerpApi query 8/10: Frigidaire FGRF1097 manual filetype:pdf
app-4    | 2025-11-12 22:47:09 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGRF1097 manual filetype:pdf location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:47:09 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGRF1097 manual filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:09 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGRF1097 manual filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:09 - serpapi.orchestrator - INFO - SerpApi query 9/10: Frigidaire FGRF1097 installation manual filetype:pdf
app-4    | 2025-11-12 22:47:09 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGRF1097 installation manual filetype:pdf location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:47:09 - serpapi.orchestrator - INFO - Successfully downloaded url=https://www.classaction.org/media/mauro-v-electrolux-home-products-inc-et-al.pdf to /app/headless-browser-scraper/temp/tmpzmflwia5/mauro-v-electrolux-home-products-inc-et-al.pdf
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpzmflwia5/mauro-v-electrolux-home-products-inc-et-al.pdf doc_type=owner accept=False manual_signal=0 manual_tokens=0 marketing_hits=0 page_count=175 contains_model=False
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpzmflwia5/mauro-v-electrolux-home-products-inc-et-al.pdf reason=no_manual_keywords
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://www.classaction.org/media/mauro-v-electrolux-home-products-inc-et-al.pdf brand=frigidaire model=FGMV175QFA
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Attempting candidate url=https://irp.cdn-website.com/16b21435/files/uploaded/44442734.pdf score=41 source=organic_results
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Downloading candidate url=https://irp.cdn-website.com/16b21435/files/uploaded/44442734.pdf brand=frigidaire model=FGMV175QFA referer=https://irp.cdn-website.com/ read_timeout=15
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Successfully downloaded url=https://irp.cdn-website.com/16b21435/files/uploaded/44442734.pdf to /app/headless-browser-scraper/temp/tmpfo2oz696/44442734.pdf
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Validation failed for candidate url=https://irp.cdn-website.com/16b21435/files/uploaded/44442734.pdf
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://irp.cdn-website.com/16b21435/files/uploaded/44442734.pdf brand=frigidaire model=FGMV175QFA
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Attempting candidate url=https://pdf.lowes.com/productdocuments/89527ee2-5c7c-44de-9e0d-52ac2db6a884/61007491.pdf score=37 source=organic_results
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Downloading candidate url=https://pdf.lowes.com/productdocuments/89527ee2-5c7c-44de-9e0d-52ac2db6a884/61007491.pdf brand=frigidaire model=FGMV175QFA referer=https://pdf.lowes.com/ read_timeout=15
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - WARNING - Download failed for url=https://pdf.lowes.com/productdocuments/89527ee2-5c7c-44de-9e0d-52ac2db6a884/61007491.pdf: HTTPSConnectionPool(host='pdf.lowes.com', port=443): Max retries exceeded with url: /productdocuments/89527ee2-5c7c-44de-9e0d-52ac2db6a884/61007491.pdf (Caused by ProxyError('Unable to connect to proxy', OSError('Tunnel connection failed: 403 Forbidden')))
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://pdf.lowes.com/productdocuments/89527ee2-5c7c-44de-9e0d-52ac2db6a884/61007491.pdf brand=frigidaire model=FGMV175QFA
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Attempting candidate url=https://irp.cdn-website.com/569bb1b0/files/uploaded/655835.pdf score=34 source=organic_results
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Downloading candidate url=https://irp.cdn-website.com/569bb1b0/files/uploaded/655835.pdf brand=frigidaire model=FGMV175QFA referer=https://irp.cdn-website.com/ read_timeout=15
app-3    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Successfully downloaded url=https://m.media-amazon.com/images/I/C1LWlz+5QOL.pdf to /app/headless-browser-scraper/temp/tmpv79jh0qy/C1LWlz+5QOL.pdf
app-3    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Validation failed for candidate url=https://m.media-amazon.com/images/I/C1LWlz+5QOL.pdf
app-3    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://m.media-amazon.com/images/I/C1LWlz+5QOL.pdf brand=samsung model=DVE45T3400W/A3
app-3    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - SerpApi query 6/10: Samsung DVE45T3400W/A3 installation manual filetype:pdf
app-3    | 2025-11-12 22:47:10 - serpapi.client - INFO - Issuing SerpApi request query=Samsung DVE45T3400W/A3 installation manual filetype:pdf location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Successfully downloaded url=https://irp.cdn-website.com/569bb1b0/files/uploaded/655835.pdf to /app/headless-browser-scraper/temp/tmpxkz4_xow/655835.pdf
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Validation failed for candidate url=https://irp.cdn-website.com/569bb1b0/files/uploaded/655835.pdf
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://irp.cdn-website.com/569bb1b0/files/uploaded/655835.pdf brand=frigidaire model=FGMV175QFA
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - SerpApi query 6/10: Frigidaire FGMV175QFA installation instructions filetype:pdf
app-4    | 2025-11-12 22:47:10 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGMV175QFA installation instructions filetype:pdf location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:47:10 - serpapi.client - ERROR - SerpApi reported error for query=Frigidaire FGRF1097 installation manual filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - WARNING - SerpApi search error for query=Frigidaire FGRF1097 installation manual filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:10 - serpapi.orchestrator - INFO - SerpApi query 10/10: FGRF1097 owner's manual filetype:pdf
app-4    | 2025-11-12 22:47:10 - serpapi.client - INFO - Issuing SerpApi request query=FGRF1097 owner's manual filetype:pdf location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:47:12 - serpapi.client - INFO - SerpApi request succeeded query=Samsung DVE45T3400W/A3 installation manual filetype:pdf search_id=69150e6e634a630ed79f57a0 organic_results=5
app-3    | 2025-11-12 22:47:12 - serpapi.orchestrator - INFO - Collecting candidates for query=Samsung DVE45T3400W/A3 installation manual filetype:pdf (search_id=69150e6e634a630ed79f57a0)
app-3    | 2025-11-12 22:47:12 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=Samsung DVE45T3400W/A3 installation manual filetype:pdf (search_id=69150e6e634a630ed79f57a0)
app-3    | 2025-11-12 22:47:12 - serpapi.orchestrator - INFO - No PDF candidates returned for query=Samsung DVE45T3400W/A3 installation manual filetype:pdf
app-3    | 2025-11-12 22:47:12 - serpapi.orchestrator - INFO - SerpApi query 7/10: Samsung DVE45T3400W/A3 owner's manual filetype:pdf
app-3    | 2025-11-12 22:47:12 - serpapi.client - INFO - Issuing SerpApi request query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf location=Austin, Texas, United States num=10
squid-1  | 2025/11/12 22:47:12| ERROR: Connection to upstream2 failed
squid-1  |     current master transaction: master847
squid-1  | 2025/11/12 22:47:12| ERROR: Connection to upstream1 failed
squid-1  |     current master transaction: master847
app-4    | 2025-11-12 22:47:13 - serpapi.client - ERROR - SerpApi reported error for query=FGRF1097 owner's manual filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:13 - serpapi.orchestrator - WARNING - SerpApi search error for query=FGRF1097 owner's manual filetype:pdf: Google hasn't returned any results for this query.
app-4    | 2025-11-12 22:47:13 - serpapi.orchestrator - INFO - No valid SerpApi manual found for brand=frigidaire model=FGRF1097
app-4    | Using proxy server http://squid:8888
app-4    | 2025-11-12 22:47:13 - undetected_chromedriver.patcher - INFO - patching driver executable /usr/bin/chromedriver
app-4    | 2025-11-12 22:47:13 - uc - WARNING - could not detect version_main.therefore, we are assuming it is chrome 108 or higher
app-3    | 2025-11-12 22:47:13 - serpapi.client - INFO - SerpApi request succeeded query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf search_id=69150e7095e950865f43c308 organic_results=6
app-3    | 2025-11-12 22:47:13 - serpapi.orchestrator - INFO - Collecting candidates for query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf (search_id=69150e7095e950865f43c308)
app-3    | 2025-11-12 22:47:13 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf (search_id=69150e7095e950865f43c308)
app-3    | 2025-11-12 22:47:13 - serpapi.orchestrator - INFO - No PDF candidates returned for query=Samsung DVE45T3400W/A3 owner's manual filetype:pdf
app-3    | 2025-11-12 22:47:13 - serpapi.orchestrator - INFO - SerpApi query 8/10: Samsung DVE45T3400W/A3 manual filetype:pdf
app-3    | 2025-11-12 22:47:13 - serpapi.client - INFO - Issuing SerpApi request query=Samsung DVE45T3400W/A3 manual filetype:pdf location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:47:13 - serpapi.client - INFO - SerpApi request succeeded query=LG WM4270HWA owner's manual filetype:pdf search_id=69150e6cc2034876cbab4f39 organic_results=9
app-3    | 2025-11-12 22:47:13 - serpapi.orchestrator - INFO - Collecting candidates for query=LG WM4270HWA owner's manual filetype:pdf (search_id=69150e6cc2034876cbab4f39)
app-3    | 2025-11-12 22:47:13 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=LG WM4270HWA owner's manual filetype:pdf (search_id=69150e6cc2034876cbab4f39)
app-3    | 2025-11-12 22:47:13 - serpapi.orchestrator - INFO - No PDF candidates returned for query=LG WM4270HWA owner's manual filetype:pdf
app-3    | 2025-11-12 22:47:13 - serpapi.orchestrator - INFO - SerpApi query 8/10: LG WM4270HWA installation manual filetype:pdf
app-3    | 2025-11-12 22:47:13 - serpapi.client - INFO - Issuing SerpApi request query=LG WM4270HWA installation manual filetype:pdf location=Austin, Texas, United States num=10
app-4    | Trying direct URL for model FGRF1097...
app-4    | 2025-11-12 22:47:14 - serpapi.client - INFO - SerpApi request succeeded query=Frigidaire FGMV175QFA installation instructions filetype:pdf search_id=69150e6e88de926685957b15 organic_results=7
app-4    | 2025-11-12 22:47:14 - serpapi.orchestrator - INFO - Collecting candidates for query=Frigidaire FGMV175QFA installation instructions filetype:pdf (search_id=69150e6e88de926685957b15)
app-4    | 2025-11-12 22:47:14 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=Frigidaire FGMV175QFA installation instructions filetype:pdf (search_id=69150e6e88de926685957b15)
app-4    | 2025-11-12 22:47:14 - serpapi.orchestrator - INFO - No PDF candidates returned for query=Frigidaire FGMV175QFA installation instructions filetype:pdf
app-4    | 2025-11-12 22:47:14 - serpapi.orchestrator - INFO - SerpApi query 7/10: Frigidaire FGMV175QFA owner's manual filetype:pdf
app-4    | 2025-11-12 22:47:14 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGMV175QFA owner's manual filetype:pdf location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:47:15 - serpapi.client - INFO - SerpApi request succeeded query=LG WM4270HWA installation manual filetype:pdf search_id=69150e716372f3cc58cb9301 organic_results=5
app-3    | 2025-11-12 22:47:15 - serpapi.orchestrator - INFO - Collecting candidates for query=LG WM4270HWA installation manual filetype:pdf (search_id=69150e716372f3cc58cb9301)
app-3    | 2025-11-12 22:47:15 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=LG WM4270HWA installation manual filetype:pdf (search_id=69150e716372f3cc58cb9301)
app-3    | 2025-11-12 22:47:15 - serpapi.orchestrator - INFO - No PDF candidates returned for query=LG WM4270HWA installation manual filetype:pdf
app-3    | 2025-11-12 22:47:15 - serpapi.orchestrator - INFO - SerpApi query 9/10: WM4270HWA owner's manual filetype:pdf
app-3    | 2025-11-12 22:47:15 - serpapi.client - INFO - Issuing SerpApi request query=WM4270HWA owner's manual filetype:pdf location=Austin, Texas, United States num=10
app-4    | Current URL after navigation: https://www.frigidaire.com/en/p/owner-center/product-support/FGRF1097
app-4    | 2025-11-12 22:47:16 - serpapi.client - INFO - SerpApi request succeeded query=Frigidaire FGMV175QFA owner's manual filetype:pdf search_id=69150e72d6eb729133eccfe6 organic_results=8
app-4    | 2025-11-12 22:47:16 - serpapi.orchestrator - INFO - Collecting candidates for query=Frigidaire FGMV175QFA owner's manual filetype:pdf (search_id=69150e72d6eb729133eccfe6)
app-4    | 2025-11-12 22:47:16 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=Frigidaire FGMV175QFA owner's manual filetype:pdf (search_id=69150e72d6eb729133eccfe6)
app-4    | 2025-11-12 22:47:16 - serpapi.orchestrator - INFO - No PDF candidates returned for query=Frigidaire FGMV175QFA owner's manual filetype:pdf
app-4    | 2025-11-12 22:47:16 - serpapi.orchestrator - INFO - SerpApi query 8/10: Frigidaire FGMV175QFA manual filetype:pdf
app-4    | 2025-11-12 22:47:16 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGMV175QFA manual filetype:pdf location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:47:16 - serpapi.client - INFO - SerpApi request succeeded query=WM4270HWA owner's manual filetype:pdf search_id=69150e73e9639b175d310246 organic_results=10
app-3    | 2025-11-12 22:47:16 - serpapi.orchestrator - INFO - Collecting candidates for query=WM4270HWA owner's manual filetype:pdf (search_id=69150e73e9639b175d310246)
app-3    | 2025-11-12 22:47:16 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=WM4270HWA owner's manual filetype:pdf (search_id=69150e73e9639b175d310246)
app-3    | 2025-11-12 22:47:16 - serpapi.orchestrator - INFO - No PDF candidates returned for query=WM4270HWA owner's manual filetype:pdf
app-3    | 2025-11-12 22:47:16 - serpapi.orchestrator - INFO - SerpApi query 10/10: WM4270HWA manual filetype:pdf
app-3    | 2025-11-12 22:47:16 - serpapi.client - INFO - Issuing SerpApi request query=WM4270HWA manual filetype:pdf location=Austin, Texas, United States num=10
app-2    | INFO:     127.0.0.1:51096 - "GET /health HTTP/1.1" 200 OK
app-1    | Navigating to: https://www.whirlpool.com/results.html?term=LE7680XSH2
app-1    | Current URL: https://www.whirlpool.com/results.html?term=LE7680XSH2&tab=clp&plp=&plpView=list&clp=&currentPage=0
app-1    | Waiting for page elements to load...
app-1    | An error occurred while scraping for model LE7680XSH2: Message:
app-1    | Stacktrace:
app-1    | #0 0x62df896fdaea <unknown>
app-1    | #1 0x62df89149cdb <unknown>
app-1    | #2 0x62df8919c6c4 <unknown>
app-1    | #3 0x62df8919c901 <unknown>
app-1    | #4 0x62df891eb8b4 <unknown>
app-1    | #5 0x62df891e8c87 <unknown>
app-1    | #6 0x62df8918eaca <unknown>
app-1    | #7 0x62df8918f7d1 <unknown>
app-1    | #8 0x62df896c4ab9 <unknown>
app-1    | #9 0x62df896c7a8c <unknown>
app-1    | #10 0x62df896add49 <unknown>
app-1    | #11 0x62df896c8685 <unknown>
app-1    | #12 0x62df896956c3 <unknown>
app-1    | #13 0x62df896ea7d8 <unknown>
app-1    | #14 0x62df896ea9b3 <unknown>
app-1    | #15 0x62df896fca83 <unknown>
app-1    | #16 0x7e450be12aa4 <unknown>
app-1    | #17 0x7e450be9fa64 __clone
app-1    |
app-1    | Owner's Manual link not found for LE7680XSH2 on search page, trying direct owners-center URL...
app-1    | Navigated to direct URL: https://www.whirlpool.com/owners-center-pdp.LE7680XSH2.html
app-1    | Direct page loaded.
app-1    | Searching for Owner's Manual link using data-doc-type
app-1    | INFO:     127.0.0.1:51110 - "GET /health HTTP/1.1" 200 OK
app-4    | 2025-11-12 22:47:18 - serpapi.client - INFO - SerpApi request succeeded query=Frigidaire FGMV175QFA manual filetype:pdf search_id=69150e74b9fc5f00d8bd1b7c organic_results=6
app-4    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - Collecting candidates for query=Frigidaire FGMV175QFA manual filetype:pdf (search_id=69150e74b9fc5f00d8bd1b7c)
app-4    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=Frigidaire FGMV175QFA manual filetype:pdf (search_id=69150e74b9fc5f00d8bd1b7c)
app-4    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - No PDF candidates returned for query=Frigidaire FGMV175QFA manual filetype:pdf
app-4    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - SerpApi query 9/10: Frigidaire FGMV175QFA installation manual filetype:pdf
app-4    | 2025-11-12 22:47:18 - serpapi.client - INFO - Issuing SerpApi request query=Frigidaire FGMV175QFA installation manual filetype:pdf location=Austin, Texas, United States num=10
app-3    | INFO:     127.0.0.1:51124 - "GET /health HTTP/1.1" 200 OK
app-3    | 2025-11-12 22:47:18 - serpapi.client - INFO - SerpApi request succeeded query=WM4270HWA manual filetype:pdf search_id=69150e74a68855753298e6ec organic_results=6
app-3    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - Collecting candidates for query=WM4270HWA manual filetype:pdf (search_id=69150e74a68855753298e6ec)
app-3    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - Collected 1 candidate(s) for query=WM4270HWA manual filetype:pdf (search_id=69150e74a68855753298e6ec)
app-3    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - Attempting candidate url=https://images.thdstatic.com/catalog/pdfImages/bc/bc5a499a-ecd5-42a9-98fc-b31aedd93199.pdf score=37 source=organic_results
app-3    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - Downloading candidate url=https://images.thdstatic.com/catalog/pdfImages/bc/bc5a499a-ecd5-42a9-98fc-b31aedd93199.pdf brand=lg model=WM4270HWA referer=https://images.thdstatic.com/ read_timeout=15
app-4    | INFO:     127.0.0.1:44924 - "GET /health HTTP/1.1" 200 OK
app-3    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - Successfully downloaded url=https://images.thdstatic.com/catalog/pdfImages/bc/bc5a499a-ecd5-42a9-98fc-b31aedd93199.pdf to /app/headless-browser-scraper/temp/tmpru5ml4cp/bc5a499a-ecd5-42a9-98fc-b31aedd93199.pdf
app-3    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpru5ml4cp/bc5a499a-ecd5-42a9-98fc-b31aedd93199.pdf doc_type=owner accept=False manual_signal=0 manual_tokens=1 marketing_hits=0 page_count=1 contains_model=True
app-3    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpru5ml4cp/bc5a499a-ecd5-42a9-98fc-b31aedd93199.pdf reason=owner_manual_too_short
app-3    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://images.thdstatic.com/catalog/pdfImages/bc/bc5a499a-ecd5-42a9-98fc-b31aedd93199.pdf brand=lg model=WM4270HWA
app-3    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - No valid SerpApi manual found for brand=lg model=WM4270HWA
app-3    | Using proxy server http://squid:8888
app-3    | 2025-11-12 22:47:18 - undetected_chromedriver.patcher - INFO - patching driver executable /usr/bin/chromedriver
app-3    | 2025-11-12 22:47:18 - uc - WARNING - could not detect version_main.therefore, we are assuming it is chrome 108 or higher
app-4    | 2025-11-12 22:47:18 - serpapi.client - INFO - SerpApi request succeeded query=Frigidaire FGMV175QFA installation manual filetype:pdf search_id=69150e768ffd7b452e75f39d organic_results=5
app-4    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - Collecting candidates for query=Frigidaire FGMV175QFA installation manual filetype:pdf (search_id=69150e768ffd7b452e75f39d)
app-4    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=Frigidaire FGMV175QFA installation manual filetype:pdf (search_id=69150e768ffd7b452e75f39d)
app-4    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - No PDF candidates returned for query=Frigidaire FGMV175QFA installation manual filetype:pdf
app-4    | 2025-11-12 22:47:18 - serpapi.orchestrator - INFO - SerpApi query 10/10: FGMV175QFA owner's manual filetype:pdf
app-4    | 2025-11-12 22:47:18 - serpapi.client - INFO - Issuing SerpApi request query=FGMV175QFA owner's manual filetype:pdf location=Austin, Texas, United States num=10
app-4    | 2025-11-12 22:47:19 - serpapi.client - INFO - SerpApi request succeeded query=FGMV175QFA owner's manual filetype:pdf search_id=69150e765b92f847dfdb3356 organic_results=8
app-4    | 2025-11-12 22:47:19 - serpapi.orchestrator - INFO - Collecting candidates for query=FGMV175QFA owner's manual filetype:pdf (search_id=69150e765b92f847dfdb3356)
app-4    | 2025-11-12 22:47:19 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=FGMV175QFA owner's manual filetype:pdf (search_id=69150e765b92f847dfdb3356)
app-4    | 2025-11-12 22:47:19 - serpapi.orchestrator - INFO - No PDF candidates returned for query=FGMV175QFA owner's manual filetype:pdf
app-4    | 2025-11-12 22:47:19 - serpapi.orchestrator - INFO - No valid SerpApi manual found for brand=frigidaire model=FGMV175QFA
app-4    | Using proxy server http://squid:8888
app-4    | 2025-11-12 22:47:19 - uc - WARNING - could not detect version_main.therefore, we are assuming it is chrome 108 or higher
app-3    | Fetching page for model WM4270HWA...
app-3    | 2025-11-12 22:47:21 - serpapi.orchestrator - WARNING - Download timed out while reading url=https://www.whirlpool.com/content/dam/business-unit/whirlpool/en-us/marketing-content/site-assets/global-assets/documents/whirlpool-brand-catalog-2019-Q2.pdf host=www.whirlpool.com read_timeout=15 error=HTTPSConnectionPool(host='www.whirlpool.com', port=443): Read timed out. (read timeout=15)
app-3    | 2025-11-12 22:47:21 - serpapi.orchestrator - INFO - Attempting headless fallback download for url=https://www.whirlpool.com/content/dam/business-unit/whirlpool/en-us/marketing-content/site-assets/global-assets/documents/whirlpool-brand-catalog-2019-Q2.pdf
app-3    | Using proxy server http://squid:8888
app-3    | 2025-11-12 22:47:21 - uc - WARNING - could not detect version_main.therefore, we are assuming it is chrome 108 or higher
app-3    | 2025-11-12 22:47:21 - serpapi.client - INFO - SerpApi request succeeded query=Samsung DVE45T3400W/A3 manual filetype:pdf search_id=69150e71bca7e5c0e85d9d8b organic_results=5
app-3    | 2025-11-12 22:47:21 - serpapi.orchestrator - INFO - Collecting candidates for query=Samsung DVE45T3400W/A3 manual filetype:pdf (search_id=69150e71bca7e5c0e85d9d8b)
app-3    | 2025-11-12 22:47:21 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=Samsung DVE45T3400W/A3 manual filetype:pdf (search_id=69150e71bca7e5c0e85d9d8b)
app-3    | 2025-11-12 22:47:21 - serpapi.orchestrator - INFO - No PDF candidates returned for query=Samsung DVE45T3400W/A3 manual filetype:pdf
app-3    | 2025-11-12 22:47:21 - serpapi.orchestrator - INFO - SerpApi query 9/10: DVE45T3400W/A3 owner's manual filetype:pdf
app-3    | 2025-11-12 22:47:21 - serpapi.client - INFO - Issuing SerpApi request query=DVE45T3400W/A3 owner's manual filetype:pdf location=Austin, Texas, United States num=10
app-3    | 2025-11-12 22:47:24 - serpapi.client - INFO - SerpApi request succeeded query=DVE45T3400W/A3 owner's manual filetype:pdf search_id=69150e794fa3ba1ed97c31b6 organic_results=6
app-3    | 2025-11-12 22:47:24 - serpapi.orchestrator - INFO - Collecting candidates for query=DVE45T3400W/A3 owner's manual filetype:pdf (search_id=69150e794fa3ba1ed97c31b6)
app-3    | 2025-11-12 22:47:24 - serpapi.orchestrator - INFO - Collected 1 candidate(s) for query=DVE45T3400W/A3 owner's manual filetype:pdf (search_id=69150e794fa3ba1ed97c31b6)
app-3    | 2025-11-12 22:47:24 - serpapi.orchestrator - INFO - Attempting candidate url=https://s3.amazonaws.com/productuploader-uploads/rebate/dealer_v2/staging/1714356441_2403019SA_23HA.pdf score=36 source=organic_results
app-3    | 2025-11-12 22:47:24 - serpapi.orchestrator - INFO - Downloading candidate url=https://s3.amazonaws.com/productuploader-uploads/rebate/dealer_v2/staging/1714356441_2403019SA_23HA.pdf brand=samsung model=DVE45T3400W/A3 referer=https://s3.amazonaws.com/ read_timeout=15
app-3    | 2025-11-12 22:47:25 - serpapi.orchestrator - INFO - Successfully downloaded url=https://s3.amazonaws.com/productuploader-uploads/rebate/dealer_v2/staging/1714356441_2403019SA_23HA.pdf to /app/headless-browser-scraper/temp/tmpq99lqhdh/1714356441_2403019SA_23HA.pdf
app-3    | 2025-11-12 22:47:25 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpq99lqhdh/1714356441_2403019SA_23HA.pdf doc_type=owner accept=False manual_signal=0 manual_tokens=1 marketing_hits=1 page_count=11 contains_model=False
app-3    | 2025-11-12 22:47:25 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpq99lqhdh/1714356441_2403019SA_23HA.pdf reason=marketing_signals
app-3    | 2025-11-12 22:47:25 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://s3.amazonaws.com/productuploader-uploads/rebate/dealer_v2/staging/1714356441_2403019SA_23HA.pdf brand=samsung model=DVE45T3400W/A3
app-3    | 2025-11-12 22:47:25 - serpapi.orchestrator - INFO - SerpApi query 10/10: DVE45T3400W/A3 manual filetype:pdf
app-3    | 2025-11-12 22:47:25 - serpapi.client - INFO - Issuing SerpApi request query=DVE45T3400W/A3 manual filetype:pdf location=Austin, Texas, United States num=10
squid-1  | 2025/11/12 22:47:29| ERROR: Connection to upstream2 failed
squid-1  |     current master transaction: master2272
squid-1  | 2025/11/12 22:47:29| ERROR: Connection to upstream1 failed
squid-1  |     current master transaction: master2272
app-3    | Current URL: https://www.lg.com/us/support/product/WM4270HWA
app-3    | Page title: LG Electronics & Home Appliances | Shop Now | LG USA
app-3    | Guide error found: True
app-3    | 404 page detected: True
app-3    | Guide error detected for WM4270HWA, retrying with lg- prefix...
app-3    | 2025-11-12 22:47:30 - serpapi.headless_pdf_fetcher - INFO - Headless PDF navigation url=https://www.whirlpool.com/content/dam/business-unit/whirlpool/en-us/marketing-content/site-assets/global-assets/documents/whirlpool-brand-catalog-2019-Q2.pdf host=www.whirlpool.com
app-4    | Trying direct URL for model FGMV175QFA...
app-4    | Manuals section not found, waiting additional time...
app-4    | Current URL after page load: https://www.frigidaire.com/en/p/owner-center/product-support/FGRF1097
app-4    | Looking for 'owner-center': True
app-4    | Looking for model 'FGRF1097': True
app-4    | Direct URL worked (found model in URL), looking for manual links...
app-4    | Looking for manual links on Frigidaire page...
app-4    | Current URL: https://www.frigidaire.com/en/p/owner-center/product-support/FGRF1097
app-4    | Current URL after navigation: https://www.frigidaire.com/en/p/owner-center/product-support/FGMV175QFA
app-4    | Manuals section not found, waiting additional time...
app-4    | Found 180 links on the page:
app-4    |   1.  -> https://www.frigidaire.com/en/
app-4    |   2.  -> https://www.electrolux.com/en/
app-4    |   3. Contact us -> /en/contactUs
app-4    |   4. Contact us -> /en/contact-us
app-4    |   5.  -> /en/cart
app-4    |   6.  -> /
app-4    |   7. Refrigerators -> /en/kitchen-appliances/refrigerators
app-4    |   8. Explore Refrigerators -> /en/kitchen-appliances/refrigerators
app-4    |   9. French Door -> /en/kitchen-appliances/refrigerators/french-door
app-4    |   10. Side-by-Side -> /en/kitchen-appliances/refrigerators/side-by-side
app-4    |   11. Single Door -> /en/kitchen-appliances/single-door-refrigerator-freezer
app-4    |   12. Top Freezer -> /en/kitchen-appliances/refrigerators/top-freezer
app-4    |   13. Bottom Freezer -> /en/kitchen-appliances/refrigerators/bottom-freezer
app-4    |   14. Compact -> /en/kitchen-appliances/refrigerators/compact
app-4    |   15. Wine & Beverage -> /en/kitchen-appliances/refrigerators/wine-beverage
app-4    |   16. Freezers -> /en/kitchen-appliances/freezers
app-4    |   17. Explore Freezers -> /en/kitchen-appliances/freezers
app-4    |   18. Upright -> /en/kitchen-appliances/freezers/upright
app-4    |   19. Chest -> /en/kitchen-appliances/freezers/chest
app-4    |   20. Single Door -> /en/kitchen-appliances/single-door-refrigerator-freezer
app-4    | Selector '.mannual-name' found 0 elements
app-4    | Selector '.manuals a' found 0 elements
app-4    | Selector 'a[href*=".pdf"]' found 0 elements
app-4    | Selector 'a[href*="guide"]' found 0 elements
app-4    | Selector 'a[href*="manual"]' found 0 elements
app-4    | Selector 'a[href*="electroluxmedia.com"]' found 0 elements
app-4    | No manual links found on the page
app-4    | No manual links found on direct page
app-4    | Attempting DuckDuckGo fallback...
app-4    | Attempting DuckDuckGo fallback for FGRF1097 on frigidaire.com...
app-4    | Running DuckDuckGo search for query: "FGRF1097" site:frigidaire.com
app-4    | DuckDuckGo search loaded for query: "FGRF1097" site:frigidaire.com
app-4    | No trusted link found for frigidaire.com using query '"FGRF1097" site:frigidaire.com'
app-4    | DuckDuckGo fallback failed for FGRF1097 after trying 1 queries.
app-4    | INFO:     172.18.0.3:60256 - "GET /scrape/frigidaire/FGRF1097 HTTP/1.1" 404 Not Found
app-3    | 2025-11-12 22:47:31 - serpapi.client - INFO - SerpApi request succeeded query=DVE45T3400W/A3 manual filetype:pdf search_id=69150e7dbd1731d97a129de7 organic_results=5
app-3    | 2025-11-12 22:47:31 - serpapi.orchestrator - INFO - Collecting candidates for query=DVE45T3400W/A3 manual filetype:pdf (search_id=69150e7dbd1731d97a129de7)
app-3    | 2025-11-12 22:47:31 - serpapi.orchestrator - INFO - Collected 0 candidate(s) for query=DVE45T3400W/A3 manual filetype:pdf (search_id=69150e7dbd1731d97a129de7)
app-3    | 2025-11-12 22:47:31 - serpapi.orchestrator - INFO - No PDF candidates returned for query=DVE45T3400W/A3 manual filetype:pdf
app-3    | 2025-11-12 22:47:31 - serpapi.orchestrator - INFO - No valid SerpApi manual found for brand=samsung model=DVE45T3400W/A3
app-3    | Using proxy server http://squid:8888
app-3    | 2025-11-12 22:47:31 - uc - WARNING - could not detect version_main.therefore, we are assuming it is chrome 108 or higher
squid-1  | 2025/11/12 22:47:33| ERROR: Connection to upstream2 failed
squid-1  |     current master transaction: master2455
squid-1  | 2025/11/12 22:47:33| ERROR: Connection to upstream1 failed
squid-1  |     current master transaction: master2455
squid-1  | 2025/11/12 22:47:33| ERROR: Connection to upstream1 failed
squid-1  |     current master transaction: master2518
squid-1  | 2025/11/12 22:47:33| ERROR: Connection to upstream2 failed
squid-1  |     current master transaction: master2518
app-4    | Manuals section not found, waiting additional time...
app-4    | Current URL after page load: https://www.frigidaire.com/en/p/owner-center/product-support/FGMV175QFA
app-4    | Looking for 'owner-center': True
app-4    | Looking for model 'FGMV175QFA': True
app-4    | Direct URL worked (found model in URL), looking for manual links...
app-4    | Looking for manual links on Frigidaire page...
app-4    | Current URL: https://www.frigidaire.com/en/p/owner-center/product-support/FGMV175QFA
app-4    | INFO:     172.18.0.3:41548 - "GET /health HTTP/1.1" 200 OK
app-4    | Manuals section not found, waiting additional time...
app-4    | Found 180 links on the page:
app-4    |   1.  -> https://www.frigidaire.com/en/
app-4    |   2.  -> https://www.electrolux.com/en/
app-4    |   3. Contact us -> /en/contactUs
app-4    |   4. Contact us -> /en/contact-us
app-4    |   5.  -> /en/cart
app-4    |   6.  -> /
app-4    |   7. Refrigerators -> /en/kitchen-appliances/refrigerators
app-4    |   8. Explore Refrigerators -> /en/kitchen-appliances/refrigerators
app-4    |   9. French Door -> /en/kitchen-appliances/refrigerators/french-door
app-4    |   10. Side-by-Side -> /en/kitchen-appliances/refrigerators/side-by-side
app-4    |   11. Single Door -> /en/kitchen-appliances/single-door-refrigerator-freezer
app-4    |   12. Top Freezer -> /en/kitchen-appliances/refrigerators/top-freezer
app-4    |   13. Bottom Freezer -> /en/kitchen-appliances/refrigerators/bottom-freezer
app-4    |   14. Compact -> /en/kitchen-appliances/refrigerators/compact
app-4    |   15. Wine & Beverage -> /en/kitchen-appliances/refrigerators/wine-beverage
app-4    |   16. Freezers -> /en/kitchen-appliances/freezers
app-4    |   17. Explore Freezers -> /en/kitchen-appliances/freezers
app-4    |   18. Upright -> /en/kitchen-appliances/freezers/upright
app-4    |   19. Chest -> /en/kitchen-appliances/freezers/chest
app-4    |   20. Single Door -> /en/kitchen-appliances/single-door-refrigerator-freezer
app-4    | Selector '.mannual-name' found 0 elements
app-4    | Selector '.manuals a' found 0 elements
app-4    | Selector 'a[href*=".pdf"]' found 0 elements
app-4    | Selector 'a[href*="guide"]' found 0 elements
app-4    | Selector 'a[href*="manual"]' found 0 elements
app-4    | Selector 'a[href*="electroluxmedia.com"]' found 0 elements
app-4    | No manual links found on the page
app-4    | No manual links found on direct page
app-4    | Attempting DuckDuckGo fallback...
app-4    | Attempting DuckDuckGo fallback for FGMV175QFA on frigidaire.com...
app-4    | Running DuckDuckGo search for query: "FGMV175QFA" site:frigidaire.com
app-4    | DuckDuckGo search loaded for query: "FGMV175QFA" site:frigidaire.com
app-4    | No trusted link found for frigidaire.com using query '"FGMV175QFA" site:frigidaire.com'
app-4    | DuckDuckGo fallback failed for FGMV175QFA after trying 1 queries.
app-4    | INFO:     172.18.0.3:60270 - "GET /scrape/frigidaire/FGMV175QFA HTTP/1.1" 404 Not Found
app-3    | Fetching page for model DVE45T3400W/A3...
app-3    | Current URL: https://www.samsung.com/latin_en/support/user-manuals-and-guide/
app-3    | Retry URL: https://www.lg.com/us/support/product/lg-WM4270HWA
app-3    | Retry page title: LG WM4270HWA: Support, Manuals, Warranty & More | LG USA Product Support Page
app-3    | Guide error after retry: False
app-3    | Performing recorded actions for lg- page...
app-3    | Clicked manuals tab.
app-3    | Found 19 manual items:
app-3    | Clicking manual item...
app-3    | Clicked manual item.
app-3    | Current URL after click: https://www.lg.com/us/support/product/lg-WM4270HWA
app-3    | Number of windows: 1
app-3    | Files in download_dir before wait: ['MFL68639701-Eng.pdf.crdownload']
app-3    | Starting wait_for_download with timeout=30 in /app/headless-browser-scraper/temp/tmp5bzr21j9
app-3    | Primary scraping for Samsung DVE45T3400W/A3 failed: Model link not found with any attempted model code
app-3    | Using proxy server http://squid:8888
app-3    | 2025-11-12 22:47:45 - uc - WARNING - could not detect version_main.therefore, we are assuming it is chrome 108 or higher
app-1    | Error finding manual on direct page: Message:
app-1    | Stacktrace:
app-1    | #0 0x62df896fdaea <unknown>
app-1    | #1 0x62df89149cdb <unknown>
app-1    | #2 0x62df8919c6c4 <unknown>
app-1    | #3 0x62df8919c901 <unknown>
app-1    | #4 0x62df891eb8b4 <unknown>
app-1    | #5 0x62df891e8c87 <unknown>
app-1    | #6 0x62df8918eaca <unknown>
app-1    | #7 0x62df8918f7d1 <unknown>
app-1    | #8 0x62df896c4ab9 <unknown>
app-1    | #9 0x62df896c7a8c <unknown>
app-1    | #10 0x62df896add49 <unknown>
app-1    | #11 0x62df896c8685 <unknown>
app-1    | #12 0x62df896956c3 <unknown>
app-1    | #13 0x62df896ea7d8 <unknown>
app-1    | #14 0x62df896ea9b3 <unknown>
app-1    | #15 0x62df896fca83 <unknown>
app-1    | #16 0x7e450be12aa4 <unknown>
app-1    | #17 0x7e450be9fa64 __clone
app-1    |
app-1    | Direct URL fallback did not succeed for LE7680XSH2; trying Whirlpool.com via DuckDuckGo...
app-1    | Attempting DuckDuckGo fallback for LE7680XSH2 on whirlpool.com...
app-1    | Running DuckDuckGo search for query: "LE7680XSH2" site:whirlpool.com
app-1    | DuckDuckGo search loaded for query: "LE7680XSH2" site:whirlpool.com
app-1    | DuckDuckGo search attempt failed for query '"LE7680XSH2" site:whirlpool.com': Message:
app-1    | Stacktrace:
app-1    | #0 0x62df896fdaea <unknown>
app-1    | #1 0x62df89149cdb <unknown>
app-1    | #2 0x62df8919c6c4 <unknown>
app-1    | #3 0x62df8919c901 <unknown>
app-1    | #4 0x62df891eb8b4 <unknown>
app-1    | #5 0x62df891e8c87 <unknown>
app-1    | #6 0x62df8918eaca <unknown>
app-1    | #7 0x62df8918f7d1 <unknown>
app-1    | #8 0x62df896c4ab9 <unknown>
app-1    | #9 0x62df896c7a8c <unknown>
app-1    | #10 0x62df896add49 <unknown>
app-1    | #11 0x62df896c8685 <unknown>
app-1    | #12 0x62df896956c3 <unknown>
app-1    | #13 0x62df896ea7d8 <unknown>
app-1    | #14 0x62df896ea9b3 <unknown>
app-1    | #15 0x62df896fca83 <unknown>
app-1    | #16 0x7e450be12aa4 <unknown>
app-1    | #17 0x7e450be9fa64 __clone
app-1    |
app-1    | Running DuckDuckGo search for query: "LE7680XSH" site:whirlpool.com
app-1    | DuckDuckGo search loaded for query: "LE7680XSH" site:whirlpool.com
app-1    | DuckDuckGo search attempt failed for query '"LE7680XSH" site:whirlpool.com': Message:
app-1    | Stacktrace:
app-1    | #0 0x62df896fdaea <unknown>
app-1    | #1 0x62df89149cdb <unknown>
app-1    | #2 0x62df8919c6c4 <unknown>
app-1    | #3 0x62df8919c901 <unknown>
app-1    | #4 0x62df891eb8b4 <unknown>
app-1    | #5 0x62df891e8c87 <unknown>
app-1    | #6 0x62df8918eaca <unknown>
app-1    | #7 0x62df8918f7d1 <unknown>
app-1    | #8 0x62df896c4ab9 <unknown>
app-1    | #9 0x62df896c7a8c <unknown>
app-1    | #10 0x62df896add49 <unknown>
app-1    | #11 0x62df896c8685 <unknown>
app-1    | #12 0x62df896956c3 <unknown>
app-1    | #13 0x62df896ea7d8 <unknown>
app-1    | #14 0x62df896ea9b3 <unknown>
app-1    | #15 0x62df896fca83 <unknown>
app-1    | #16 0x7e450be12aa4 <unknown>
app-1    | #17 0x7e450be9fa64 __clone
app-1    |
app-1    | Running DuckDuckGo search for query: "LE7680XS" site:whirlpool.com
app-1    | DuckDuckGo search loaded for query: "LE7680XS" site:whirlpool.com
app-1    | DuckDuckGo search attempt failed for query '"LE7680XS" site:whirlpool.com': Message:
app-1    | Stacktrace:
app-1    | #0 0x62df896fdaea <unknown>
app-1    | #1 0x62df89149cdb <unknown>
app-1    | #2 0x62df8919c6c4 <unknown>
app-1    | #3 0x62df8919c901 <unknown>
app-1    | #4 0x62df891eb8b4 <unknown>
app-1    | #5 0x62df891e8c87 <unknown>
app-1    | #6 0x62df8918eaca <unknown>
app-1    | #7 0x62df8918f7d1 <unknown>
app-1    | #8 0x62df896c4ab9 <unknown>
app-1    | #9 0x62df896c7a8c <unknown>
app-1    | #10 0x62df896add49 <unknown>
app-1    | #11 0x62df896c8685 <unknown>
app-1    | #12 0x62df896956c3 <unknown>
app-1    | #13 0x62df896ea7d8 <unknown>
app-1    | #14 0x62df896ea9b3 <unknown>
app-1    | #15 0x62df896fca83 <unknown>
app-1    | #16 0x7e450be12aa4 <unknown>
app-1    | #17 0x7e450be9fa64 __clone
app-1    |
app-1    | Running DuckDuckGo search for query: "LE7680X" site:whirlpool.com
app-1    | DuckDuckGo search loaded for query: "LE7680X" site:whirlpool.com
app-1    | DuckDuckGo search attempt failed for query '"LE7680X" site:whirlpool.com': Message:
app-1    | Stacktrace:
app-1    | #0 0x62df896fdaea <unknown>
app-1    | #1 0x62df89149cdb <unknown>
app-1    | #2 0x62df8919c6c4 <unknown>
app-1    | #3 0x62df8919c901 <unknown>
app-1    | #4 0x62df891eb8b4 <unknown>
app-1    | #5 0x62df891e8c87 <unknown>
app-1    | #6 0x62df8918eaca <unknown>
app-1    | #7 0x62df8918f7d1 <unknown>
app-1    | #8 0x62df896c4ab9 <unknown>
app-1    | #9 0x62df896c7a8c <unknown>
app-1    | #10 0x62df896add49 <unknown>
app-1    | #11 0x62df896c8685 <unknown>
app-1    | #12 0x62df896956c3 <unknown>
app-1    | #13 0x62df896ea7d8 <unknown>
app-1    | #14 0x62df896ea9b3 <unknown>
app-1    | #15 0x62df896fca83 <unknown>
app-1    | #16 0x7e450be12aa4 <unknown>
app-1    | #17 0x7e450be9fa64 __clone
app-1    |
app-1    | DuckDuckGo fallback failed for LE7680XSH2 after trying 4 queries.
app-1    | Whirlpool DuckDuckGo fallback failed for LE7680XSH2.
app-1    | INFO:     172.18.0.3:33316 - "GET /scrape/whirlpool/LE7680XSH2 HTTP/1.1" 404 Not Found
app-3    | Primary scraping failed for DVE45T3400W/A3, trying fallback...
app-3    | Files in download_dir after wait: ['MFL68639701-Eng.pdf', 'downloads.html']
app-3    | Downloaded PDF: /app/headless-browser-scraper/temp/tmp5bzr21j9/MFL68639701-Eng.pdf
app-3    | Found PDF: Owner's Manual
app-3    | URL: /app/headless-browser-scraper/temp/tmp5bzr21j9/MFL68639701-Eng.pdf
app-3    | Validated as PDF.
app-3    | 2025-11-12 22:47:47 - ingest - INFO - Ingesting PDF from local path: /app/headless-browser-scraper/temp/tmp5bzr21j9/MFL68639701-Eng.pdf
app-3    | Cleaned up temp dir: /app/headless-browser-scraper/temp/tmp5bzr21j9
app-3    | INFO:     172.18.0.3:40864 - "GET /scrape/lg/WM4270HWA HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43194 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43210 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:43214 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:40928 - "GET /health HTTP/1.1" 200 OK
app-3    | Navigated to fallback URL: https://samsungparts.com/products/DVE45T3400W-a3
app-3    | An error occurred during fallback scraping for model DVE45T3400W/A3: Message:
app-3    | Stacktrace:
app-3    | #0 0x602152ef2aea <unknown>
app-3    | #1 0x60215293ecdb <unknown>
app-3    | #2 0x6021529916c4 <unknown>
app-3    | #3 0x602152991901 <unknown>
app-3    | #4 0x6021529e08b4 <unknown>
app-3    | #5 0x6021529ddc87 <unknown>
app-3    | #6 0x602152983aca <unknown>
app-3    | #7 0x6021529847d1 <unknown>
app-3    | #8 0x602152eb9ab9 <unknown>
app-3    | #9 0x602152ebca8c <unknown>
app-3    | #10 0x602152ea2d49 <unknown>
app-3    | #11 0x602152ebd685 <unknown>
app-3    | #12 0x602152e8a6c3 <unknown>
app-3    | #13 0x602152edf7d8 <unknown>
app-3    | #14 0x602152edf9b3 <unknown>
app-3    | #15 0x602152ef1a83 <unknown>
app-3    | #16 0x7e9532251aa4 <unknown>
app-3    | #17 0x7e95322dea64 __clone
app-3    |
app-3    | INFO:     172.18.0.3:55794 - "GET /scrape/samsung/DVE45T3400W/A3 HTTP/1.1" 404 Not Found
app-3    | 2025-11-12 22:48:06 - serpapi.headless_pdf_fetcher - INFO - Fetch-based download succeeded url=https://www.whirlpool.com/content/dam/business-unit/whirlpool/en-us/marketing-content/site-assets/global-assets/documents/whirlpool-brand-catalog-2019-Q2.pdf path=/app/headless-browser-scraper/temp/tmpeiq6wufh/whirlpool-brand-catalog-2019-Q2.pdf
app-3    | 2025-11-12 22:48:06 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpeiq6wufh/whirlpool-brand-catalog-2019-Q2.pdf doc_type=owner accept=False manual_signal=0 manual_tokens=2 marketing_hits=1 page_count=111 contains_model=False
app-3    | 2025-11-12 22:48:06 - serpapi.orchestrator - INFO - Rejecting PDF path=/app/headless-browser-scraper/temp/tmpeiq6wufh/whirlpool-brand-catalog-2019-Q2.pdf reason=marketing_signals
app-3    | 2025-11-12 22:48:06 - serpapi.orchestrator - INFO - Candidate rejected after validation url=https://www.whirlpool.com/content/dam/business-unit/whirlpool/en-us/marketing-content/site-assets/global-assets/documents/whirlpool-brand-catalog-2019-Q2.pdf brand=whirlpool model=WEG750H0H
app-3    | 2025-11-12 22:48:06 - serpapi.orchestrator - INFO - Attempting candidate url=https://www.whirlpool.com/content/dam/global/documents/202102/owners-manual-w11498994-reva.pdf score=71 source=organic_results
app-1    | INFO:     172.18.0.3:46378 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:38910 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:38912 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:59040 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:59052 - "GET /health HTTP/1.1" 200 OK
app-3    | 2025-11-12 22:48:21 - serpapi.orchestrator - INFO - Downloading candidate url=https://www.whirlpool.com/content/dam/global/documents/202102/owners-manual-w11498994-reva.pdf brand=whirlpool model=WEG750H0H referer=https://www.whirlpool.com/ read_timeout=15
app-3    | 2025-11-12 22:48:36 - serpapi.orchestrator - WARNING - Download timed out while reading url=https://www.whirlpool.com/content/dam/global/documents/202102/owners-manual-w11498994-reva.pdf host=www.whirlpool.com read_timeout=15 error=HTTPSConnectionPool(host='www.whirlpool.com', port=443): Read timed out. (read timeout=15)
app-3    | 2025-11-12 22:48:36 - serpapi.orchestrator - INFO - Attempting headless fallback download for url=https://www.whirlpool.com/content/dam/global/documents/202102/owners-manual-w11498994-reva.pdf
app-3    | Using proxy server http://squid:8888
app-3    | 2025-11-12 22:48:36 - uc - WARNING - could not detect version_main.therefore, we are assuming it is chrome 108 or higher
app-1    | INFO:     172.18.0.3:49236 - "GET /health HTTP/1.1" 200 OK
app-3    | 2025-11-12 22:48:43 - serpapi.headless_pdf_fetcher - INFO - Headless PDF navigation url=https://www.whirlpool.com/content/dam/global/documents/202102/owners-manual-w11498994-reva.pdf host=www.whirlpool.com
app-2    | INFO:     127.0.0.1:55382 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:55386 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:42722 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:42732 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:40408 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:58480 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:58486 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:34296 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:34310 - "GET /health HTTP/1.1" 200 OK
app-3    | 2025-11-12 22:49:21 - serpapi.headless_pdf_fetcher - INFO - Fetch-based download succeeded url=https://www.whirlpool.com/content/dam/global/documents/202102/owners-manual-w11498994-reva.pdf path=/app/headless-browser-scraper/temp/tmpp6l8h99v/owners-manual-w11498994-reva.pdf
app-3    | 2025-11-12 22:49:21 - serpapi.orchestrator - INFO - PDF analysis path=/app/headless-browser-scraper/temp/tmpp6l8h99v/owners-manual-w11498994-reva.pdf doc_type=owner accept=True manual_signal=1 manual_tokens=3 marketing_hits=0 page_count=83 contains_model=False
app-3    | 2025-11-12 22:49:21 - serpapi.orchestrator - INFO - Validation passed for candidate url=https://www.whirlpool.com/content/dam/global/documents/202102/owners-manual-w11498994-reva.pdf doc_type=owner score=71
app-3    | 2025-11-12 22:49:21 - serpapi.orchestrator - INFO - Candidate accepted url=https://www.whirlpool.com/content/dam/global/documents/202102/owners-manual-w11498994-reva.pdf brand=whirlpool model=WEG750H0H
app-3    | 2025-11-12 22:49:21 - ingest - INFO - Ingesting PDF from local path: /app/headless-browser-scraper/temp/tmpp6l8h99v/owners-manual-w11498994-reva.pdf
app-3    | Cleaned up temp dir: /app/headless-browser-scraper/temp/tmpp6l8h99v
app-3    | INFO:     172.18.0.3:32988 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43086 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43102 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:53646 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:53648 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:34690 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:46098 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:46102 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:38970 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:38974 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:38512 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:58338 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:58348 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:46720 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:46732 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:34020 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:38812 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:38820 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:38836 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:38840 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:56374 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:48032 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:48042 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:48054 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:48068 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:51028 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:51836 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:51842 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:51848 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:51856 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:44714 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:34416 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:34420 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:34424 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:34438 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:47942 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:38204 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:38212 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:38216 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:38218 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:50872 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:54302 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:54316 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:54328 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:54338 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:47062 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:47458 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:47468 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:47480 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:47494 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:44516 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:34650 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:34656 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:34670 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:34684 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:48326 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:40488 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:40498 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:40502 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:40518 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:43226 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43038 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43044 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:43056 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:43066 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:47246 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:54446 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:54462 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:54474 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:54490 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:40742 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:58620 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:58632 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:58638 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:58654 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:54280 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:58380 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:58392 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:58394 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:58398 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:40116 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:42844 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:42860 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:42870 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:42886 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:60130 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:48336 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:48340 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:48348 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:48362 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:34408 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:36522 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:36532 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:36544 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:36558 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:58896 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:59430 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:59444 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:59452 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:59464 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:42682 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:36030 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:36034 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:36038 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:36052 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:55298 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:51338 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:51344 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:51360 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:51364 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:53800 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:46476 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:46478 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:46488 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:46502 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:56736 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:46194 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:46200 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:46202 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:46214 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:50524 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43418 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43422 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:43430 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:43442 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:56674 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43050 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43052 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:43064 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:43072 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:33040 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:48584 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:48592 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:48608 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:48620 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:51256 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:52830 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:52842 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:52852 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:52862 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:46570 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:45190 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:45204 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:45212 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:45222 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:56780 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:48862 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:48864 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:48868 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:48882 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:36460 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:38206 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:38212 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:38222 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:38236 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:60690 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:36342 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:36326 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:36354 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:36362 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:53998 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:52528 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:52540 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:52552 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:52556 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:53216 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:57078 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:57088 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:57100 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:57104 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     172.18.0.3:52662 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:42910 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:42926 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:42934 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:42948 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:40262 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:58164 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:58172 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:58182 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:58186 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:56876 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:47424 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:47432 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:47442 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:47448 - "GET /health HTTP/1.1" 200 OK
pdf


app-2    | INFO:     172.18.0.3:56946 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:49180 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:49182 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:49184 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:49198 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:34350 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:44158 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:44166 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:44168 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:44184 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     172.18.0.3:40088 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:56870 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:56878 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:56890 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:56904 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:38936 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:44150 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:44160 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:44168 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:44178 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:49156 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:33656 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:33662 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:33668 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:33670 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:49106 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:58250 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:58260 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:58268 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:58284 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:33694 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:34092 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:34094 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:34110 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:34122 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     172.18.0.3:39606 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:49830 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:49834 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:49836 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:49852 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:47456 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:43804 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:43812 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:43816 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:43818 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:43434 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:60390 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:60392 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:60404 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:60408 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     172.18.0.3:40850 - "GET /health HTTP/1.1" 200 OK
app-1    | INFO:     127.0.0.1:51024 - "GET /health HTTP/1.1" 200 OK
app-2    | INFO:     127.0.0.1:51036 - "GET /health HTTP/1.1" 200 OK
app-3    | INFO:     127.0.0.1:51048 - "GET /health HTTP/1.1" 200 OK
app-4    | INFO:     127.0.0.1:51060 - "GET /health HTTP/1.1" 200 OK
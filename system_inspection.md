# System Inspection & Efficiency Report: Cosmos Lab

This report provides a detailed overview of your Portainer environments, resource utilization, and configuration efficiency on your **Beelink Mini PC** running **Proxmox VE** (`cosmoslab.dev`).

---

## 🖥️ Hardware Profile (Beelink Mini PC)
* **CPU:** Intel(R) N150 (Alder Lake-N, 4 Cores / 4 Threads, base frequency up to 3.60 GHz, 6W TDP).
* **Virtualization:** Proxmox VE 7.x Kernel (`7.0.6-2-pve`) running LXC containers.
* **Estimated Physical Memory:** 16 GB DDR4/DDR5 (based on combined LXC allocations of 8GB + 4GB + other services).

---

## 📦 Portainer Environments Summary

Portainer manages three distinct environments across your lab setup:

| ID | Name | Type | Host IP / URL | Running Containers | Status |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **3** | `edge` | Standalone Docker | `unix:///var/run/docker.sock` (LXC 102) | 7 | Up |
| **5** | `pihole` | Portainer Agent | `tcp://192.168.4.134:9001` | 3 | Up |
| **8** | `bodhi` | Portainer Agent | `tcp://192.168.4.113:9001` (LXC 104) | 48 | Up |

---

## 🔍 Detailed Environment Inspection

### 1. `edge` Environment (LXC 102)
* **IP Address:** `192.168.4.120` (resolves as `cosmoslab.dev`)
* **Allocated RAM:** 4.0 GiB (288 MiB used, 3.4 GiB free)
* **Containers (7 total, all running):**
  * `cloudflare-ddns` (DDNS updates)
  * `watchtower` (Docker updates)
  * `portainer` (Portainer CE web UI)
  * `caddy` (Reverse proxy gateway)
  * `duckdns` (DuckDNS DDNS)
  * `crowdsec` (Security & IPS)
  * `wg-easy` (Wireguard VPN UI)

### 2. `pihole` Environment
* **IP Address:** `192.168.4.134`
* **Containers (3 total, all running):**
  * `pihole` (Network DNS & Ad-blocker)
  * `watchtower` (Docker updates)
  * `portainer_agent` (Portainer management agent)

### 3. `bodhi` Environment (LXC 104)
* **IP Address:** `192.168.4.113`
* **Allocated RAM:** 8.0 GiB (4.3 GiB used, 1.1 GiB free, 3.7 GiB available)
* **Swap Usage:** 12.0 GiB total (4.5 GiB used)
* **Containers (48 total, all running):**
  This environment is the main workhorse of your lab, hosting a large suite of services:
  * **Databases:** 2x PostgreSQL 16 (for `n8n` and `twenty-crm`), 4x MariaDB (for `invoiceninja`, `freescout`, `cypht`, and `romm`), 2x Redis (for `paperless` and `twenty-crm`), and 1x InfluxDB 2.7.
  * **Core Services:** Mealie (planner + app), n8n workflow engine, Twenty CRM (server, worker, redis, db), Home Assistant, CyPht webmail, RomM (ROM manager), Paperless-ngx (webserver + redis), Gotify, Plex Media Server, Node-RED, Open WebUI, and Actual Budget.
  * **Games:** Minecraft Bedrock server (`cos_mc_1`).
  * **Custom/Web Apps:** Speedhive Tools UI, Curbclass web, Chassis Shield web, Bidagent, Breakout web, WHRRI website, Event DRSCCA app, Event Demo app.

---

## ⚡ Resource Utilization & Efficiency Analysis

> [!WARNING]
> ### 1. LXC Memory Allocation Mismatch (High Priority)
> * **The Issue:** The `edge` container has **4.0 GiB** of RAM allocated but is only using **288 MiB** (~7.2%). Meanwhile, the `bodhi` container has **8.0 GiB** of RAM allocated, is fully utilizing it, and has swapped out **4.5 GiB** of memory to disk.
> * **The Impact:** Swapping on an Intel N150 (which relies on shared resources and typically consumer-grade SSDs) slows down database lookups and application responsiveness on `bodhi`, while 3.7 GiB of physical memory sits entirely idle in the `edge` container.

> [!NOTE]
> ### 2. CPU Efficiency & Consolidation
> * **The Reality:** Running 48 containers inside a single LXC container (`bodhi`) is extremely high consolidation. The Intel N150 has only 4 E-cores (no hyper-threading). 
> * **The Positive:** Despite the huge container count, the load average sits comfortably around `0.70 - 0.90` (roughly 20% total CPU usage). This means the CPU handles the idle state of these containers very well.
> * **The Negative:** Because these containers are running multiple duplicate database engines (Postgres, MariaDB, Redis), memory overhead is high.

---

## 🛠️ Recommended Actions (Inspect-Only)

Since you requested **no changes**, here are the optimizations you can perform in Proxmox when ready:

1. **Rebalance LXC Memory Allocations:**
   * In Proxmox VE, reduce the memory limit for LXC `102` (`edge`) from **4 GiB to 1.5 GiB**.
   * Increase the memory limit for LXC `104` (`bodhi`) from **8 GiB to 10.5 GiB** or **11 GiB**.
   * *This will instantly mitigate the swap thrashing on `bodhi` by utilizing the unused RAM from `edge` without increasing the host's overall memory footprint.*
2. **Review LXC Swappiness:**
   * The container is swapping very early. Consider setting `sysctl vm.swappiness=10` inside the `bodhi` container or setting it at the Proxmox host level if you want to keep pages in physical RAM longer.
3. **Database Consolidation:**
   * You are running 4 separate MariaDB instances and 2 PostgreSQL instances. If resource limits become an issue, you could consolidate these databases into single shared database containers (e.g., one Postgres container hosting multiple databases, one MariaDB container hosting multiple databases). This would save roughly 500MB–1GB of RAM overhead.

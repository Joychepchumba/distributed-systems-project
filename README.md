# Distributed Systems Project: Consistent Hashing Load Balancer

A production-grade Consistent Hashing Load Balancer system designed to route client requests dynamically across a cluster of backend server replica containers. The load balancer implements a self-healing heartbeat daemon, dynamic replication management, and offline simulation suites to model system scalability.

---

## 1. System Architecture

The load balancer manages a cluster of Dockerized Flask backend servers using a **Consistent Hash Ring** mechanism.

### Key Components

- **Consistent Hash Ring (`ConsistentHashMap`)**: Tracks server virtual nodes on a ring of slot size $M = 512$ with $K = 9$ virtual nodes per server. Maps incoming requests using quadratic probing to handle ring collisions gracefully.
- **Load Balancer Service (`lb.py`)**: A multi-threaded Flask server that serves as the entry-point proxy. It intercepts client requests, hashes their identifiers, queries the ring, and proxies requests to the target replica.
- **Heartbeat Self-Healing Daemon**: Runs a background monitoring loop that periodically checks backend server health, automatically terminating and recreating failing server instances.
- **Backend Servers (`server.py`)**: Individual Flask containers responding to `/home` requests and serving `/heartbeat` health signals.

---

## 2. API Endpoints

The load balancer exposes the following HTTP REST endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/rep` | `GET` | Retrieve list of active replicas and total server count. |
| `/add` | `POST` | Dynamically scale up the active server count by $n$ instances. |
| `/rm` | `DELETE` | Dynamically scale down the active server count by $n$ instances. |
| `/<path>` | `GET` | Proxy incoming request to a consistent-hash selected replica. |

---

## 3. Getting Started

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- `pip` packages specified in `requirements.txt`

### Running the Services
1. Build the server image:
   ```bash
   docker build -t server_img ./server
   ```
2. Build and start the load balancer service (which accesses the host Docker daemon socket to spawn backend replicas dynamically):
   ```bash
   docker compose up --build
   ```

---

## 4. Performance & Benchmarking Suite

The project includes a benchmarking script to evaluate request distributions, scalability metrics, and failure recovery.

### Execution
Run the benchmarking suite via:
```bash
python analysis/analyze.py [a1|a2|a3|a4|all]
```

- **`a1`**: Measures request distribution across 3 replicas using 10,000 asynchronous client requests.
- **`a2`**: Evaluates scalability, recording average server load as $N$ ranges from 2 to 6.
- **`a3`**: Kills a container instance and measures time taken for self-healing daemon to deploy a replacement replica.
- **`a4`**: Runs offline mathematical simulation comparing the default quadratic hash ring setup against a modified function option.

---

## 5. Contributors and Academic Integrity
Created as part of the Distributed Systems course project. All contributions are logged via git commits detailing incremental refactoring, code quality, typing enhancements, and modular configuration improvements.
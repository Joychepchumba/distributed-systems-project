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
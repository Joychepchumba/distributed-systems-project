"""Load balancer service for the distributed systems project.

Spawns/kills backend server containers via the Docker CLI (using the
host's Docker socket mounted into this container), registers them on a
consistent-hash ring, forwards client requests to the ring-selected
replica, and runs a background heartbeat thread that detects and
replaces dead replicas automatically.
"""
import os
import random
import string
import subprocess
import threading
import time
from typing import Dict, List, Optional

from flask import Flask, jsonify, request
import requests as req

from consistent_hash import ConsistentHashMap


app = Flask(__name__)

N             = int(os.environ.get("N", 3))
SERVER_IMAGE  = "server_img"
NETWORK       = os.environ.get("NETWORK", "net1")

chmap          = ConsistentHashMap()
servers        = {}        # hostname: numeric server_id
server_id_counter = 1
lock           = threading.Lock()

# helpers 

def random_hostname() -> str:
    """Generate a random container/hostname string.

    Returns:
        str: A string of the format 'Server_XXXX' where XXXX are 4 random uppercase alphanumeric characters.
    """
    return "Server_" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))


def spawn_container(hostname: str, server_id: int) -> bool:
    """Start a new server container instance on the shared Docker network.

    Args:
        hostname (str): Unique hostname and container name to spawn.
        server_id (int): Numeric identifier passed as environment variable SERVER_ID.

    Returns:
        bool: True if the Docker command successfully launched the container, False otherwise.
    """
    result = subprocess.run(
        ['docker', 'run', '--name', hostname,
         '--network', NETWORK, '--network-alias', hostname,
         '-e', f'SERVER_ID={server_id}', '-d', f'{SERVER_IMAGE}:latest'],
        capture_output=True, text=True
    )
    return result.returncode == 0


def kill_container(hostname: str) -> None:
    """Stop and remove a server container instance via the Docker CLI.

    Args:
        hostname (str): Unique name of the container/server instance to terminate.
    """
    subprocess.run(['docker', 'stop', hostname], capture_output=True)
    subprocess.run(['docker', 'rm',   hostname], capture_output=True)


def add_server_internal(hostname: str, server_id: int) -> bool:
    """Spawn container + register in ring. Caller must hold lock.

    Args:
        hostname (str): Unique name/hostname of the container.
        server_id (int): Numeric identifier assigned to this container.

    Returns:
        bool: True if server successfully spawned and added to consistent hash ring, False otherwise.
    """
    if spawn_container(hostname, server_id):
        servers[hostname] = server_id
        chmap.add_server(server_id)
        return True
    return False

def remove_server_internal(hostname: str) -> None:
    """Remove from ring + kill container. Caller must hold lock.

    Args:
        hostname (str): Unique name/hostname of the container to tear down.
    """
    server_id = servers.pop(hostname, None)
    if server_id is not None:
        chmap.remove_server(server_id)
        kill_container(hostname)


# startup 

def init_servers() -> None:
    """Spawn the initial N server containers at startup and register
    them on the consistent hash ring.

    This function runs exactly once at startup.
    """
    global server_id_counter
    with lock:
        for i in range(1, N + 1):
            hostname = f"Server_{i}"
            add_server_internal(hostname, server_id_counter)
            server_id_counter += 1


# heartbeat monitor 

def heartbeat_loop() -> None:
    """Background thread loop: every 5 seconds, check health of all registered servers.

    Pings the /heartbeat endpoint of each server container. If a server is
    unreachable or fails to return HTTP 200, it is removed from the consistent
    hash ring and its container is replaced with a new, healthy server.
    """
    global server_id_counter
    while True:
        time.sleep(5)

        # Snapshot hostnames without holding the lock during slow network I/O
        with lock:
            snapshot = list(servers.keys())

        dead = []
        for hostname in snapshot:
            try:
                r = req.get(f"http://{hostname}:5000/heartbeat", timeout=2)
                if r.status_code != 200:
                    dead.append(hostname)
            except Exception:
                dead.append(hostname)

        for hostname in dead:
            print(f"[LB] {hostname} is dead, respawning...")

            # Remove from ring state under lock (fast), grab new ID atomically
            with lock:
                sid = servers.pop(hostname, None)
                if sid is None:
                    continue   # already removed by a concurrent /rm
                chmap.remove_server(sid)
                new_id = server_id_counter
                server_id_counter += 1

            new_name = random_hostname()

            # Docker operations happen outside the lock so user requests are not blocked
            kill_container(hostname)
            if spawn_container(new_name, new_id):
                with lock:
                    servers[new_name] = new_id
                    chmap.add_server(new_id)
            else:
                print(f"[LB] Failed to spawn replacement for {hostname}")


# endpoints 

@app.route("/rep", methods=["GET"])
def rep():
    """Return the current replica count and hostnames.

    Returns:
        JSON response with the list of running replicas and HTTP 200.
    """
    with lock:
        return jsonify({
            "message": {"N": len(servers), "replicas": list(servers.keys())},
            "status": "successful"
        }), 200


@app.route("/add", methods=["POST"])
def add():
    """Scale up: spawn `n` new server containers (using any given
    `hostnames`, filling the rest with random ones) and register them
    on the consistent hash ring.

    Returns:
        JSON response with updated list of replicas and HTTP 200, or HTTP 400 on error.
    """
    global server_id_counter
    data      = request.json
    n         = data.get("n", 0)
    hostnames = list(data.get("hostnames", []))

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure"
        }), 400

    while len(hostnames) < n:
        hostnames.append(random_hostname())

    with lock:
        for hostname in hostnames:
            add_server_internal(hostname, server_id_counter)
            server_id_counter += 1
        return jsonify({
            "message": {"N": len(servers), "replicas": list(servers.keys())},
            "status": "successful"
        }), 200



@app.route("/rm", methods=["DELETE"])
def remove():
    """Scale down: remove `n` server containers (specific `hostnames`
    if given, otherwise chosen at random) from the ring and tear them
    down.

    Returns:
        JSON response with updated list of replicas and HTTP 200, or HTTP 400 on error.
    """
    data      = request.json
    n         = data.get("n", 0)
    hostnames = list(data.get("hostnames", []))

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure"
        }), 400

    with lock:
        remaining  = n - len(hostnames)
        candidates = [h for h in servers if h not in hostnames]
        hostnames += random.sample(candidates, min(remaining, len(candidates)))

        for hostname in hostnames:
            if hostname in servers:
                remove_server_internal(hostname)

        return jsonify({
            "message": {"N": len(servers), "replicas": list(servers.keys())},
            "status": "successful"
        }), 200



@app.route("/<path:path>", methods=["GET"])
def route(path: str):
    """Forward an arbitrary GET request to whichever server the
    consistent-hash ring selects for a freshly generated random
    request ID.

    Args:
        path (str): The remaining URL path that the client requested.

    Returns:
        JSON response forwarded from the target server or an error status code.
    """
    req_id = random.randint(100000, 999999)
    with lock:
        server_id = chmap.get_server(req_id)
        target    = next((h for h, sid in servers.items() if sid == server_id), None)

    if target is None:
        return jsonify({
            "message": "<Error> No servers available",
            "status": "failure"
        }), 503

    try:
        r = req.get(f"http://{target}:5000/{path}", timeout=5)
        if r.status_code == 404:
            return jsonify({
                "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
                "status": "failure"
            }), 400
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({
            "message": f"<Error> Server '{target}' is unavailable",
            "status": "failure"
        }), 503



if __name__ == "__main__":
    init_servers()
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)

import subprocess
import time
import sys
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
BLOCKCHAIN_DIR = os.path.join(ROOT_DIR, "blockchain")
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = SCRIPT_DIR

processes = []

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    DIM = Style.DIM
    BRIGHT = Style.BRIGHT
    RESET = Style.RESET_ALL
except ImportError:
    GREEN = YELLOW = RED = CYAN = WHITE = DIM = BRIGHT = RESET = ""


def log(msg, color=WHITE, bright=False):
    prefix = BRIGHT if bright else ""
    print(f"{prefix}{color}{msg}{RESET}")


def log_header(msg):
    log("=" * 60, CYAN, bright=True)
    log(f"  {msg}", CYAN, bright=True)
    log("=" * 60, CYAN, bright=True)


def log_step(msg):
    log(f"  >> {msg}", WHITE)


def log_success(msg):
    log(f"  [OK] {msg}", GREEN)


def log_error(msg):
    log(f"  [ERROR] {msg}", RED)


def log_warning(msg):
    log(f"  [WARN] {msg}", YELLOW)


def update_contract_address(new_address):
    backend_file = os.path.join(BACKEND_DIR, "blockchain.py")
    with open(backend_file, "r") as f:
        content = f.read()
    old = re.search(r'contract_address = "[^"]*"', content)
    if old:
        old_address = old.group()
        if old_address != f'contract_address = "{new_address}"':
            content = content.replace(old_address, f'contract_address = "{new_address}"')
            with open(backend_file, "w") as f:
                f.write(content)
            log_success(f"Updated contract address in backend/blockchain.py")
            log(f"       Old: {old_address}", DIM)
            log(f"       New: {new_address}", GREEN)
        else:
            log(f"       Contract address unchanged: {new_address}", DIM)
    else:
        log_warning(f"Could not find contract_address in blockchain.py — please update manually")


def start_service(name, cwd, command):
    log(f"Starting {name}...", CYAN)
    try:
        proc = subprocess.Popen(
            command,
            cwd=cwd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        processes.append((name, proc))
        log_success(f"{name} started (PID: {proc.pid})")
        return proc
    except Exception as e:
        log_error(f"Failed to start {name}: {e}")
        return None


def wait_for_service(url, name, max_attempts=15):
    import urllib.request
    import urllib.error

    for i in range(max_attempts):
        time.sleep(2)
        try:
            urllib.request.urlopen(url, timeout=5)
            log_success(f"{name} is ready!")
            return True
        except (urllib.error.URLError, urllib.error.HTTPError):
            log(f"  Waiting for {name}... ({i+1}/{max_attempts})", DIM)
        except Exception:
            log(f"  Checking {name}... ({i+1}/{max_attempts})", DIM)
    log_error(f"{name} did not become ready in time")
    return False


def run_command(command, cwd):
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1


def check_ipfs_installed():
    result = subprocess.run(
        "ipfs --version",
        shell=True,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def stop_all():
    log("\nStopping all services...", YELLOW)
    for name, proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
            log(f"  Stopped {name}", DIM)
        except Exception:
            try:
                proc.kill()
                log(f"  Killed {name}", DIM)
            except Exception:
                pass
    log_success("All services stopped.")


def main():
    log_header("TRANSCRIPT VERIFICATION — SERVICE STARTER")

    log(f"\nDirectories:", WHITE, bright=True)
    log(f"  Blockchain: {BLOCKCHAIN_DIR}", DIM)
    log(f"  Backend:    {BACKEND_DIR}", DIM)
    log(f"  Frontend:   {FRONTEND_DIR}", DIM)

    # Check and start IPFS
    log("\n[Step 1/6] Checking IPFS...", WHITE, bright=True)
    if not check_ipfs_installed():
        log_error("IPFS is not installed!")
        log("", WHITE)
        log("  To install IPFS, run one of the following:", WHITE)
        log("  - Chocolatey: choco install ipfs", DIM)
        log("  - Manual: download from https://dist.ipfs.tech", DIM)
        log("  - Desktop: https://docs.ipfs.tech/install/ipfs-desktop/", DIM)
        log("", WHITE)
        log_warning("  Skipping IPFS — file storage will not work.", YELLOW)
        ipfs_started = False
    else:
        log("  IPFS found, attempting to start daemon...", CYAN)
        ipfs_result = subprocess.run(
            "ipfs daemon",
            shell=True,
            capture_output=True,
            text=True,
        )
        if ipfs_result.returncode == 0 or "Daemon is running" in ipfs_result.stdout:
            log_success("IPFS daemon is running")
            ipfs_started = True
        else:
            log_warning("Could not start IPFS daemon. File storage may not work.")
            log(f"  {ipfs_result.stdout[:200]}", DIM)
            ipfs_started = False

    log("\n[Step 2/6] Starting Hardhat node...", WHITE, bright=True)
    proc_node = start_service(
        "Hardhat Node",
        BLOCKCHAIN_DIR,
        "npx hardhat node",
    )
    if not proc_node:
        log_error("Hardhat node failed to start. Exiting.")
        sys.exit(1)

    log("Waiting for Hardhat node to be ready...", YELLOW)
    if not wait_for_service("http://127.0.0.1:8545", "Hardhat Node", max_attempts=20):
        log_error("Hardhat node did not start. Check if port 8545 is in use.")
        sys.exit(1)

    log_success("Hardhat node is running")

    log("\n[Step 3/6] Compiling contract...", WHITE, bright=True)
    log_step("Running: npx hardhat compile")
    stdout, stderr, code = run_command("npx hardhat compile", BLOCKCHAIN_DIR)
    if code == 0:
        log_success("Contract compiled successfully")
    else:
        log_error("Contract compilation failed")
        log(f"Output: {stdout[:300]}", RED)
        log(f"Errors: {stderr[:300]}", RED)

    log("\n[Step 4/6] Deploying contract...", WHITE, bright=True)
    log_step("Running: npx hardhat run scripts/deploy.cjs --network localhost")
    stdout, stderr, code = run_command(
        "npx hardhat run scripts/deploy.cjs --network localhost",
        BLOCKCHAIN_DIR,
    )

    new_address = None
    for line in stdout.split("\n"):
        if "Contract deployed to:" in line:
            new_address = line.split("Contract deployed to:")[-1].strip()
            break

    if new_address:
        log_success(f"Contract deployed at: {new_address}")
        update_contract_address(new_address)
    else:
        log_error("Could not find contract address in deployment output")
        log(f"Output: {stdout[:500]}", DIM)
        if code != 0:
            log(f"Stderr: {stderr[:300]}", RED)

    log("\n[Step 5/6] Starting backend...", WHITE, bright=True)
    proc_backend = start_service(
        "Backend (FastAPI)",
        BACKEND_DIR,
        "python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000",
    )

    if proc_backend:
        wait_for_service("http://127.0.0.1:8000/", "Backend")

    log("\n[Step 6/6] Starting frontend...", WHITE, bright=True)
    proc_frontend = start_service(
        "Frontend (Streamlit)",
        FRONTEND_DIR,
        "python -m streamlit run main.py --server.port 8501",
    )

    if proc_frontend:
        wait_for_service("http://localhost:8501", "Frontend", max_attempts=20)

    log_header("ALL SERVICES STARTED")
    log("", WHITE)
    log(f"  Frontend:  http://localhost:8501", GREEN, bright=True)
    log(f"  Backend:   http://127.0.0.1:8000", WHITE)
    log(f"  API Docs:  http://127.0.0.1:8000/docs", DIM)
    log("", WHITE)
    log(f"  Default login: admin / admin123", YELLOW)
    log("", WHITE)
    if ipfs_started:
        log_success("IPFS daemon is running — file storage enabled", GREEN)
    else:
        log_warning("IPFS not running — file storage disabled", YELLOW)
    log("", WHITE)
    log("  Press Ctrl+C to stop all services.", DIM)
    log("=" * 60 + "\n", CYAN)

    try:
        while True:
            time.sleep(5)
            dead = []
            for name, proc in processes:
                if proc.poll() is not None:
                    dead.append((name, proc))
                    log_error(f"{name} stopped unexpectedly!")
            for item in dead:
                processes.remove(item)
            if not processes:
                log_error("All processes stopped. Exiting.")
                break
    except KeyboardInterrupt:
        stop_all()


if __name__ == "__main__":
    main()

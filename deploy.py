import subprocess
import sys
import logging
import os
import tarfile
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def run_cmd(cmd, shell=False, check=True, cwd=None):
    logging.info(f"Running: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    result = subprocess.run(cmd, shell=shell, check=check, cwd=cwd, text=True, capture_output=True)
    return result

def deploy_to_vps():
    """
    Automates deployment to a Private US VPS via SSH/SCP.
    Reads target details from a local .env file.
    """
    load_dotenv()

    vps_ip = os.getenv("VPS_IP")
    ssh_user = os.getenv("SSH_USER")
    target_dir = os.getenv("TARGET_DIR", "/opt/liquidity-arena")

    if not vps_ip or not ssh_user:
        logging.error("VPS_IP and SSH_USER must be set in the environment or .env file.")
        sys.exit(1)

    ssh_target = f"{ssh_user}@{vps_ip}"

    # 1. Package the codebase
    tar_filename = "liquidity-arena-deploy.tar.gz"
    logging.info(f"Packaging codebase into {tar_filename}...")

    def exclude_files(tarinfo):
        # Exclude common directories that shouldn't be deployed
        name = tarinfo.name
        # The path typically starts with "./" or just the top-level name
        # We'll normalize by stripping leading "./"
        if name.startswith("./"):
            name = name[2:]

        # Exact root directory names to exclude, and .env
        excludes = [".venv", "__pycache__", ".git", "pytest_cache", "logs", ".env"]

        # Check if the path belongs to an excluded directory or is the tar itself
        if name == tar_filename:
            return None

        path_parts = Path(name).parts
        if len(path_parts) > 0 and path_parts[0] in excludes:
            return None

        return tarinfo

    with tarfile.open(tar_filename, "w:gz") as tar:
        tar.add(".", arcname=".", filter=exclude_files)

    try:
        # 2. Upload the package
        logging.info(f"Uploading {tar_filename} to {ssh_target}:{target_dir}...")
        run_cmd(["ssh", ssh_target, f"mkdir -p {target_dir}"])
        run_cmd(["scp", tar_filename, f"{ssh_target}:{target_dir}/"])

        # 3. Extract and setup environment remotely FIRST
        logging.info("Setting up remote environment and installing dependencies...")

        # We also generate the systemd file dynamically to match the exact target paths/user
        systemd_service = f"""[Unit]
Description=Hybrid Decision Intelligence Engine (Liquidity Arena 2026)
After=network.target

[Service]
Type=simple
User={ssh_user}
Group={ssh_user}
WorkingDirectory={target_dir}
Environment="PATH={target_dir}/.venv/bin"
EnvironmentFile={target_dir}/.env
ExecStart={target_dir}/.venv/bin/python src/execution/live_trading.py
Restart=always
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=5
KillSignal=SIGTERM
TimeoutStopSec=30
SendSIGKILL=yes

[Install]
WantedBy=multi-user.target
"""
        with open("liquidity-arena.service.tmp", "w") as f:
            f.write(systemd_service)

        run_cmd(["scp", "liquidity-arena.service.tmp", f"{ssh_target}:{target_dir}/liquidity-arena.service"])
        os.remove("liquidity-arena.service.tmp")

        setup_script = f"""
        cd {target_dir}
        tar -xzf {tar_filename}
        rm {tar_filename}
        python3.10 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        mkdir -p logs
        sudo cp liquidity-arena.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable liquidity-arena
        """
        run_cmd(["ssh", ssh_target, setup_script])

        # 4. Generate remote .env and upload securely AFTER extraction
        remote_env_content = ""
        rapidx_api_key = os.getenv("PROD_RAPIDX_API_KEY", "generate_or_inject_api_key_here")
        rapidx_api_secret = os.getenv("PROD_RAPIDX_API_SECRET", "generate_or_inject_api_secret_here")

        remote_env_content += f"RAPIDX_API_KEY={rapidx_api_key}\n"
        remote_env_content += f"RAPIDX_API_SECRET={rapidx_api_secret}\n"

        temp_env_file = ".env.remote.tmp"
        with open(temp_env_file, "w") as f:
            f.write(remote_env_content)

        try:
            logging.info("Uploading securely generated .env...")
            run_cmd(["scp", temp_env_file, f"{ssh_target}:{target_dir}/.env"])
        finally:
            os.remove(temp_env_file)

        # 5. Restart service
        run_cmd(["ssh", ssh_target, "sudo systemctl restart liquidity-arena"])

        logging.info("Deployment successful! Systemd service restarted.")

    except subprocess.CalledProcessError as e:
        logging.error(f"Deployment failed during command execution: {e.cmd}")
        logging.error(f"Stdout: {e.stdout}")
        logging.error(f"Stderr: {e.stderr}")
        sys.exit(1)
    finally:
        if os.path.exists(tar_filename):
            os.remove(tar_filename)

if __name__ == "__main__":
    deploy_to_vps()

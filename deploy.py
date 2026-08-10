import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def deploy_to_cloud_run(project_id: str, service_name: str, region: str, image_tag: str):
    """
    Deploys the Hybrid Decision Intelligence Engine to GCP Cloud Run.
    """
    logging.info(f"Starting deployment for {service_name} to region {region} in project {project_id}...")

    # 1. Build the Docker image using Cloud Build
    image_uri = f"gcr.io/{project_id}/{service_name}:{image_tag}"
    build_cmd = [
        "gcloud", "builds", "submit",
        "--tag", image_uri,
        "--project", project_id
    ]

    logging.info(f"Building image: {' '.join(build_cmd)}")
    # Uncomment in real execution
    result = subprocess.run(build_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Build failed: {result.stderr}")
        sys.exit(1)

    # 2. Deploy to Cloud Run
    deploy_cmd = [
        "gcloud", "run", "deploy", service_name,
        "--image", image_uri,
        "--region", region,
        "--platform", "managed",
        "--project", project_id,
        "--allow-unauthenticated",
        "--memory", "2Gi",
        "--cpu", "1",
        "--concurrency", "80"
    ]

    logging.info(f"Deploying to Cloud Run: {' '.join(deploy_cmd)}")
    # Uncomment in real execution
    result = subprocess.run(deploy_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Deployment failed: {result.stderr}")
        sys.exit(1)

    logging.info("Deployment successful! Service is now live.")

if __name__ == "__main__":
    # Default parameters for the declarative script
    PROJECT_ID = "liquidity-arena-2026"
    SERVICE_NAME = "hybrid-engine-router"
    REGION = "us-central1"
    IMAGE_TAG = "latest"

    deploy_to_cloud_run(PROJECT_ID, SERVICE_NAME, REGION, IMAGE_TAG)

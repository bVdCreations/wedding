import logging
import os
import subprocess
from datetime import UTC, datetime

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %Z",
)

logger = logging.getLogger("access")


app = FastAPI()


class DeployRequest(BaseModel):
    tag: str


def update_env_file(env_file: str, image_base: str, tag: str):
    new_image = f"{image_base}:{tag}"
    logger.info(f"Updating env file: {env_file} with image: {new_image}")
    if not os.path.exists(env_file):
        logger.info(f"Env file does not exist, creating new file: {env_file}")
        with open(env_file, "w") as f:
            f.write(f"API_IMAGE={new_image}\n")
        logger.debug(f"Written API_IMAGE={new_image} to new file")
        return

    lines = []
    found = False
    with open(env_file) as f:
        for line in f:
            if line.startswith("API_IMAGE="):
                lines.append(f"API_IMAGE={new_image}\n")
                found = True
                logger.debug(f"Replacing existing API_IMAGE line: {line.strip()}")
            else:
                lines.append(line)

    if not found:
        lines.append(f"API_IMAGE={new_image}\n")
        logger.debug("Added new API_IMAGE line")

    with open(env_file, "w") as f:
        f.writelines(lines)

    logger.info(f"Successfully updated env file: {env_file}")


@app.post("/webhook")
async def deploy(http_request: Request, request: DeployRequest, authorization: str = Header(None)):
    try:
        logger.info("=" * 60)
        logger.info("Received deploy request at %s", datetime.now(UTC).isoformat())
        logger.debug(f"Request body: {request.model_dump_json()}")

        if client := http_request.client:
            client_host = client.host
            logger.info(f"Request from IP: {client_host}")

        headers = dict(http_request.headers)
        sanitized_headers = {
            k: v if k.lower() != "authorization" else "[REDACTED]" for k, v in headers.items()
        }
        logger.debug(f"Request headers: {sanitized_headers}")

        expected_secret = os.getenv("WEBHOOK_SECRET")
        if not expected_secret:
            logger.error("WEBHOOK_SECRET environment variable not set")
            raise HTTPException(status_code=500, detail="Webhook not configured")

        if not authorization or not authorization.startswith("Bearer "):
            logger.warning(f"Invalid authorization header from {client_host}")
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = authorization[7:]
        if token != expected_secret:
            logger.warning(f"Invalid token from {client_host}")
            raise HTTPException(status_code=401, detail="Invalid token")

        logger.info("Authentication successful")

        compose_file = os.getenv("COMPOSE_FILE", "docker-compose.prod.yml")
        env_file = os.getenv("ENV_FILE", ".env.prod")
        image_base = os.getenv("API_IMAGE_BASE", "ghcr.io/owner/wedding-api")

        logger.info(
            f"Configuration: compose_file={compose_file}, env_file={env_file}, image_base={image_base}, tag={request.tag}"
        )

        update_env_file(env_file, image_base, request.tag)

        pull_cmd = [
            "docker",
            "compose",
            "-f",
            compose_file,
            "--env-file",
            env_file,
            "--env",
            f"API_IMAGE={image_base}:{request.tag}",
            "pull",
            "api",
        ]
        logger.info(f"Executing pull command: {' '.join(pull_cmd)}")
        pull_result = subprocess.run(pull_cmd, capture_output=True, text=True)
        logger.debug(f"Pull stdout: {pull_result.stdout}")
        logger.debug(f"Pull stderr: {pull_result.stderr}")
        if pull_result.returncode != 0:
            logger.error(
                f"Pull failed with return code {pull_result.returncode}: {pull_result.stderr}"
            )
            raise HTTPException(status_code=500, detail=f"Pull failed: {pull_result.stderr}")

        logger.info("Pull successful")

        up_cmd = [
            "docker",
            "compose",
            "-f",
            compose_file,
            "--env-file",
            env_file,
            "--env",
            f"API_IMAGE={image_base}:{request.tag}",
            "up",
            "-d",
            "api",
        ]
        logger.info(f"Executing up command: {' '.join(up_cmd)}")
        up_result = subprocess.run(up_cmd, capture_output=True, text=True)
        logger.debug(f"Up stdout: {up_result.stdout}")
        logger.debug(f"Up stderr: {up_result.stderr}")
        if up_result.returncode != 0:
            logger.error(f"Up failed with return code {up_result.returncode}: {up_result.stderr}")
            raise HTTPException(status_code=500, detail=f"Deploy failed: {up_result.stderr}")

        logger.info("Deploy successful")

        new_image = f"{image_base}:{request.tag}"
        response = {"status": "success", "tag": request.tag, "image": new_image}
        logger.info(f"Response: {response}")
        logger.info("=" * 60)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during deploy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

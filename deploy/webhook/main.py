import os
import subprocess

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI()


class DeployRequest(BaseModel):
    tag: str


def update_env_file(env_file: str, image_base: str, tag: str):
    new_image = f"{image_base}:{tag}"
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write(f"API_IMAGE={new_image}\n")
        return

    lines = []
    found = False
    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("API_IMAGE="):
                lines.append(f"API_IMAGE={new_image}\n")
                found = True
            else:
                lines.append(line)

    if not found:
        lines.append(f"API_IMAGE={new_image}\n")

    with open(env_file, "w") as f:
        f.writelines(lines)


@app.post("/webhook")
async def deploy(request: DeployRequest, authorization: str = Header(None)):
    expected_secret = os.getenv("WEBHOOK_SECRET")
    if not expected_secret:
        raise HTTPException(status_code=500, detail="Webhook not configured")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization[7:]
    if token != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid token")

    compose_file = os.getenv("COMPOSE_FILE", "docker-compose.prod.yml")
    env_file = os.getenv("ENV_FILE", ".env.prod")
    image_base = os.getenv("API_IMAGE_BASE", "ghcr.io/owner/wedding-api")

    update_env_file(env_file, image_base, request.tag)

    pull_cmd = ["docker", "compose", "-f", compose_file, "--env-file", env_file, "pull", "api"]
    pull_result = subprocess.run(pull_cmd, capture_output=True, text=True)
    if pull_result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Pull failed: {pull_result.stderr}")

    up_cmd = ["docker", "compose", "-f", compose_file, "--env-file", env_file, "up", "-d", "api"]
    up_result = subprocess.run(up_cmd, capture_output=True, text=True)
    if up_result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Deploy failed: {up_result.stderr}")

    new_image = f"{image_base}:{request.tag}"
    return {"status": "success", "tag": request.tag, "image": new_image}

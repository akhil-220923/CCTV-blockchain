#!/usr/bin/env python3
"""
Automated Render Cloud Deployment & Verification Script for CCTV-blockchain (IBVAP).
Uses official Render REST API v1.
"""

import os
import sys
import json
import time
import requests

RENDER_API_BASE = "https://api.render.com/v1"
REPO_URL = "https://github.com/akhil-220923/CCTV-blockchain"
SERVICE_NAME = "cctv-blockchain"


def get_headers(api_key: str):
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


def deploy_to_render(api_key: str):
    headers = get_headers(api_key)

    # 1. Verify credentials and retrieve owner / workspace ID
    print("[1/6] Authenticating with Render API...")
    owners_res = requests.get(f"{RENDER_API_BASE}/owners", headers=headers)
    if owners_res.status_code != 200:
        print(f"Error authenticating with Render: {owners_res.status_code} - {owners_res.text}")
        sys.exit(1)

    owners = owners_res.json()
    if not owners:
        print("Error: No owner or workspace found on this Render account.")
        sys.exit(1)

    owner_id = owners[0]["owner"]["id"]
    owner_name = owners[0]["owner"].get("name", owner_id)
    print(f"  ✓ Authenticated as '{owner_name}' (Owner ID: {owner_id})")

    # 2. Check for existing service
    print("[2/6] Checking for existing Render service...")
    services_res = requests.get(f"{RENDER_API_BASE}/services", headers=headers, params={"limit": 50})
    service_id = None
    service_url = None

    if services_res.status_code == 200:
        for s in services_res.json():
            svc = s.get("service", {})
            if svc.get("name") == SERVICE_NAME or (svc.get("repo") == REPO_URL and svc.get("type") == "web_service"):
                service_id = svc.get("id")
                service_url = svc.get("serviceDetails", {}).get("url")
                print(f"  Found existing service '{svc.get('name')}' (ID: {service_id}) -> URL: {service_url}")
                break

    # 3. Create service if not present
    if not service_id:
        print(f"[3/6] Creating new Web Service '{SERVICE_NAME}' on Render...")
        payload = {
            "type": "web_service",
            "name": SERVICE_NAME,
            "ownerId": owner_id,
            "repo": REPO_URL,
            "branch": "main",
            "autoDeploy": "yes",
            "serviceDetails": {
                "env": "docker",
                "dockerfilePath": "Dockerfile",
                "dockerContext": ".",
                "region": "oregon",
                "plan": "free",
                "healthCheckPath": "/health",
                "envVars": [
                    {"key": "PORT", "value": "10000"},
                    {"key": "NODE_ENV", "value": "production"},
                    {"key": "CORS_ORIGIN", "value": "*"},
                    {"key": "PYTHONUNBUFFERED", "value": "1"}
                ]
            }
        }
        create_res = requests.post(f"{RENDER_API_BASE}/services", headers=headers, json=payload)
        if create_res.status_code not in (200, 201):
            print(f"Service creation returned {create_res.status_code}: {create_res.text}")
            print("Retrying with unique timestamped service name...")
            payload["name"] = f"cctv-blockchain-{int(time.time())}"
            create_res = requests.post(f"{RENDER_API_BASE}/services", headers=headers, json=payload)
            if create_res.status_code not in (200, 201):
                print(f"Failed to create service: {create_res.status_code} - {create_res.text}")
                sys.exit(1)

        new_svc = create_res.json()
        service_id = new_svc.get("id")
        service_url = new_svc.get("serviceDetails", {}).get("url")
        print(f"  ✓ Service successfully created! (ID: {service_id})")
    else:
        # Trigger deploy on existing service
        print(f"[3/6] Triggering deploy latest commit on existing service ({service_id})...")
        deploy_res = requests.post(f"{RENDER_API_BASE}/services/{service_id}/deploys", headers=headers, json={"clearCache": "do_not_clear"})
        if deploy_res.status_code in (200, 201):
            print(f"  ✓ Deployment triggered.")
        else:
            print(f"  Deploy trigger response: {deploy_res.status_code} - {deploy_res.text}")

    # 4. Monitor Deployment Status
    print(f"[4/6] Monitoring deployment progress...")
    poll_count = 0
    max_polls = 60  # ~10 minutes
    status = "building"

    while poll_count < max_polls:
        deploys_res = requests.get(f"{RENDER_API_BASE}/services/{service_id}/deploys", headers=headers, params={"limit": 1})
        if deploys_res.status_code == 200 and deploys_res.json():
            latest = deploys_res.json()[0].get("deploy", {})
            status = latest.get("status", "unknown")
            print(f"  Status: {status} (poll {poll_count + 1}/{max_polls})")
            if status == "live":
                print("  ✓ Deployment is LIVE!")
                break
            elif status in ("build_failed", "update_failed", "canceled", "deactivated"):
                print(f"  Deployment ended with status: {status}")
                break
        time.sleep(10)
        poll_count += 1

    # 5. Retrieve final Service details
    svc_detail_res = requests.get(f"{RENDER_API_BASE}/services/{service_id}", headers=headers)
    if svc_detail_res.status_code == 200:
        service_url = svc_detail_res.json().get("serviceDetails", {}).get("url") or service_url

    print(f"\n[5/6] Service Public URL: {service_url}")

    # 6. Verify Health Endpoint
    if service_url:
        print("[6/6] Verifying public endpoint health...")
        health_url = f"{service_url.rstrip('/')}/health"
        for attempt in range(12):
            try:
                res = requests.get(health_url, timeout=10)
                if res.status_code == 200:
                    print(f"  ✓ Health check passed (HTTP 200): {res.json()}")
                    print("\n" + "=" * 60)
                    print(f"  DEPLOYMENT COMPLETE & VERIFIED")
                    print(f"  PUBLIC URL: {service_url}")
                    print("=" * 60)
                    return service_url
                else:
                    print(f"  Attempt {attempt + 1}: status code {res.status_code}")
            except Exception as e:
                print(f"  Attempt {attempt + 1}: connection waiting ({e})")
            time.sleep(10)

    return service_url


if __name__ == "__main__":
    key = os.environ.get("RENDER_API_KEY")
    if not key and len(sys.argv) > 1:
        key = sys.argv[1]

    if not key:
        print("Usage: python3 scripts/deploy_render.py <RENDER_API_KEY>")
        print("Or set RENDER_API_KEY environment variable.")
        sys.exit(1)

    deploy_to_render(key)

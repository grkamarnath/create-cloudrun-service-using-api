import json
import os
from typing import Optional

import requests
from google import auth
from google.auth.transport.requests import Request

from logger import Logger


class CloudRunException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def create_service(
        service_name: str,
        project_id: str,
        service_account: str,
        image: str,
        environment_variables: Optional[list]
):
    url = f"{_base_url()}apis/serving.knative.dev/v1/namespaces/{project_id}/services"
    response = requests.post(
        url=url,
        data=_cloud_run_payload(service_name, project_id, service_account, image, environment_variables),
        headers=header()
    )
    if response.status_code != 200:
        Logger.error(response.text)
    if response.status_code == 409:
        raise CloudRunException(f"The service with the name: {service_name} already exists")
    response.raise_for_status()
    return response


def _base_url():
    return "https://us-central1-run.googleapis.com/"


def _token():
    credentials = auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform",
                "https://www.googleapis.com/auth/cloud-platform.read-only"])[0]
    credentials.refresh(Request())
    return credentials.token


def header():
    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {_token()}"
    }
    return headers


def _cloud_run_payload(
        service_name: str,
        project_id: str,
        service_account: Optional[str],
        image: str,
        environment_variables: Optional[list]
) -> str:
    payload: dict = {
        "apiVersion": "serving.knative.dev/v1",
        "kind": "Service",
        "metadata": {
            "name": service_name,
            "namespace": project_id
        },
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "autoscaling.knative.dev/minScale": "0",
                        "autoscaling.knative.dev/maxScale": "1"
                    }
                },
                "spec": {
                    "timeoutSeconds": 180,
                    "serviceAccountName": service_account,
                    "containers": [
                        {
                            "image": image,
                            "env": environment_variables,
                            "resources": {
                                "limits": {
                                    "memory": "128Mi"
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    return json.dumps(payload)


if __name__ == "__main__":
    image_path = "us-docker.pkg.dev/cloudrun/container/hello"
    cloud_run_name = "cloud-run-name"
    gcp_project_id = os.environ["GCP_PROJECT"]
    service_account = os.environ["SERVICE_ACCOUNT"]
    environment_variables = [
        {
            "name": "test_d",
            "value": "value",
        },
        {
            "name": "test_d1",
            "value": "value1",
        }
    ]
    create_service(cloud_run_name, gcp_project_id, service_account, image_path, environment_variables)

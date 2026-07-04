# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from dotenv import load_dotenv
load_dotenv()

import os
import logging
import google.auth
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

class LocalLogger:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def log_struct(self, data, severity="INFO"):
        self.logger.info(f"Feedback: {data}")

# Attempt to configure GCP telemetry and logging if credentials exist.
# Fall back to local logging and disable cloud tracing if credentials are not valid.
otel_to_cloud = False
try:
    setup_telemetry()
    _, project_id = google.auth.default()
    from google.cloud import logging as google_cloud_logging
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
    otel_to_cloud = True
except Exception:
    logger = LocalLogger()

allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

# Artifact bucket for ADK
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_service_uri = None
artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    otel_to_cloud=otel_to_cloud,
)
app.title = "customer-support-agent"
app.description = "API for interacting with the customer-support-agent graph workflow"


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

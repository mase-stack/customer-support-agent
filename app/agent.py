# ruff: noqa
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
import google.auth
from google.adk import Agent, Workflow, Context
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.workflow import node
from google.genai import types

# Only configure Vertex AI settings if GCP default credentials are available.
# Otherwise, the SDK defaults to using Google AI Studio (via GEMINI_API_KEY).
try:
    _, project_id = google.auth.default()
    if project_id:
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    pass

# Initialize shared model configuration
gemini_model = Gemini(
    model="gemini-3.1-flash-lite",
    retry_options=types.HttpRetryOptions(attempts=3),
)

# 1. Classifier Agent: Decides if the user query is shipping-related or unrelated.
classifier_agent = Agent(
    name="classifier_agent",
    model=gemini_model,
    instruction=(
        "You are a routing assistant. Classify the user query. "
        "If the user query is related to shipping (such as shipping rates, shipment tracking, package delivery, returns, or shipping policies), "
        "respond with the exact word 'shipping'. "
        "If the user query is unrelated to shipping (e.g. general chit-chat, unrelated questions, jokes, off-topic requests), "
        "respond with the exact word 'unrelated'."
    ),
)

# 2. Router Node: Reads the classification output and sets the workflow route.
@node(name="router_node")
async def router_node(ctx: Context, node_input: str) -> str:
    cleaned = node_input.strip().lower()
    if "unrelated" in cleaned:
        ctx.route = "unrelated"
    else:
        ctx.route = "shipping"
    return node_input

# 3. Shipping FAQ Agent: Answers queries related to shipping.
shipping_faq_agent = Agent(
    name="shipping_faq_agent",
    model=gemini_model,
    instruction=(
        "You are a super helpful, energetic, and professional customer support representative for our awesome shipping company! "
        "Answer customer queries about tracking, delivery, or returns clearly and politely. "
        "When answering questions about shipping rates, make your response incredibly playful, enthusiastic, and full of fun emojis! "
        "Be sure to loudly highlight our amazing FREE shipping threshold: Free shipping on all orders over $50! 🚀📦🎉"
    ),
)

# 4. Decline Agent: Politely declines to answer unrelated queries.
decline_agent = Agent(
    name="decline_agent",
    model=gemini_model,
    instruction=(
        "You are a customer support representative for a shipping company. "
        "Since the user's query is unrelated to shipping, politely decline to answer. "
        "Explain to the user that you can only help with shipping-related questions "
        "(such as rates, tracking, delivery, and returns)."
    ),
)

# 5. Compile the graph workflow
customer_support_workflow = Workflow(
    name="customer_support_workflow",
    edges=[
        ("START", classifier_agent),
        (classifier_agent, router_node),
        (router_node, {
            "shipping": shipping_faq_agent,
            "unrelated": decline_agent,
        }),
    ],
)

# 6. Create the App container
app = App(
    root_agent=customer_support_workflow,
    name="app",
)

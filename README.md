# Customer Support Agent

A graph workflow agent project built using Google Agent Development Kit (ADK) 2.0.

## Overview

This project implements a customer support representative for a shipping company. The workflow works as follows:

1. **Classification Node (`classifier_agent`)**: First classifies the user query to check if it is related to shipping (rates, tracking, delivery, returns) or unrelated.
2. **Router Node (`router_node`)**: Deterministically routes the flow based on the classification.
3. **FAQ Node (`shipping_faq_agent`)**: If the query is related to shipping, this node answers the query.
4. **Decline Node (`decline_agent`)**: If the query is unrelated, this node politely declines to answer.

## Project Structure

- `app/agent.py`: Defines the agent workflow, sub-agents, and compiling of the graph.
- `app/fast_api_app.py`: Sets up a FastAPI wrapper using ADK.
- `pyproject.toml`: Defines dependencies and project settings.
- `agents-cli-manifest.yaml`: CLI configuration for testing and managing the project.
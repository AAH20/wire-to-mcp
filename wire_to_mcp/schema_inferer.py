"""
Schema Inference Engine for Wire-to-MCP.
Infers parameter types, constraints, and tool names from captured network frames and curl commands.
"""

import json
import re
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Any, Optional
from .models import HTTPMethod, WiretapFrame, InferredParameter, InferredToolSchema


class SchemaInferer:
    """Infers typed tool signatures from HTTP traffic frames."""

    @staticmethod
    def infer_tool_from_frame(frame: WiretapFrame) -> InferredToolSchema:
        parsed_url = urlparse(frame.url)
        path = parsed_url.path.strip("/")

        # 1. Derive canonical tool name
        # e.g., POST /v1/services/deploy -> deploy_service or post_v1_services_deploy
        segments = [s for s in path.split("/") if not s.startswith("v1") and not s.startswith("v2")]
        if not segments:
            segments = path.split("/")
        
        action = segments[-1] if segments else "action"
        noun = segments[-2] if len(segments) >= 2 else ""
        
        if noun and action not in ("get", "post", "put", "delete"):
            tool_name = f"{action}_{noun}"
        elif noun:
            tool_name = f"{frame.method.value.lower()}_{noun}"
        else:
            tool_name = f"{frame.method.value.lower()}_{action}"

        tool_name = re.sub(r"[^a-zA-Z0-9_]", "_", tool_name).lower()

        # 2. Infer Parameters from Query and Request Body
        parameters: List[InferredParameter] = []

        # Query parameters
        query_dict = parse_qs(parsed_url.query)
        for qk, qv in query_dict.items():
            parameters.append(InferredParameter(
                name=qk,
                param_type="str",
                required=False,
                default_value=qv[0] if qv else None,
                description=f"Query parameter '{qk}'"
            ))

        # Request body parameters
        if isinstance(frame.request_body, dict):
            for k, v in frame.request_body.items():
                ptype = "str"
                if isinstance(v, int) and not isinstance(v, bool):
                    ptype = "int"
                elif isinstance(v, float):
                    ptype = "float"
                elif isinstance(v, bool):
                    ptype = "bool"
                elif isinstance(v, list):
                    ptype = "list"
                elif isinstance(v, dict):
                    ptype = "dict"

                parameters.append(InferredParameter(
                    name=k,
                    param_type=ptype,
                    required=True,
                    default_value=None,
                    description=f"Field '{k}' (inferred from wiretap)"
                ))

        description = f"Autonomous MCP tool synthesized from {frame.method.value} {parsed_url.path}"

        return InferredToolSchema(
            tool_name=tool_name,
            description=description,
            http_method=frame.method,
            endpoint_url=frame.url,
            parameters=parameters,
            response_schema=frame.response_body if isinstance(frame.response_body, dict) else {}
        )

    @staticmethod
    def parse_curl_command(curl_str: str) -> WiretapFrame:
        """Parses a curl command line into a WiretapFrame."""
        method = HTTPMethod.GET
        if "-X POST" in curl_str or "--request POST" in curl_str:
            method = HTTPMethod.POST
        elif "-X PUT" in curl_str or "--request PUT" in curl_str:
            method = HTTPMethod.PUT
        elif "-X DELETE" in curl_str or "--request DELETE" in curl_str:
            method = HTTPMethod.DELETE
        elif "-d " in curl_str or "--data" in curl_str:
            method = HTTPMethod.POST

        # Extract URL
        url_match = re.search(r"https?://[^\s'\"]+", curl_str)
        url = url_match.group(0) if url_match else "http://localhost/api"

        # Extract JSON body
        body = None
        data_match = re.search(r"(?:-d|--data)\s+['\"]({.+?})['\"]", curl_str)
        if data_match:
            try:
                body = json.loads(data_match.group(1))
            except Exception:
                body = {"raw_payload": data_match.group(1)}

        return WiretapFrame(
            url=url,
            method=method,
            request_body=body,
            response_status=200
        )

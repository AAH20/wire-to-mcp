"""
Data models and wiretap specifications for Wire-to-MCP.
Autonomous MCP Server Synthesizer from Passive Wiretap & Network Traffic.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import time


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class WiretapFrame:
    url: str
    method: HTTPMethod
    headers: Dict[str, str] = field(default_factory=dict)
    request_body: Optional[Any] = None
    response_status: int = 200
    response_body: Optional[Any] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class InferredParameter:
    name: str
    param_type: str
    required: bool = True
    default_value: Optional[Any] = None
    description: str = ""


@dataclass
class InferredToolSchema:
    tool_name: str
    description: str
    http_method: HTTPMethod
    endpoint_url: str
    parameters: List[InferredParameter] = field(default_factory=list)
    response_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedMCPServer:
    server_name: str
    source_code: str
    tools: List[InferredToolSchema] = field(default_factory=list)
    generation_duration_ms: float = 0.0

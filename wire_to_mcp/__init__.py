"""
wire-to-mcp: Autonomous MCP Server Synthesizer from Passive Wiretap & Network Traffic.
"""

from .models import (
    HTTPMethod,
    WiretapFrame,
    InferredParameter,
    InferredToolSchema,
    GeneratedMCPServer,
)
from .schema_inferer import SchemaInferer
from .server_synthesizer import MCPServerSynthesizer

__version__ = "0.1.0"
__all__ = [
    "HTTPMethod",
    "WiretapFrame",
    "InferredParameter",
    "InferredToolSchema",
    "GeneratedMCPServer",
    "SchemaInferer",
    "MCPServerSynthesizer",
]

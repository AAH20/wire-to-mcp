"""
Unit tests for Wire-to-MCP curl parsing, schema inference, and server synthesis.
"""

import unittest
from wire_to_mcp.models import HTTPMethod
from wire_to_mcp.schema_inferer import SchemaInferer
from wire_to_mcp.server_synthesizer import MCPServerSynthesizer


class TestWireToMCP(unittest.TestCase):

    def test_curl_parser(self):
        curl = "curl -X POST https://api.corp.com/v1/users -d '{\"name\": \"Alice\", \"age\": 30}'"
        frame = SchemaInferer.parse_curl_command(curl)
        self.assertEqual(frame.method, HTTPMethod.POST)
        self.assertEqual(frame.url, "https://api.corp.com/v1/users")
        self.assertEqual(frame.request_body["name"], "Alice")
        self.assertEqual(frame.request_body["age"], 30)

    def test_schema_inference(self):
        curl = "curl -X POST https://api.corp.com/v1/cluster/deploy -d '{\"env\": \"staging\", \"count\": 5, \"debug\": true}'"
        frame = SchemaInferer.parse_curl_command(curl)
        schema = SchemaInferer.infer_tool_from_frame(frame)

        param_dict = {p.name: p.param_type for p in schema.parameters}
        self.assertEqual(param_dict["env"], "str")
        self.assertEqual(param_dict["count"], "int")
        self.assertEqual(param_dict["debug"], "bool")
        self.assertIn("deploy", schema.tool_name)

    def test_synthesizer_and_execution(self):
        curl = "curl -X POST https://api.corp.com/v1/trigger -d '{\"job\": \"backup\"}'"
        frame = SchemaInferer.parse_curl_command(curl)
        tool_schema = SchemaInferer.infer_tool_from_frame(frame)

        server = MCPServerSynthesizer.synthesize_server("TestMCP", [tool_schema])
        self.assertIn("class SynthesizedMCPServer:", server.source_code)

        # Dynamic execution test
        scope = {}
        exec(server.source_code, scope)
        srv = scope["build_server"]()
        self.assertEqual(len(srv.tools), 1)

        tool_item = list(srv.tools.values())[0]
        res = tool_item["handler"](job="nightly")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["dispatched_payload"]["job"], "nightly")


if __name__ == "__main__":
    unittest.main()

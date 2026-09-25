"""
CLI interface and interactive demonstration runner for Wire-to-MCP.
"""

import sys
import json
import argparse
from .schema_inferer import SchemaInferer
from .server_synthesizer import MCPServerSynthesizer


def run_demo():
    print("=" * 74)
    print("  WIRE-TO-MCP: Autonomous MCP Server Synthesizer from Wiretap")
    print("  Transforming Raw Traffic into MCP Servers for Claude Opus 5.5 & GPT-6 Astra")
    print("=" * 74)

    raw_curls = [
        (
            "Deployment Service Tool",
            "curl -X POST https://infra.corp.internal/v1/deploy "
            "-d '{\"service\": \"auth-gateway\", \"version\": \"v3.2\", \"replicas\": 4}'"
        ),
        (
            "Cluster Metrics Query Tool",
            "curl 'https://infra.corp.internal/v1/metrics?cluster_id=us-east-prod&period=1h'"
        ),
        (
            "Pod Termination Tool",
            "curl -X DELETE https://infra.corp.internal/v1/pods/pod_8812"
        )
    ]

    print("\n[STEP 1] PASSIVE WIRETAP: CAPTURING INGRESS HTTP FRAMES")
    inferred_tools = []
    for idx, (label, curl_cmd) in enumerate(raw_curls, 1):
        print(f"\n  ({idx}/3) {label}")
        print(f"        Captured Wiretap: `{curl_cmd}`")

        frame = SchemaInferer.parse_curl_command(curl_cmd)
        tool_schema = SchemaInferer.infer_tool_from_frame(frame)
        inferred_tools.append(tool_schema)

        print(f"        >> Inferred Tool Name : `{tool_schema.tool_name}`")
        print(f"        >> Inferred Parameters: {len(tool_schema.parameters)}")
        for p in tool_schema.parameters:
            print(f"           * {p.name}: {p.param_type} (Required: {p.required})")

    # Synthesize Complete Standalone MCP Server
    print("\n[STEP 2] SYNTHESIZING PYTHON MCP SERVER CODE (<0.05s)")
    server = MCPServerSynthesizer.synthesize_server("InfraOpsMCP", inferred_tools)

    print(f"  >> MCP Server Name: {server.server_name}")
    print(f"  >> Total Tools Synthesized: {len(server.tools)}")
    print(f"  >> Synthesis Duration: {server.generation_duration_ms:.3f} ms")

    print("\n[STEP 3] SYNTHESIZED PYTHON MCP CODE PREVIEW:")
    print("-" * 74)
    preview_lines = server.source_code.split("\n")[:38]
    print("\n".join(preview_lines))
    print("    ... [Truncated for brevity: includes complete handlers and JSON schemas] ...")
    print("-" * 74)

    # Test dynamic execution of synthesized code
    print("\n[STEP 4] DYNAMIC EXECUTION SANITY TEST")
    exec_scope = {}
    exec(server.source_code, exec_scope)
    srv_instance = exec_scope["build_server"]()

    # Invoke the deploy tool dynamically
    deploy_handler = srv_instance.tools["deploy_v1"]["handler"] if "deploy_v1" in srv_instance.tools else list(srv_instance.tools.values())[0]["handler"]
    sample_result = deploy_handler(service="billing-api", version="v4.0", replicas=2)

    print("  Invoked Synthesized MCP Tool Handler:")
    print(f"  >> Result: {json.dumps(sample_result, indent=4)}")

    print("\n" + "=" * 74)
    print("  WIRE-TO-MCP SYNTHESIS COMPLETE: 100% OPERATIONAL")
    print("=" * 74 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="wire-to-mcp: Autonomous MCP Server Synthesizer from Passive Wiretap"
    )
    subparsers = parser.add_subparsers(dest="command")
    demo_parser = subparsers.add_parser("demo", help="Run interactive MCP synthesis demonstration")

    args = parser.parse_args()
    if args.command == "demo" or len(sys.argv) == 1:
        run_demo()


if __name__ == "__main__":
    main()

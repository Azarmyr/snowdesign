#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stitch MCP Client - HTTP client for Google Stitch remote MCP server.

Communicates with stitch.googleapis.com/mcp using MCP Streamable HTTP transport.
Handles session management, tool calls, and SSE response parsing.

Auth: Set STITCH_API_KEY env var or pass api_key to StitchClient.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

MCP_URL = "https://stitch.googleapis.com/mcp"
PROTOCOL_VERSION = "2025-03-26"
CLIENT_INFO = {"name": "snowdesign", "version": "2.0.0"}


class StitchError(Exception):
    """Stitch API error."""
    def __init__(self, message, code=None, data=None):
        super().__init__(message)
        self.code = code
        self.data = data


class StitchClient:
    """
    MCP HTTP client for Google Stitch.
    
    Usage:
        client = StitchClient(api_key="your-key")
        client.initialize()
        
        # Create design system
        ds = client.create_design_system({"displayName": "My DS", "theme": {...}})
        
        # Create project
        project = client.create_project("My App")
        
        # Generate screen
        screen = client.generate_screen(project_id, "A dashboard with charts", device_type="DESKTOP")
        
        # Get screen code
        code = client.get_screen_code(project_id, screen_id)
    """

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("STITCH_API_KEY", "")
        if not self.api_key:
            raise StitchError(
                "No Stitch API key found. Set STITCH_API_KEY env var or pass api_key.\n"
                "Get your key at: https://stitch.withgoogle.com/settings"
            )
        self.session_id = None
        self._msg_id = 0
        self._initialized = False

    def _next_id(self):
        self._msg_id += 1
        return self._msg_id

    def _make_request(self, method, params=None):
        """Send JSON-RPC request to Stitch MCP endpoint."""
        body = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params is not None:
            body["params"] = params

        data = json.dumps(body).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "X-Goog-Api-Key": self.api_key,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        req = urllib.request.Request(MCP_URL, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                # Capture session ID from response
                new_session = resp.headers.get("Mcp-Session-Id")
                if new_session:
                    self.session_id = new_session

                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read().decode("utf-8")

                if "text/event-stream" in content_type:
                    return self._parse_sse(raw)
                else:
                    return json.loads(raw)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            raise StitchError(
                f"HTTP {e.code}: {e.reason}\n{error_body}",
                code=e.code
            )
        except urllib.error.URLError as e:
            raise StitchError(f"Connection error: {e.reason}")

    def _parse_sse(self, text):
        """Parse Server-Sent Events response, return last complete JSON-RPC result."""
        result = None
        for line in text.strip().split("\n"):
            line = line.strip()
            if line.startswith("data: "):
                try:
                    parsed = json.loads(line[6:])
                    result = parsed
                except json.JSONDecodeError:
                    continue
        return result

    def _extract_result(self, response):
        """Extract result from JSON-RPC response, raise on error."""
        if response is None:
            raise StitchError("Empty response from server")

        if "error" in response:
            err = response["error"]
            raise StitchError(
                err.get("message", "Unknown error"),
                code=err.get("code"),
                data=err.get("data")
            )

        return response.get("result", {})

    def _call_tool(self, tool_name, arguments=None):
        """Call a Stitch MCP tool and return the result."""
        if not self._initialized:
            self.initialize()

        resp = self._make_request("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
        return self._extract_result(resp)

    # ============ SESSION ============

    def initialize(self):
        """Initialize MCP session. Must be called before tool calls."""
        resp = self._make_request("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": CLIENT_INFO
        })
        result = self._extract_result(resp)
        self._initialized = True

        # Send initialized notification (no response expected)
        try:
            self._make_request("notifications/initialized")
        except Exception:
            pass  # Notifications may not get a response

        return result

    def list_tools(self):
        """List available MCP tools."""
        if not self._initialized:
            self.initialize()
        resp = self._make_request("tools/list")
        return self._extract_result(resp)

    # ============ PROJECT MANAGEMENT ============

    def create_project(self, title=None):
        """Create a new Stitch project."""
        args = {}
        if title:
            args["title"] = title
        return self._call_tool("create_project", args)

    def get_project(self, project_name):
        """Get project details. project_name format: projects/{id}"""
        return self._call_tool("get_project", {"name": project_name})

    def list_projects(self, filter_type=None):
        """List all projects. filter: 'view=owned' (default) or 'view=shared'."""
        args = {}
        if filter_type:
            args["filter"] = filter_type
        return self._call_tool("list_projects", args)

    def delete_project(self, project_name):
        """Delete a project. project_name format: projects/{id}"""
        return self._call_tool("delete_project", {"name": project_name})

    # ============ SCREEN MANAGEMENT ============

    def list_screens(self, project_id):
        """List all screens in a project."""
        return self._call_tool("list_screens", {"projectId": project_id})

    def get_screen(self, project_id, screen_id):
        """
        Get screen details including HTML code and screenshot URLs.
        Returns Screen object with htmlCode, screenshot, figmaExport file references.
        """
        return self._call_tool("get_screen", {
            "name": f"projects/{project_id}/screens/{screen_id}",
            "projectId": project_id,
            "screenId": screen_id
        })

    # ============ AI GENERATION ============

    def generate_screen(self, project_id, prompt, device_type="DESKTOP", model="GEMINI_3_PRO"):
        """
        Generate a new screen from a text prompt.
        
        NOTE: This can take a few minutes. Connection errors don't mean failure.
        Use get_screen() to check status after a few minutes.
        
        Args:
            project_id: Project ID (without 'projects/' prefix)
            prompt: Text description of the screen to generate
            device_type: MOBILE, DESKTOP, TABLET, or AGNOSTIC
            model: GEMINI_3_PRO or GEMINI_3_FLASH
        """
        return self._call_tool("generate_screen_from_text", {
            "projectId": project_id,
            "prompt": prompt,
            "deviceType": device_type,
            "modelId": model
        })

    def edit_screens(self, project_id, screen_ids, prompt, device_type=None, model=None):
        """
        Edit existing screens with a text prompt.
        Same timing caveat as generate_screen.
        """
        args = {
            "projectId": project_id,
            "selectedScreenIds": screen_ids,
            "prompt": prompt
        }
        if device_type:
            args["deviceType"] = device_type
        if model:
            args["modelId"] = model
        return self._call_tool("edit_screens", args)

    def generate_variants(self, project_id, screen_ids, prompt, variant_count=3,
                          creative_range="EXPLORE", aspects=None):
        """
        Generate design variants of existing screens.
        
        Args:
            creative_range: REFINE, EXPLORE, or REIMAGINE
            aspects: list of LAYOUT, COLOR_SCHEME, IMAGES, TEXT_FONT, TEXT_CONTENT
        """
        variant_options = {
            "variantCount": variant_count,
            "creativeRange": creative_range
        }
        if aspects:
            variant_options["aspects"] = aspects

        return self._call_tool("generate_variants", {
            "projectId": project_id,
            "selectedScreenIds": screen_ids,
            "prompt": prompt,
            "variantOptions": variant_options
        })

    def upload_screens_from_images(self, project_id, images):
        """
        Upload images as new screens.
        images: list of {"fileContentBase64": "...", "mimeType": "image/png"}
        """
        return self._call_tool("upload_screens_from_images", {
            "projectId": project_id,
            "images": images
        })

    # ============ DESIGN SYSTEMS ============

    def create_design_system(self, design_system, project_id=None):
        """
        Create a new design system.
        
        design_system: {
            "displayName": "My Design System",
            "theme": {
                "colorMode": "DARK",        # LIGHT, DARK
                "font": "INTER",            # INTER, DM_SANS, GEIST, etc.
                "roundness": "ROUND_EIGHT", # ROUND_FOUR, ROUND_EIGHT, ROUND_TWELVE, ROUND_FULL
                "preset": "blue",           # preset color name
                "saturation": 3,            # 1-4
                "customColor": "#2563EB",   # hex color override
                "backgroundLight": "#FFFFFF",
                "backgroundDark": "#0F172A",
                "description": "..."
            },
            "styleGuidelines": "Freeform style text...",
            "designTokens": "DTCG format tokens..."
        }
        """
        args = {"designSystem": design_system}
        if project_id:
            args["projectId"] = project_id
        return self._call_tool("create_design_system", args)

    def update_design_system(self, asset_name, design_system):
        """Update an existing design system. asset_name format: assets/{id}"""
        return self._call_tool("update_design_system", {
            "designSystem": {
                "name": asset_name,
                "designSystem": design_system
            }
        })

    def list_design_systems(self):
        """List all design systems."""
        return self._call_tool("list_design_systems", {})

    def apply_design_system(self, project_id, asset_name):
        """Apply a design system to a project."""
        return self._call_tool("apply_design_system", {
            "projectId": project_id,
            "assetName": asset_name
        })

    # ============ HELPERS ============

    def download_file(self, url, output_path):
        """Download a file from a Stitch URL."""
        headers = {"X-Goog-Api-Key": self.api_key}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(resp.read())
        return output_path


# ============ CLI ============
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stitch MCP Client CLI")
    sub = parser.add_subparsers(dest="command")

    # list-projects
    sub.add_parser("list-projects", help="List Stitch projects")

    # list-screens
    ls = sub.add_parser("list-screens", help="List screens in a project")
    ls.add_argument("project_id", help="Project ID")

    # list-design-systems
    sub.add_parser("list-design-systems", help="List design systems")

    # create-project
    cp = sub.add_parser("create-project", help="Create a project")
    cp.add_argument("--title", "-t", help="Project title")

    # generate-screen
    gs = sub.add_parser("generate-screen", help="Generate a screen from text")
    gs.add_argument("project_id", help="Project ID")
    gs.add_argument("prompt", help="Text prompt")
    gs.add_argument("--device", "-d", default="DESKTOP", choices=["MOBILE", "DESKTOP", "TABLET", "AGNOSTIC"])
    gs.add_argument("--model", "-m", default="GEMINI_3_PRO", choices=["GEMINI_3_PRO", "GEMINI_3_FLASH"])

    # get-screen
    gsc = sub.add_parser("get-screen", help="Get screen details + code")
    gsc.add_argument("project_id", help="Project ID")
    gsc.add_argument("screen_id", help="Screen ID")

    # list-tools
    sub.add_parser("list-tools", help="List available MCP tools")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        client = StitchClient()

        if args.command == "list-tools":
            result = client.list_tools()
            print(json.dumps(result, indent=2))
        elif args.command == "list-projects":
            result = client.list_projects()
            print(json.dumps(result, indent=2))
        elif args.command == "list-screens":
            result = client.list_screens(args.project_id)
            print(json.dumps(result, indent=2))
        elif args.command == "list-design-systems":
            result = client.list_design_systems()
            print(json.dumps(result, indent=2))
        elif args.command == "create-project":
            result = client.create_project(args.title)
            print(json.dumps(result, indent=2))
        elif args.command == "generate-screen":
            print(f"Generating screen (this may take a few minutes)...")
            result = client.generate_screen(args.project_id, args.prompt, args.device, args.model)
            print(json.dumps(result, indent=2))
        elif args.command == "get-screen":
            result = client.get_screen(args.project_id, args.screen_id)
            print(json.dumps(result, indent=2))

    except StitchError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

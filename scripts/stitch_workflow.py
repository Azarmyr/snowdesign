#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stitch Workflow - Brief-driven design generation via Google Stitch MCP.

Primary workflow (brief-driven):
  python stitch_workflow.py --brief path/to/brief.md -p "Entima" --screens "landing,pricing"
  cat brief.md | python stitch_workflow.py -p "My App"

Reference fallback (BM25, for quick lookups without a brief):
  python stitch_workflow.py "fintech dashboard" -p "My App" --reference
  python stitch_workflow.py "fintech dashboard" -p "My App" --reference --screens "hero,pricing"

The brief IS the intelligence layer. Stitch/Gemini is the creative engine.
BM25 is only used in --reference mode as a quick fallback when no brief exists.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))

from stitch_client import StitchClient, StitchError


# ============ PRIMARY WORKFLOW: BRIEF-DRIVEN ============

def run_brief_workflow(brief, project_name, screens=None, device_type="DESKTOP",
                       model="GEMINI_3_PRO", output_dir=None, verbose=False):
    """
    Brief-driven Stitch workflow. The brief provides all creative direction.
    
    1. Read the design brief (brand context, visual direction, copy, screens)
    2. Create Stitch project
    3. Generate screens with the full brief injected as context
    4. Return project info, screen details, and download links
    
    Args:
        brief: Design brief text (the full creative context)
        project_name: Project name
        screens: List of screen prompts. If None, uses brief as single screen prompt.
        device_type: MOBILE, DESKTOP, TABLET, AGNOSTIC
        model: GEMINI_3_PRO or GEMINI_3_FLASH
        output_dir: Directory to save output files
        verbose: Print detailed progress
        
    Returns:
        dict with project info, screens, and file paths
    """
    project_name = project_name or "Design Project"
    output_dir = Path(output_dir) if output_dir else Path.cwd() / "stitch-output" / project_name.lower().replace(" ", "-")
    output_dir.mkdir(parents=True, exist_ok=True)

    log = lambda msg: print(msg) if verbose else None

    # Save brief for reference
    brief_path = output_dir / "design-brief.md"
    with open(brief_path, "w") as f:
        f.write(brief)
    log(f"\n[1/3] Design brief saved: {brief_path}")
    log(f"  Brief length: {len(brief)} chars")

    # ── Step 2: Create Project ──
    try:
        client = StitchClient()
    except StitchError as e:
        return _error_result(str(e), output_dir, brief)

    log("\n[2/3] Creating Stitch project...")
    try:
        project_result = client.create_project(project_name)
        project_id = _extract_project_id(project_result)
        log(f"  Project created: {project_id}")
    except StitchError as e:
        return _error_result(f"Failed to create project: {e}", output_dir, brief)

    # ── Step 3: Generate Screens ──
    log("\n[3/3] Generating screens...")
    if screens is None:
        # Use a summary prompt derived from the brief
        screens = [_brief_to_screen_prompt(brief)]

    generated_screens = []
    for i, screen_prompt in enumerate(screens, 1):
        # The brief provides all creative context - inject it fully
        enriched_prompt = f"""{screen_prompt}

--- DESIGN BRIEF (follow this creative direction) ---
{brief}
"""
        
        log(f"  [{i}/{len(screens)}] Generating: {screen_prompt[:60]}...")
        log(f"  (This may take 1-3 minutes per screen)")
        try:
            screen_result = client.generate_screen(
                project_id, enriched_prompt,
                device_type=device_type,
                model=model
            )
            screen_info = _extract_screen_info(screen_result)
            screen_info["prompt"] = screen_prompt
            generated_screens.append(screen_info)
            log(f"  Screen generated: {screen_info.get('screen_id', 'unknown')}")
        except StitchError as e:
            log(f"  Error generating screen: {e}")
            generated_screens.append({
                "prompt": screen_prompt,
                "error": str(e)
            })

    # ── Save Results ──
    result = {
        "status": "success",
        "project_name": project_name,
        "project_id": project_id,
        "screens": generated_screens,
        "output_dir": str(output_dir),
        "stitch_url": f"https://stitch.withgoogle.com/project/{project_id}",
        "next_steps": [
            f"View designs: https://stitch.withgoogle.com/project/{project_id}",
            f"Get screen code: python stitch_client.py get-screen {project_id} <screen_id>",
            f"Edit screen: Use edit_screens to refine with text prompts",
            f"Generate variants: Use generate_variants for alternatives",
        ]
    }

    result_path = output_dir / "stitch-result.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    log(f"\n  Full result saved: {result_path}")

    return result


def _brief_to_screen_prompt(brief):
    """
    Extract a usable screen generation prompt from a full brief.
    Looks for the SCREENS section, falls back to first 500 chars.
    """
    lines = brief.split("\n")
    
    # Try to find a "Screens to Generate" or similar section
    screen_section_start = None
    for i, line in enumerate(lines):
        lower = line.lower().strip()
        if any(kw in lower for kw in ["screens to generate", "screens needed", "screen name", "## 7."]):
            screen_section_start = i
            break
    
    if screen_section_start is not None:
        # Extract the first screen description
        section_lines = lines[screen_section_start:screen_section_start + 20]
        return "\n".join(section_lines)
    
    # Fallback: use brief summary
    return f"Generate the primary landing page based on this design brief:\n{brief[:1000]}"


# ============ REFERENCE FALLBACK: BM25-DRIVEN ============

def run_reference_workflow(query, project_name=None, screens=None, device_type="DESKTOP",
                           model="GEMINI_3_PRO", output_dir=None, verbose=False):
    """
    BM25 reference fallback for when no brief is available.
    Quick and dirty: keyword match against CSV data, inject into Stitch.
    
    Use --reference flag. For real projects, use a brief instead.
    """
    from design_system import DesignSystemGenerator

    project_name = project_name or query.title()
    output_dir = Path(output_dir) if output_dir else Path.cwd() / "stitch-output" / project_name.lower().replace(" ", "-")
    output_dir.mkdir(parents=True, exist_ok=True)

    log = lambda msg: print(msg) if verbose else None

    # BM25 lookup
    log("\n[1/3] Running BM25 reference lookup...")
    generator = DesignSystemGenerator()
    bm25_ds = generator.generate(query, project_name)

    bm25_path = output_dir / "reference-bm25.json"
    with open(bm25_path, "w") as f:
        json.dump(bm25_ds, f, indent=2)
    log(f"  Reference saved: {bm25_path}")
    log(f"  Category: {bm25_ds.get('category')}")
    log(f"  Style: {bm25_ds.get('style', {}).get('name')}")

    # Build a minimal context string from BM25 output
    design_context = _bm25_to_context(bm25_ds)

    try:
        client = StitchClient()
    except StitchError as e:
        return _error_result(str(e), output_dir)

    # Create project
    log("\n[2/3] Creating Stitch project...")
    try:
        project_result = client.create_project(project_name)
        project_id = _extract_project_id(project_result)
        log(f"  Project created: {project_id}")
    except StitchError as e:
        return _error_result(f"Failed to create project: {e}", output_dir)

    # Generate screens
    log("\n[3/3] Generating screens...")
    if screens is None:
        screens = [query]

    generated_screens = []
    for i, screen_prompt in enumerate(screens, 1):
        enriched_prompt = f"{screen_prompt}\n\nDesign reference:\n{design_context}"
        
        log(f"  [{i}/{len(screens)}] Generating: {screen_prompt[:60]}...")
        try:
            screen_result = client.generate_screen(
                project_id, enriched_prompt,
                device_type=device_type,
                model=model
            )
            screen_info = _extract_screen_info(screen_result)
            screen_info["prompt"] = screen_prompt
            generated_screens.append(screen_info)
            log(f"  Screen generated: {screen_info.get('screen_id', 'unknown')}")
        except StitchError as e:
            log(f"  Error generating screen: {e}")
            generated_screens.append({"prompt": screen_prompt, "error": str(e)})

    result = {
        "status": "success",
        "mode": "reference (BM25 fallback)",
        "project_name": project_name,
        "project_id": project_id,
        "bm25_reference": bm25_ds,
        "screens": generated_screens,
        "output_dir": str(output_dir),
        "stitch_url": f"https://stitch.withgoogle.com/project/{project_id}",
        "next_steps": [
            f"View designs: https://stitch.withgoogle.com/project/{project_id}",
            "NOTE: This used BM25 reference mode. For better results, use a design brief.",
        ]
    }

    result_path = output_dir / "stitch-result.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    log(f"\n  Full result saved: {result_path}")

    return result


def _bm25_to_context(bm25_ds):
    """Build a minimal context string from BM25 output for reference mode."""
    colors = bm25_ds.get("colors", {})
    typography = bm25_ds.get("typography", {})
    style = bm25_ds.get("style", {})
    pattern = bm25_ds.get("pattern", {})
    effects = bm25_ds.get("key_effects", "")

    parts = []
    parts.append(f"Style: {style.get('name', 'Modern')} - {style.get('keywords', '')}")
    parts.append(f"Colors: primary {colors.get('primary', '#2563EB')}, secondary {colors.get('secondary', '#3B82F6')}, CTA {colors.get('cta', '#F97316')}, background {colors.get('background', '#F8FAFC')}, text {colors.get('text', '#1E293B')}")
    parts.append(f"Typography: heading font {typography.get('heading', 'Inter')}, body font {typography.get('body', 'Inter')}")
    if effects:
        parts.append(f"Effects: {effects}")
    if pattern.get("sections"):
        parts.append(f"Layout: {pattern.get('sections', '')}")

    return "\n".join(parts)


# ============ HELPERS ============

def _extract_project_id(result):
    """Extract project ID from create_project response."""
    if isinstance(result, dict):
        content = result.get("content", [])
        for item in content:
            if isinstance(item, dict) and "text" in item:
                try:
                    data = json.loads(item["text"])
                    name = data.get("name", "")
                    if "/" in name:
                        return name.split("/")[-1]
                    return name
                except (json.JSONDecodeError, TypeError):
                    pass
        name = result.get("name", "")
        if "/" in name:
            return name.split("/")[-1]
        return name
    return ""


def _extract_screen_info(result):
    """Extract screen info from generate_screen response."""
    info = {"screen_id": "", "title": "", "html_url": "", "screenshot_url": "", "width": "", "height": ""}

    if not isinstance(result, dict):
        return info

    # Try structuredContent first
    structured = result.get("structuredContent", {})
    output_components = structured.get("outputComponents", [])

    # Fallback: parse from content[].text JSON
    if not output_components:
        for item in result.get("content", []):
            if isinstance(item, dict) and "text" in item:
                try:
                    data = json.loads(item["text"])
                    output_components = data.get("outputComponents", [])
                    if output_components:
                        break
                except (json.JSONDecodeError, TypeError):
                    continue

    # Extract from outputComponents -> design -> screens[]
    for comp in output_components:
        if not isinstance(comp, dict):
            continue
        design = comp.get("design", {})
        screens = design.get("screens", [])
        for screen in screens:
            if not isinstance(screen, dict):
                continue
            name = screen.get("name", "")
            if "/" in name:
                info["screen_id"] = name.split("/")[-1]
            elif screen.get("id"):
                info["screen_id"] = screen["id"]

            info["title"] = screen.get("title", "")
            info["width"] = screen.get("width", "")
            info["height"] = screen.get("height", "")

            html_code = screen.get("htmlCode", {})
            if isinstance(html_code, dict):
                info["html_url"] = html_code.get("downloadUrl", "")

            screenshot = screen.get("screenshot", {})
            if isinstance(screenshot, dict):
                info["screenshot_url"] = screenshot.get("downloadUrl", "")

            if info["screen_id"]:
                return info

    return info


def _error_result(message, output_dir, brief=None):
    """Return error result."""
    result = {
        "status": "error",
        "error": message,
        "output_dir": str(output_dir),
    }
    if brief:
        result["note"] = "Design brief is saved in output_dir/design-brief.md. You can retry or use it manually."
    return result


# ============ OUTPUT ============

def format_workflow_result(result):
    """Format workflow result for terminal display."""
    lines = []
    
    if result["status"] == "error":
        lines.append("=" * 70)
        lines.append("  SNOWDESIGN + STITCH - ERROR")
        lines.append("=" * 70)
        lines.append(f"  Error: {result['error']}")
        lines.append(f"  Output dir: {result.get('output_dir', '?')}")
        lines.append("=" * 70)
        return "\n".join(lines)

    mode = result.get("mode", "brief-driven")
    lines.append("")
    lines.append("=" * 70)
    lines.append(f"  SNOWDESIGN + STITCH - {result['project_name']}")
    lines.append(f"  Mode: {mode}")
    lines.append("=" * 70)
    lines.append("")

    lines.append(f"  Stitch Project:  {result.get('project_id', '?')}")
    lines.append(f"  View Online:     {result.get('stitch_url', '?')}")
    lines.append("")

    screens = result.get("screens", [])
    if screens:
        lines.append(f"  Screens Generated: {len(screens)}")
        for i, screen in enumerate(screens, 1):
            if screen.get("error"):
                lines.append(f"    {i}. [ERROR] {screen['prompt'][:50]}: {screen['error']}")
            else:
                lines.append(f"    {i}. {screen.get('title', screen['prompt'][:50])}")
                lines.append(f"       ID: {screen.get('screen_id', '?')}")
        lines.append("")

    lines.append("  Next Steps:")
    for step in result.get("next_steps", []):
        lines.append(f"    - {step}")
    lines.append("")
    lines.append(f"  Output: {result.get('output_dir', '?')}")
    lines.append("=" * 70)

    return "\n".join(lines)


# ============ CLI ============

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Snowdesign + Stitch: Design brief -> Stitch visual generation"
    )
    parser.add_argument("query", nargs="?", default=None,
                        help="Design query (only used in --reference mode)")
    parser.add_argument("--brief", "-b", type=str, default=None,
                        help="Path to design brief file (primary workflow)")
    parser.add_argument("--project-name", "-p", help="Project name")
    parser.add_argument("--screens", "-s", help="Comma-separated screen prompts")
    parser.add_argument("--device", "-d", default="DESKTOP",
                        choices=["MOBILE", "DESKTOP", "TABLET", "AGNOSTIC"])
    parser.add_argument("--model", "-m", default="GEMINI_3_PRO",
                        choices=["GEMINI_3_PRO", "GEMINI_3_FLASH"])
    parser.add_argument("--output-dir", "-o", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--reference", "-r", action="store_true",
                        help="Use BM25 reference mode (fallback, no brief needed)")

    args = parser.parse_args()

    screens = None
    if args.screens:
        screens = [s.strip() for s in args.screens.split(",")]

    # Brief-driven workflow (primary)
    if args.brief or not args.reference:
        brief_text = None
        
        if args.brief:
            # Read from file
            brief_path = Path(args.brief)
            if not brief_path.exists():
                print(f"Error: Brief file not found: {args.brief}", file=sys.stderr)
                sys.exit(1)
            brief_text = brief_path.read_text(encoding="utf-8")
        elif not sys.stdin.isatty():
            # Read from stdin
            brief_text = sys.stdin.read()
        
        if brief_text:
            result = run_brief_workflow(
                brief=brief_text,
                project_name=args.project_name,
                screens=screens,
                device_type=args.device,
                model=args.model,
                output_dir=args.output_dir,
                verbose=args.verbose
            )
        else:
            print("Error: No brief provided. Use --brief <file>, pipe via stdin, or use --reference mode.", file=sys.stderr)
            print("\nUsage:", file=sys.stderr)
            print("  python stitch_workflow.py --brief design-brief.md -p 'My App'", file=sys.stderr)
            print("  cat brief.md | python stitch_workflow.py -p 'My App'", file=sys.stderr)
            print("  python stitch_workflow.py 'fintech dashboard' -p 'My App' --reference", file=sys.stderr)
            sys.exit(1)
    
    # Reference fallback (BM25)
    elif args.reference:
        if not args.query:
            print("Error: --reference mode requires a query argument.", file=sys.stderr)
            sys.exit(1)
        result = run_reference_workflow(
            query=args.query,
            project_name=args.project_name,
            screens=screens,
            device_type=args.device,
            model=args.model,
            output_dir=args.output_dir,
            verbose=args.verbose
        )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(format_workflow_result(result))

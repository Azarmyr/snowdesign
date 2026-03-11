#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snowdesign Reference Library - BM25 search for design inspiration and lookups.

This is a REFERENCE tool, not the main pipeline. Use it to browse:
  - 67 visual styles
  - 96 color palettes  
  - 57 font pairings
  - 100 industry patterns
  - Landing page layouts
  - Framework-specific guidelines

Usage:
  python search.py "glassmorphism" --domain style       # Look up a style
  python search.py "luxury warm" --domain color          # Browse palettes
  python search.py "editorial serif" --domain typography  # Font pairings
  python search.py "SaaS" --domain landing               # Page patterns
  python search.py "nextjs" --stack nextjs               # Framework guidelines
  python search.py "fintech" --reference -p "My App"     # Full BM25 reference sheet

For the main design pipeline, use stitch_workflow.py with a design brief.
"""

import argparse
import sys
import io
from core import CSV_CONFIG, AVAILABLE_STACKS, MAX_RESULTS, search, search_stack
from design_system import generate_design_system

# Force UTF-8 for stdout/stderr
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def format_output(result):
    """Format results for Claude consumption (token-optimized)"""
    if "error" in result:
        return f"Error: {result['error']}"

    output = []
    if result.get("stack"):
        output.append(f"## Snowdesign Reference - Stack Guidelines")
        output.append(f"**Stack:** {result['stack']} | **Query:** {result['query']}")
    else:
        output.append(f"## Snowdesign Reference - {result['domain'].title()}")
        output.append(f"**Domain:** {result['domain']} | **Query:** {result['query']}")
    output.append(f"**Source:** {result['file']} | **Found:** {result['count']} results\n")

    for i, row in enumerate(result['results'], 1):
        output.append(f"### Result {i}")
        for key, value in row.items():
            value_str = str(value)
            if len(value_str) > 300:
                value_str = value_str[:300] + "..."
            output.append(f"- **{key}:** {value_str}")
        output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Snowdesign Reference Library - browse styles, colors, fonts, patterns"
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()),
                        help="Search domain (style, color, typography, landing, product, ux, chart, icons)")
    parser.add_argument("--stack", "-s", choices=AVAILABLE_STACKS,
                        help="Stack-specific guidelines (html-tailwind, react, nextjs)")
    parser.add_argument("--max-results", "-n", type=int, default=MAX_RESULTS,
                        help="Max results (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Reference sheet (BM25 aggregate - for inspiration, not pipeline)
    parser.add_argument("--reference", "-r", action="store_true",
                        help="Generate full BM25 reference sheet (style + colors + fonts + patterns)")
    parser.add_argument("--design-system", "-ds", action="store_true",
                        help="Alias for --reference (legacy)")
    parser.add_argument("--project-name", "-p", type=str, default=None,
                        help="Project name for reference output")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii",
                        help="Output format for reference sheet")
    
    # Persistence
    parser.add_argument("--persist", action="store_true",
                        help="Save reference sheet to design-system/ directory")
    parser.add_argument("--page", type=str, default=None,
                        help="Create page-specific override file")
    parser.add_argument("--output-dir", "-o", type=str, default=None,
                        help="Output directory for persisted files")

    args = parser.parse_args()

    # --design-system is alias for --reference (backward compat)
    if args.design_system:
        args.reference = True

    # Reference sheet mode
    if args.reference:
        result = generate_design_system(
            args.query, 
            args.project_name, 
            args.format,
            persist=args.persist,
            page=args.page,
            output_dir=args.output_dir
        )
        print(result)
        
        if args.persist:
            project_slug = args.project_name.lower().replace(' ', '-') if args.project_name else "default"
            print("\n" + "=" * 60)
            print(f"  Reference sheet saved to design-system/{project_slug}/")
            print(f"  This is for INSPIRATION, not constraints.")
            print("=" * 60)
    
    # Stack guidelines
    elif args.stack:
        result = search_stack(args.query, args.stack, args.max_results)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
    
    # Domain lookup
    else:
        result = search(args.query, args.domain, args.max_results)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))

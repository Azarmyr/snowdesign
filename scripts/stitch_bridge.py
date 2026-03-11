#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stitch Bridge - Converts snowdesign's BM25 intelligence into Stitch MCP parameters.

Bridges the gap between snowdesign's design reasoning engine and Google Stitch's
visual design generation API.

Usage:
    # Generate Stitch-ready design system JSON
    python3 stitch_bridge.py "fintech dashboard" -p "My App"
    
    # Generate design system + screen prompt
    python3 stitch_bridge.py "fintech dashboard" -p "My App" --screen "A modern dashboard with real-time metrics"
    
    # Output as MCP tool call format
    python3 stitch_bridge.py "fintech dashboard" -p "My App" --mcp
    
    # Full pipeline: design system + all screen prompts
    python3 stitch_bridge.py "fintech dashboard" -p "My App" --full-pipeline
"""

import argparse
import json
import sys
import io
from pathlib import Path

# Force UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from core import search
from design_system import DesignSystemGenerator


# ============ FONT MAPPING ============
# Maps snowdesign font names to Stitch FONT enum values
STITCH_FONT_MAP = {
    "inter": "INTER",
    "dm sans": "DM_SANS",
    "geist": "GEIST",
    "roboto": "INTER",        # closest match
    "open sans": "DM_SANS",   # closest match
    "poppins": "DM_SANS",     # closest match
    "montserrat": "INTER",    # closest match
    "lato": "DM_SANS",        # closest match
    "source sans": "DM_SANS",
    "nunito": "DM_SANS",
    "raleway": "INTER",
    "work sans": "DM_SANS",
    "space grotesk": "GEIST",
    "jetbrains mono": "GEIST",
    "fira code": "GEIST",
    "ibm plex": "GEIST",
}

# Maps color moods to Stitch preset names
STITCH_PRESET_MAP = {
    "professional": "blue",
    "trust": "blue",
    "calm": "blue",
    "energy": "orange",
    "creative": "purple",
    "growth": "green",
    "luxury": "purple",
    "warm": "orange",
    "cool": "blue",
    "bold": "red",
    "minimal": "gray",
    "tech": "blue",
    "finance": "green",
    "health": "green",
    "entertainment": "purple",
    "food": "orange",
    "travel": "blue",
    "education": "blue",
    "social": "purple",
}

# Color roundness inference from style
ROUNDNESS_MAP = {
    "brutalism": "ROUND_FOUR",
    "minimalism": "ROUND_EIGHT",
    "glassmorphism": "ROUND_TWELVE",
    "neumorphism": "ROUND_TWELVE",
    "flat design": "ROUND_EIGHT",
    "material design": "ROUND_EIGHT",
    "skeuomorphism": "ROUND_TWELVE",
    "aurora": "ROUND_FULL",
    "gradient": "ROUND_TWELVE",
    "retro": "ROUND_FOUR",
    "pixel": "ROUND_FOUR",
    "organic": "ROUND_FULL",
    "geometric": "ROUND_FOUR",
}


def _infer_stitch_font(font_name: str) -> str:
    """Map a font name to the closest Stitch FONT enum."""
    if not font_name:
        return "INTER"
    font_lower = font_name.lower().strip()
    for key, value in STITCH_FONT_MAP.items():
        if key in font_lower:
            return value
    return "INTER"


def _infer_stitch_preset(color_mood: str, primary_hex: str) -> str:
    """Infer Stitch color preset from mood or primary hex."""
    if color_mood:
        mood_lower = color_mood.lower()
        for key, value in STITCH_PRESET_MAP.items():
            if key in mood_lower:
                return value
    
    # Fallback: infer from primary hex hue
    if primary_hex and primary_hex.startswith("#") and len(primary_hex) == 7:
        try:
            r = int(primary_hex[1:3], 16)
            g = int(primary_hex[3:5], 16)
            b = int(primary_hex[5:7], 16)
            if b > r and b > g:
                return "blue"
            elif g > r and g > b:
                return "green"
            elif r > g and r > b:
                if g > 100:
                    return "orange"
                return "red"
        except ValueError:
            pass
    
    return "blue"


def _infer_roundness(style_name: str) -> str:
    """Infer roundness from style name."""
    if not style_name:
        return "ROUND_EIGHT"
    style_lower = style_name.lower()
    for key, value in ROUNDNESS_MAP.items():
        if key in style_lower:
            return value
    return "ROUND_EIGHT"


def _infer_color_mode(query: str, style_name: str) -> str:
    """Infer light/dark mode from query and style."""
    combined = f"{query} {style_name}".lower()
    dark_keywords = ["dark", "night", "midnight", "noir", "shadow", "neon", "cyber", "hacker"]
    if any(kw in combined for kw in dark_keywords):
        return "DARK"
    return "LIGHT"


def snowdesign_to_stitch_design_system(design_system: dict, query: str = "") -> dict:
    """
    Convert snowdesign's design system output to Stitch create_design_system parameters.
    
    Returns a dict ready to pass as Stitch MCP tool input.
    """
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    style = design_system.get("style", {})
    pattern = design_system.get("pattern", {})
    effects = design_system.get("key_effects", "")
    anti_patterns = design_system.get("anti_patterns", "")
    
    style_name = style.get("name", "")
    heading_font = typography.get("heading", "Inter")
    
    # Build DesignTheme
    theme = {
        "colorMode": _infer_color_mode(query, style_name),
        "font": _infer_stitch_font(heading_font),
        "roundness": _infer_roundness(style_name),
        "preset": _infer_stitch_preset(
            design_system.get("category", ""),
            colors.get("primary", "")
        ),
    }
    
    # Add custom color if we have a primary
    primary = colors.get("primary", "")
    if primary and primary.startswith("#"):
        theme["customColor"] = primary
    
    # Add background overrides
    bg = colors.get("background", "")
    if bg and bg.startswith("#"):
        if theme["colorMode"] == "DARK":
            theme["backgroundDark"] = bg
        else:
            theme["backgroundLight"] = bg
    
    # Build style guidelines text (snowdesign's unique value-add)
    guidelines = []
    guidelines.append(f"Style: {style_name}")
    if style.get("keywords"):
        guidelines.append(f"Keywords: {style['keywords']}")
    if effects:
        guidelines.append(f"Effects: {effects}")
    if pattern.get("sections"):
        guidelines.append(f"Section Order: {pattern['sections']}")
    if pattern.get("conversion"):
        guidelines.append(f"Conversion: {pattern['conversion']}")
    if anti_patterns:
        guidelines.append(f"AVOID: {anti_patterns}")
    guidelines.append("MUST: cursor-pointer on clickable elements, smooth transitions 150-300ms, 4.5:1 contrast ratio")
    guidelines.append("ICONS: Use SVG icons only (Heroicons/Lucide). Never use emojis as icons.")
    
    # Build design tokens in DTCG format
    tokens = {
        "color": {
            "primary": {"$value": colors.get("primary", "#2563EB"), "$type": "color"},
            "secondary": {"$value": colors.get("secondary", "#3B82F6"), "$type": "color"},
            "cta": {"$value": colors.get("cta", "#F97316"), "$type": "color"},
            "background": {"$value": colors.get("background", "#F8FAFC"), "$type": "color"},
            "text": {"$value": colors.get("text", "#1E293B"), "$type": "color"},
        },
        "typography": {
            "heading": {"$value": heading_font, "$type": "fontFamily"},
            "body": {"$value": typography.get("body", "Inter"), "$type": "fontFamily"},
        },
        "spacing": {
            "xs": {"$value": "4px", "$type": "dimension"},
            "sm": {"$value": "8px", "$type": "dimension"},
            "md": {"$value": "16px", "$type": "dimension"},
            "lg": {"$value": "24px", "$type": "dimension"},
            "xl": {"$value": "32px", "$type": "dimension"},
        }
    }
    
    return {
        "designSystem": {
            "displayName": design_system.get("project_name", "Design System"),
            "theme": theme,
            "designTokens": json.dumps(tokens),
            "styleGuidelines": "\n".join(guidelines),
        }
    }


def generate_screen_prompt(design_system: dict, screen_description: str, device: str = "DESKTOP") -> dict:
    """
    Generate a Stitch generate_screen_from_text prompt enriched with snowdesign intelligence.
    
    Returns a dict with the enriched prompt and device type.
    """
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    style = design_system.get("style", {})
    pattern = design_system.get("pattern", {})
    effects = design_system.get("key_effects", "")
    anti_patterns = design_system.get("anti_patterns", "")
    
    # Build enriched prompt
    prompt_parts = []
    prompt_parts.append(screen_description)
    prompt_parts.append("")
    prompt_parts.append("Design constraints:")
    prompt_parts.append(f"- Style: {style.get('name', 'Minimalism')}")
    prompt_parts.append(f"- Colors: primary {colors.get('primary', '#2563EB')}, secondary {colors.get('secondary', '#3B82F6')}, CTA {colors.get('cta', '#F97316')}, background {colors.get('background', '#F8FAFC')}, text {colors.get('text', '#1E293B')}")
    prompt_parts.append(f"- Typography: {typography.get('heading', 'Inter')} for headings, {typography.get('body', 'Inter')} for body")
    
    if effects:
        prompt_parts.append(f"- Effects: {effects}")
    if anti_patterns:
        prompt_parts.append(f"- AVOID: {anti_patterns}")
    
    prompt_parts.append("- Use SVG icons, not emojis. All clickable elements need cursor:pointer. Smooth transitions 150-300ms.")
    
    if pattern.get("sections"):
        prompt_parts.append(f"- Layout sections: {pattern['sections']}")
    
    return {
        "prompt": "\n".join(prompt_parts),
        "deviceType": device,
        "modelId": "GEMINI_3_PRO"
    }


def generate_full_pipeline(query: str, project_name: str, screens: list = None, device: str = "DESKTOP") -> dict:
    """
    Generate the full Stitch pipeline: design system + screen prompts.
    
    Returns a dict with all the MCP tool calls needed.
    """
    generator = DesignSystemGenerator()
    ds = generator.generate(query, project_name)
    
    # Step 1: Create project
    create_project = {
        "tool": "create_project",
        "input": {"title": project_name or query.title()}
    }
    
    # Step 2: Create design system
    stitch_ds = snowdesign_to_stitch_design_system(ds, query)
    create_ds = {
        "tool": "create_design_system",
        "input": stitch_ds
    }
    
    # Step 3: Generate screens
    screen_prompts = []
    if screens:
        for screen_desc in screens:
            sp = generate_screen_prompt(ds, screen_desc, device)
            screen_prompts.append({
                "tool": "generate_screen_from_text",
                "input": sp
            })
    else:
        # Default: generate based on pattern sections
        sections = ds.get("pattern", {}).get("sections", "Hero > Features > CTA")
        section_list = [s.strip() for s in sections.split(">") if s.strip()]
        
        # Generate a single screen with all sections
        full_desc = f"A {ds.get('style', {}).get('name', 'modern')} {query} page with sections: {', '.join(section_list)}"
        sp = generate_screen_prompt(ds, full_desc, device)
        screen_prompts.append({
            "tool": "generate_screen_from_text",
            "input": sp
        })
    
    return {
        "project_name": project_name or query.title(),
        "snowdesign_intelligence": {
            "category": ds.get("category", "General"),
            "style": ds.get("style", {}).get("name", ""),
            "pattern": ds.get("pattern", {}).get("name", ""),
            "anti_patterns": ds.get("anti_patterns", ""),
            "severity": ds.get("severity", "MEDIUM"),
        },
        "pipeline": [
            {"step": 1, "description": "Create Stitch project", **create_project},
            {"step": 2, "description": "Create design system with snowdesign intelligence", **create_ds},
            *[{"step": i+3, "description": f"Generate screen {i+1}", **sp} for i, sp in enumerate(screen_prompts)]
        ],
        "post_generation": {
            "step": len(screen_prompts) + 3,
            "description": "Get screen code and convert to target framework",
            "tools": ["get_screen (to download HTML/CSS)", "list_screens (to see all generated screens)"],
            "notes": "Use the HTML as foundation. Convert to React/Vue/Svelte using the agent's code capabilities."
        },
        "checklist": [
            "No emojis as icons (use SVG: Heroicons/Lucide)",
            "cursor-pointer on all clickable elements",
            "Hover states with smooth transitions (150-300ms)",
            "Text contrast 4.5:1 minimum",
            "Focus states visible for keyboard nav",
            "prefers-reduced-motion respected",
            "Responsive: 375px, 768px, 1024px, 1440px"
        ]
    }


# ============ CLI ============
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stitch Bridge - snowdesign to Stitch MCP")
    parser.add_argument("query", help="Design query (e.g., 'fintech dashboard')")
    parser.add_argument("-p", "--project-name", type=str, default=None, help="Project name")
    parser.add_argument("--screen", type=str, default=None, help="Screen description for prompt generation")
    parser.add_argument("--screens", type=str, nargs="+", help="Multiple screen descriptions")
    parser.add_argument("--device", choices=["DESKTOP", "MOBILE", "TABLET"], default="DESKTOP")
    parser.add_argument("--mcp", action="store_true", help="Output as MCP tool call format")
    parser.add_argument("--full-pipeline", action="store_true", help="Generate complete pipeline")
    parser.add_argument("--design-system-only", action="store_true", help="Only output Stitch design system params")
    
    args = parser.parse_args()
    
    if args.full_pipeline:
        screens = args.screens or ([args.screen] if args.screen else None)
        result = generate_full_pipeline(args.query, args.project_name, screens, args.device)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.design_system_only or (not args.screen and not args.mcp):
        generator = DesignSystemGenerator()
        ds = generator.generate(args.query, args.project_name)
        stitch_ds = snowdesign_to_stitch_design_system(ds, args.query)
        print(json.dumps(stitch_ds, indent=2, ensure_ascii=False))
    
    elif args.screen:
        generator = DesignSystemGenerator()
        ds = generator.generate(args.query, args.project_name)
        
        if args.mcp:
            # Output both design system and screen prompt
            stitch_ds = snowdesign_to_stitch_design_system(ds, args.query)
            screen_prompt = generate_screen_prompt(ds, args.screen, args.device)
            print(json.dumps({
                "create_design_system": stitch_ds,
                "generate_screen_from_text": screen_prompt
            }, indent=2, ensure_ascii=False))
        else:
            screen_prompt = generate_screen_prompt(ds, args.screen, args.device)
            print(json.dumps(screen_prompt, indent=2, ensure_ascii=False))

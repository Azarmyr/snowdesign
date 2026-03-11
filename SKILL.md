---
name: snowdesign
description: Design-to-code pipeline powered by Google Stitch MCP. Takes a design brief (brand context, visual direction, real copy) and generates pixel-perfect screens with HTML/CSS/Tailwind code. Includes a reference library of 67 styles, 96 palettes, 57 font pairings for inspiration. Use when asked for "snowdesign", "design system for X", "use snowdesign", "pro design", or when building serious/production UI. NOT for quick prototypes - use frontend-design skill for those.
metadata: {"clawdbot":{"emoji":"🐺"}}
---

# Snowdesign

Brief-driven design-to-code pipeline. Your design brief is the intelligence layer. Stitch/Gemini is the creative engine.

**When to use:** Serious projects, landing pages, dashboards, production UIs. Not for quick mockups.

## Architecture

```
Design Brief (human/agent intelligence)
  -> Google Stitch MCP (creative generation via Gemini)
  -> Download HTML/CSS + screenshots
  -> Optional: React component generation (21st.dev Magic MCP)

Reference Library (optional, on-demand)
  -> 67 styles, 96 palettes, 57 font pairings, 100 industry patterns
  -> Use for INSPIRATION, not constraints
```

The brief IS the brain. It carries brand voice, visual direction, real copy, screen specs. The more context in the brief, the better Stitch generates.

## Main Workflow: Brief -> Stitch

### Step 1: Generate a Design Brief

If you already have project/brand knowledge, use `DESIGN_BRIEF_PROMPT.md` to extract it into a structured brief. The prompt covers:
- Product identity and audience
- Brand personality and emotional tone
- Visual direction (mode, density, shape, references)
- Color and typography preferences
- Every screen needed with real copy and content
- Competitive context and technical constraints

```bash
# Brief lives as a file
cat <skill_dir>/DESIGN_BRIEF_PROMPT.md  # Read the extraction prompt
```

For agent-to-agent handoff: give the prompt to whatever agent has project context. Its output becomes the Stitch input.

### Step 2: Generate Screens via Stitch

```bash
# From a brief file
python3 <skill_dir>/scripts/stitch_workflow.py --brief path/to/brief.md -p "Entima"

# With specific screens
python3 <skill_dir>/scripts/stitch_workflow.py --brief brief.md -p "Entima" \
  --screens "landing hero,pricing page,onboarding step 1"

# Mobile + faster model
python3 <skill_dir>/scripts/stitch_workflow.py --brief brief.md -p "App" \
  --device MOBILE --model GEMINI_3_FLASH

# From stdin (pipe from another command)
cat brief.md | python3 <skill_dir>/scripts/stitch_workflow.py -p "My App"
```

**What happens:**
1. Brief is saved to output directory for reference
2. Stitch project is created
3. Each screen is generated with the full brief as creative context
4. Gemini AI interprets the brief and generates HTML/CSS/Tailwind
5. Returns project URL, screen IDs, download links

### Step 3: Download Designs

After generation, download HTML and screenshots:

```bash
# Get screen metadata
python3 <skill_dir>/scripts/stitch_client.py get-screen <project-id> <screen-id>

# Download files
bash <skill_dir>/scripts/fetch-stitch.sh "<html-download-url>" ".stitch/designs/page.html"
bash <skill_dir>/scripts/fetch-stitch.sh "<screenshot-url>=w<width>" ".stitch/designs/page.png"
```

Note: Append `=w{width}` to screenshot URL - Google CDN serves low-res thumbnails by default.

### Step 4: React Components (Optional - 21st.dev Magic)

Use 21st.dev Magic MCP to generate individual React components from the Stitch design:

1. Review the downloaded Stitch HTML/screenshot
2. Identify individual components (navbar, hero, cards, tables, etc.)
3. For each component, prompt 21st.dev Magic with the Stitch design as reference
4. Wire components together in your app

API key: `~/secrets/21st-dev.env` as `API_KEY_21ST`

### Step 5: Quality Gate

Before delivery, verify against `resources/architecture-checklist.md`:

- [ ] No hardcoded hex values - use Tailwind theme classes
- [ ] Props use `Readonly<T>` TypeScript interfaces
- [ ] Dark mode classes applied
- [ ] Responsive at 375px, 768px, 1024px, 1440px
- [ ] Focus states visible, `prefers-reduced-motion` respected

## Reference Library (Optional)

For inspiration and lookups. NOT part of the main pipeline.

```bash
# Browse styles
python3 <skill_dir>/scripts/search.py "glassmorphism" --domain style

# Browse color palettes
python3 <skill_dir>/scripts/search.py "luxury warm" --domain color

# Browse font pairings
python3 <skill_dir>/scripts/search.py "editorial serif" --domain typography

# Browse landing page patterns
python3 <skill_dir>/scripts/search.py "SaaS" --domain landing

# Framework-specific guidelines
python3 <skill_dir>/scripts/search.py "performance" --stack nextjs

# Full reference sheet (aggregated BM25 lookup)
python3 <skill_dir>/scripts/search.py "fintech dashboard" --reference -p "My App"
```

Domains: `style`, `color`, `typography`, `landing`, `product`, `ux`, `chart`, `icons`
Stacks: `html-tailwind`, `react`, `nextjs`, `vue`, `nuxtjs`, `nuxt-ui`, `svelte`, `astro`, `shadcn`, `swiftui`, `react-native`, `flutter`, `jetpack-compose`

### Quick Reference Fallback (no brief)

When you don't have a brief and just need a quick design:

```bash
python3 <skill_dir>/scripts/stitch_workflow.py "fintech dashboard" -p "Quick App" --reference
```

This uses BM25 to generate design specs from keywords. Fast but generic - use a brief for real projects.

## Stitch MCP Tools

| Tool | What it does |
|------|-------------|
| `create_project` | Create design project container |
| `list_projects` | List all projects |
| `get_screen` | Get screen HTML code + screenshot URLs |
| `generate_screen_from_text` | Generate screen from text (1-3 min) |
| `edit_screens` | Edit existing screens with text prompt |
| `generate_variants` | Generate variants (REFINE/EXPLORE/REIMAGINE) |

## File Structure

```
snowdesign/
  DESIGN_BRIEF_PROMPT.md  - Extraction prompt for agent-to-agent handoff
  SKILL.md                - This file
  scripts/
    stitch_workflow.py    - Main pipeline: brief -> Stitch generation
    stitch_client.py      - Stitch MCP HTTP client
    fetch-stitch.sh       - Download helper for Stitch files
    search.py             - Reference library (BM25 lookups)
    core.py               - BM25 search engine
    design_system.py      - BM25 reference sheet generator
  resources/
    component-template.tsx    - React component template
    architecture-checklist.md - QA gate
  data/                       - 12 CSV datasets + 13 stack guideline files
```

## Setup

### API Keys
- **Stitch:** `~/Documents/ARK/secrets/stitch.env` -> `STITCH_API_KEY`
  Get at: https://stitch.withgoogle.com/settings
- **21st.dev:** `~/secrets/21st-dev.env` -> `API_KEY_21ST`
  Get at: https://21st.dev/magic/console
- **Reference library:** No API keys needed (fully offline)

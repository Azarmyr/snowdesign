# Snowdesign

Brief-driven design-to-code pipeline. Feed it a design brief, get back pixel-perfect screens with production HTML/CSS/Tailwind.

Built on [Google Stitch MCP](https://stitch.withgoogle.com) for visual generation, with an offline reference library of 67 styles, 96 color palettes, 57 font pairings, and 100 industry-specific layout patterns.

## Philosophy

Most design tools work backwards. They start with templates, components, or style presets and constrain your output to what already exists. Snowdesign starts with **your brief** - your brand, your voice, your actual copy - and uses AI to generate designs that match your creative direction, not a database of safe defaults.

The reference library exists for inspiration, not decisions. Browse it when you need ideas. Ignore it when you have a vision.

```
Your Brief (the intelligence)
  -> Google Stitch / Gemini (the creative engine)
  -> HTML/CSS/Tailwind code + screenshots
  -> Optional: React components via 21st.dev Magic MCP
```

## Quick Start

### Prerequisites

- Python 3.10+
- A [Google Stitch API key](https://stitch.withgoogle.com/settings) (free)

### Setup

```bash
git clone https://github.com/Azarmyr/snowdesign.git
cd snowdesign

# Set your Stitch API key
export STITCH_API_KEY="your-api-key-here"
```

### Generate Screens from a Brief

```bash
# Write your design brief (or use the template)
cat DESIGN_BRIEF_PROMPT.md  # see the template

# Generate screens
python3 scripts/stitch_workflow.py --brief my-brief.md -p "My Project"

# With specific screens
python3 scripts/stitch_workflow.py --brief my-brief.md -p "My Project" \
  --screens "landing hero,pricing page,dashboard"

# Mobile screens
python3 scripts/stitch_workflow.py --brief my-brief.md -p "App" \
  --device MOBILE --model GEMINI_3_FLASH

# Pipe from stdin
cat my-brief.md | python3 scripts/stitch_workflow.py -p "My Project"
```

### Browse the Reference Library (no API key needed)

```bash
# Look up visual styles
python3 scripts/search.py "glassmorphism" --domain style

# Browse color palettes
python3 scripts/search.py "luxury warm" --domain color

# Find font pairings
python3 scripts/search.py "editorial serif" --domain typography

# Landing page patterns
python3 scripts/search.py "SaaS" --domain landing

# Framework-specific guidelines
python3 scripts/search.py "performance" --stack nextjs

# Full reference sheet
python3 scripts/search.py "fintech dashboard" --reference -p "My App"
```

## How It Works

### The Brief

The design brief is the core input. It carries everything Stitch needs to generate good designs:

- **Product identity** - what you're building, who it's for
- **Brand personality** - voice, tone, emotional direction
- **Visual direction** - light/dark, density, shape language, references
- **Color and typography** - existing brand colors or desired mood
- **Screen specs** - every screen with real content, CTAs, section order
- **Real copy** - actual headlines, descriptions, button text (not placeholders)

The more context in the brief, the better the output. "Meet Samantha. She remembers everything." produces a real hero section. "Headline goes here" produces generic layouts.

See [`DESIGN_BRIEF_PROMPT.md`](DESIGN_BRIEF_PROMPT.md) for the full extraction template.

### The Pipeline

1. **Brief** is saved and passed to Google Stitch MCP
2. **Stitch project** is created as a container
3. **Each screen** is generated with the full brief as creative context
4. **Gemini AI** interprets the brief and generates HTML/CSS/Tailwind
5. **Output**: project URL, screen IDs, downloadable HTML + screenshots

### Agent-to-Agent Handoff

Snowdesign is designed for AI agent workflows. One agent that knows your brand generates the brief, another runs the pipeline:

```
Agent A (has brand context) -> reads DESIGN_BRIEF_PROMPT.md -> outputs brief
Agent B (has Stitch access) -> runs stitch_workflow.py with the brief -> outputs screens
```

The `DESIGN_BRIEF_PROMPT.md` template tells the first agent exactly what to extract from brand docs, positioning files, and strategy documents.

## Reference Library

An offline, searchable collection of curated design data. Use it for inspiration and research, not as a constraint on your designs.

### What's Inside

| Domain | Records | What It Contains |
|--------|---------|-----------------|
| **Styles** | 67 | Visual styles with keywords, effects, accessibility ratings, framework compatibility, CSS snippets |
| **Colors** | 96 | Curated palettes with hex codes for primary, secondary, CTA, background, text |
| **Typography** | 57 | Font pairings with mood keywords, Google Fonts URLs, CSS imports |
| **Products** | 95 | Product types mapped to recommended styles, color moods, layout patterns |
| **Landing Pages** | 30 | Page patterns with section order, CTA placement, conversion optimization |
| **UX Guidelines** | 98 | Interaction patterns, accessibility rules, responsive behaviors |
| **Industry Rules** | 100 | Category-specific reasoning: anti-patterns, effects, decision rules |
| **Charts** | 25 | Data visualization styles and library recommendations |
| **Icons** | 100 | Icon library recommendations by use case |
| **Web Interfaces** | 30 | Interface patterns with interaction models |

### Stack Guidelines

Framework-specific guidelines for 13 stacks:

`html-tailwind` `react` `nextjs` `vue` `nuxtjs` `nuxt-ui` `svelte` `astro` `shadcn` `swiftui` `react-native` `flutter` `jetpack-compose`

```bash
python3 scripts/search.py "routing" --stack nextjs
python3 scripts/search.py "animations" --stack react
python3 scripts/search.py "gestures" --stack swiftui
```

### Search Domains

```bash
python3 scripts/search.py "<query>" --domain style        # Visual styles
python3 scripts/search.py "<query>" --domain color         # Color palettes
python3 scripts/search.py "<query>" --domain typography    # Font pairings
python3 scripts/search.py "<query>" --domain landing       # Page patterns
python3 scripts/search.py "<query>" --domain product       # Product type mappings
python3 scripts/search.py "<query>" --domain ux            # UX guidelines
python3 scripts/search.py "<query>" --domain chart         # Chart/data viz
python3 scripts/search.py "<query>" --domain icons         # Icon libraries
python3 scripts/search.py "<query>" --domain web           # Web interface patterns
```

## Stitch MCP Client

A standalone Python HTTP client for the [Google Stitch MCP](https://stitch.withgoogle.com/docs/mcp/setup) server. No Node.js required - uses only Python stdlib (`urllib`, `json`).

```bash
# List projects
python3 scripts/stitch_client.py list-projects

# Get screen details (HTML code + screenshot URLs)
python3 scripts/stitch_client.py get-screen <project-id> <screen-id>

# Generate a screen from text
python3 scripts/stitch_client.py generate-screen <project-id> "dashboard with charts" --device DESKTOP

# List available MCP tools
python3 scripts/stitch_client.py list-tools
```

### Available Tools

| Tool | Description |
|------|-------------|
| `create_project` | Create a design project container |
| `list_projects` | List all projects |
| `get_screen` | Get screen HTML/CSS code + screenshot URLs |
| `generate_screen_from_text` | Generate a screen from a text prompt (1-3 min) |
| `edit_screens` | Edit existing screens with a text prompt |
| `generate_variants` | Generate REFINE/EXPLORE/REIMAGINE variants |

> **Note:** Design system tools (create/update/list/apply) require Google OAuth and are not available with API key auth. Snowdesign works around this by injecting design context directly into generation prompts.

## Post-Generation

### Download Stitch Files

```bash
# Get screen metadata first
python3 scripts/stitch_client.py get-screen <project-id> <screen-id>

# Download HTML and screenshots
bash scripts/fetch-stitch.sh "<html-download-url>" "designs/page.html"
bash scripts/fetch-stitch.sh "<screenshot-url>=w1440" "designs/page.png"
```

Append `=w{width}` to screenshot URLs - Google CDN serves low-res thumbnails by default.

### React Conversion (21st.dev Magic MCP)

After downloading Stitch HTML, generate production React components with [21st.dev Magic MCP](https://21st.dev/magic):

1. Review the Stitch HTML/screenshot
2. Identify individual components (navbar, hero, cards, footer)
3. Generate each component via 21st.dev Magic
4. Validate against `resources/architecture-checklist.md`

### Quality Checklist

Before shipping, verify:

- [ ] No hardcoded hex values - use Tailwind theme classes
- [ ] TypeScript interfaces with `Readonly<T>`
- [ ] Dark mode classes applied
- [ ] Responsive at 375px, 768px, 1024px, 1440px
- [ ] Focus states visible
- [ ] `prefers-reduced-motion` respected
- [ ] Logic extracted to custom hooks
- [ ] Static data in dedicated files

Full checklist: [`resources/architecture-checklist.md`](resources/architecture-checklist.md)

## File Structure

```
snowdesign/
  README.md                   - You are here
  SKILL.md                    - Agent skill definition (for OpenClaw/AI agents)
  DESIGN_BRIEF_PROMPT.md      - Brief extraction template for agent handoff
  .gitignore
  scripts/
    stitch_workflow.py        - Main pipeline: brief -> Stitch generation
    stitch_client.py          - Stitch MCP HTTP client (Python stdlib only)
    fetch-stitch.sh           - Reliable download helper for Stitch files
    search.py                 - Reference library CLI (BM25 lookups)
    core.py                   - BM25 search engine
    design_system.py          - Reference sheet generator
  resources/
    component-template.tsx    - React component boilerplate
    architecture-checklist.md - Pre-delivery QA gate
  data/
    styles.csv                - 67 visual styles
    colors.csv                - 96 color palettes
    typography.csv            - 57 font pairings
    products.csv              - 95 product type mappings
    landing.csv               - 30 landing page patterns
    ux-guidelines.csv         - 98 UX interaction patterns
    ui-reasoning.csv          - 100 industry reasoning rules
    charts.csv                - 25 data viz styles
    icons.csv                 - 100 icon library entries
    web-interface.csv         - 30 web interface patterns
    react-performance.csv     - React optimization patterns
    stacks/                   - 13 framework-specific guideline files
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `STITCH_API_KEY` | For Stitch pipeline | Google Stitch MCP API key |
| `API_KEY_21ST` | For React conversion | 21st.dev Magic MCP API key |

The reference library works fully offline with no API keys.

### Get API Keys

- **Stitch**: https://stitch.withgoogle.com/settings (free, Google account required)
- **21st.dev**: https://21st.dev/magic/console

## License

MIT

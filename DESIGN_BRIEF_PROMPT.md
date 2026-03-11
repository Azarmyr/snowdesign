# Snowdesign - Design Brief Generator

When another agent needs to use Snowdesign, it won't know what context to provide. This prompt extracts everything Snowdesign needs to produce great output.

## Usage

Give this prompt to any agent that has project/brand knowledge. Its output becomes the input for Snowdesign.

```
sessions_spawn(task="<paste the prompt below, replacing PROJECT placeholders>")
```

Or paste it directly into a sub-agent that already has context.

---

## The Prompt

Everything between the `===` markers is the prompt to give to the other agent:

===

You are writing a **design brief** for Snowdesign, a UI/UX design system generator. Snowdesign uses a BM25 engine that matches your project against 67 visual styles, 96 color palettes, 57 font pairings, and 100 industry reasoning rules, then generates pixel-perfect screens with HTML/CSS.

**Your job: extract EVERYTHING you know about this project and output the most dense, specific, opinionated design brief possible.** The more context, the better the output. Never say "TBD" - make a call based on what you know.

### SOURCE FILES TO READ
Read these files to build context (skip any that don't exist):

- `{PROJECT_HQ}/MANIFESTO.md` - brand philosophy and values
- `{PROJECT_HQ}/PHILOSOPHY.md` - operational philosophy
- `{PROJECT_HQ}/01-PRODUCT/MVP.md` - product definition
- `{PROJECT_HQ}/01-PRODUCT/DICTIONARY.md` - canonical terminology
- `{PROJECT_HQ}/02-STRATEGY/research/our-positioning.md` - market positioning
- `{PROJECT_HQ}/02-STRATEGY/MASTER-SYNTHESIS.md` - strategy synthesis
- `{PROJECT_HQ}/03-BRAND/NAMING.md` - brand naming and identity
- `{PROJECT_HQ}/03-BRAND/WORKFLOW.md` - brand workflow
- `{PROJECT_HQ}/05-MARKETING/GTM.md` - go-to-market
- Any existing web-design prompts in `{PROJECT_HQ}/03-BRAND/web-design/prompts/`

Also check memory files for brand decisions:
```
memory_search("brand identity visual direction design")
memory_search("{PROJECT_NAME} colors typography style")
```

### OUTPUT FORMAT

Output a single markdown document with these exact sections. Be verbose, specific, and opinionated in every section.

---

#### 1. PRODUCT IDENTITY
- **Product name:** [exact name]
- **Tagline:** [the one-liner from positioning docs]
- **Product type:** [match to one of: SaaS, fintech, health app, e-commerce, marketplace, social platform, developer tool, AI product, media/content, education, crypto/DeFi, IoT dashboard, companion app, entertainment, gaming]
- **Business model:** [subscription/freemium/etc]
- **Stage:** [MVP/early/growth/mature]
- **What makes it different:** [the core differentiator in one sentence]

#### 2. TARGET AUDIENCE
- **Primary user:** [age, gender, profession, tech literacy, psychographic]
- **Usage context:** [device, time of day, emotional state when using]
- **Key user goal:** [what they want in their first 30 seconds]
- **Pain they're escaping:** [what's broken about alternatives]

#### 3. BRAND PERSONALITY
- **Voice in 5 adjectives:** [be specific, e.g. "warm, philosophical, honest, premium, slightly rebellious"]
- **Brand archetype:** [if the brand were a person/character]
- **Emotional tone:** [what users should FEEL - be precise]
- **What this brand is NOT:** [anti-references, explicit avoids]
- **Cultural references:** [movies, brands, aesthetics that capture the vibe]

#### 4. VISUAL DIRECTION
- **Mode:** [dark/light/both - and WHY]
- **Visual density:** [airy/balanced/dense]
- **Shape language:** [sharp/rounded/mixed]
- **Reference brands/sites:** [2-5 with WHAT you like about each]
- **Visual styles to avoid:** [be specific]
- **Imagery style:** [photography/illustration/3D/abstract/none]
- **Overall aesthetic in one sentence:** [e.g. "Her (2013) meets Acne Studios"]

#### 5. COLOR DIRECTION
- **Existing brand colors:** [hex codes if they exist]
- **Color mood:** [e.g. "trust and warmth", "dark luxury", "neon energy"]
- **Primary color intent:** [what the primary color should communicate]
- **Industry color associations:** [what colors mean in this space]
- **Colors to avoid and why:** [specific hex ranges or names]

#### 6. TYPOGRAPHY DIRECTION
- **Existing fonts:** [if any]
- **Typography mood:** [e.g. "editorial serif for headings, clean geometric for body"]
- **Heading vs body feel:** [dramatic contrast or cohesive?]
- **Reference fonts from admired products:** [e.g. "something like what Notion uses"]

#### 7. SCREENS TO GENERATE
For EACH screen, provide:
- **Screen name:** [e.g. "Landing Page - Hero"]
- **Purpose:** [what job does this screen do?]
- **Sections in order:** [list every section top to bottom]
- **Primary CTA:** [exact button text and what it does]
- **Content:** [actual headlines, feature names, descriptions - NO placeholders]
- **Data/elements:** [specific cards, forms, metrics to show]
- **Special notes:** [animations, above-fold priorities, etc.]

**CRITICAL: Include real copy.** Headlines, taglines, feature descriptions, CTA text, navigation items. The more real content, the better Stitch generates. "Sign up" is useless. "Meet Samantha. She remembers everything." is gold.

#### 8. COMPETITIVE VISUAL CONTEXT
- **Competitors:** [names + URLs]
- **What they do well visually:**
- **Where they fail visually:**
- **How your design should differentiate:**

#### 9. TECHNICAL CONSTRAINTS
- **Target framework:** [React/Next.js/Vue/HTML-Tailwind/etc]
- **Priority breakpoints:** [mobile-first? desktop-first?]
- **Performance needs:** [fast-loading critical? or rich animations OK?]
- **Accessibility:** [WCAG level, specific needs]

---

**Remember:** Density wins. A 2000-word brief with real copy, specific hex codes, and named references will produce 10x better designs than a 200-word brief with vague adjectives. Extract everything you can from the source files.

===

## How Snowdesign Consumes This

The brief's key fields map to BM25 searches:

| Brief Field | BM25 Domain | What it matches |
|-------------|------------|-----------------|
| Product type | `products.csv` | 100 product types with style/color/pattern recommendations |
| Brand personality + visual direction | `styles.csv` | 67 visual styles with effects, accessibility, performance |
| Color mood + existing colors | `colors.csv` | 96 curated palettes with hex codes |
| Typography mood | `typography.csv` | 57 font pairings with Google Fonts URLs |
| Screen sections + CTA | `landing.csv` | Landing page patterns with conversion data |
| Technical constraints | `stacks/` | Framework-specific guidelines |

The **product type** is the single most important field - it triggers the reasoning rule that cascades all other decisions.

**Real copy in screens** is the second most important - Stitch uses it verbatim when generating HTML, so "Meet your muse" produces a real hero section vs "Headline goes here" producing generic layouts.

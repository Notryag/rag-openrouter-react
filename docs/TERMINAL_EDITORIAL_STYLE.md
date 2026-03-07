# Terminal Editorial Style

## Goal

Apply a distinct visual system for the RAG workspace that feels like a live research terminal edited with magazine-style typography, instead of a generic SaaS dashboard.

## Core Direction

- Dark editorial canvas instead of white app chrome.
- Warm amber and cool cyan accents, used as signals instead of large flat fills.
- Large grotesk headlines paired with monospace labels and metadata.
- Panels should feel like instrument modules: framed, layered, and slightly tactile.
- The chat transcript remains the visual center. Supporting controls should look secondary but precise.

## Visual Principles

### 1. Editorial hierarchy

- Headlines are large, compact, and high contrast.
- Labels, counters, and metadata use uppercase monospace.
- Body copy stays restrained and readable with moderate line length.

### 2. Terminal cues without retro cosplay

- Use scanline texture, status rails, and signal colors sparingly.
- Avoid neon-on-black overload and avoid fake CRT gimmicks.
- Interaction should feel fast and deliberate, not playful.

### 3. Research desk layout

- Left rail is the control column: identity, auth, ingestion, sessions, status.
- Right stage is the working canvas: transcript, prompt composer, citations.
- Message list should read like a live transcript log, not a casual messenger app.

## Color System

- Background: layered charcoal with subtle green and amber atmospheric gradients.
- Panel background: near-black graphite with translucent overlays.
- Primary text: warm off-white.
- Secondary text: muted parchment gray.
- Accent: amber for primary actions, current selection, and active rails.
- Secondary accent: cyan for system signals and counters.
- Status colors:
  - idle: muted graphite
  - busy: amber
  - success: green
  - error: red

## Typography

- Display and body: `Space Grotesk`
- Metadata and labels: `IBM Plex Mono`

Use cases:
- Titles and section headers: grotesk, bold, tightly spaced
- Eyebrows, IDs, helper text, counters: monospace uppercase

## Component Rules

### Shell

- Full-bleed dark background with subtle radial lighting and scanline overlay.
- Main shell uses a two-column editorial desk layout on desktop and a single stack on mobile.

### Sidebar

- Brand card behaves like the masthead of the workspace.
- Auth, ingestion, sessions, and status cards share the same frame language.
- Session list reads like indexed entries in a ledger.

### Chat stage

- Header includes a title, session state, and compact metrics.
- Add a ticker-style strip for live mode and session state.
- Transcript area gets the strongest framing because it is the primary work surface.

### Messages

- Assistant messages look like system dispatch cards.
- User messages are highlighted with amber tint and right alignment.
- Metadata stays compact and monospace.
- Loading indicators should feel like terminal activity, not playful chat dots.

### Composer

- Composer reads like a prompt drafting module.
- Input area should be tall, dark, and precise.
- Primary submit action uses amber emphasis.

### Sources

- Sources are presented as evidence cards or citation ledger entries.
- Empty state should still look intentional and integrated with the stage.

## Motion

- Use short reveal animations on major panels during initial load.
- Hover and focus motion should be subtle and linear, mostly lift and border glow.
- Loading indicators should use pulse or sweep, not bouncing cartoon movement.

## Responsive Rules

- Collapse to one column below tablet widths.
- Keep transcript, composer, and sources in a stable vertical order.
- On mobile, message bubbles should use full width and stat cards should wrap cleanly.

## Implementation Map

- Global theme tokens and atmospheric background: `frontend/src/index.css`
- Workspace layout and component skinning: `frontend/src/App.css`
- Chat-stage structure and transcript labels: `frontend/src/components/ChatPanel.jsx`
- Sidebar masthead and ledger labels: `frontend/src/components/WorkspaceSidebar.jsx`

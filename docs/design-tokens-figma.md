# Figma Design System — Foundations reference

Source: [swugl Design System](https://www.figma.com/design/QR85omInUcts1hDEHbzN03/swugl-Design-System) (Jeffrey), "Foundations" page, published 2026-08-10.

This is a **read-only reference** of what's in the published Figma file. It does not
reflect the current site CSS (`app/static/css/swugl.css`, the "Peavines Design System")
and no CSS/template changes were made from it — see "Drift from current CSS" below.
Actual implementation of any of this belongs on the `design` branch.

## Colors

| Token | Value |
|---|---|
| `--background` | `#f5fbf8` |
| `--foreground` | `#0d1a13` |
| `--primary` | `#6fcf97` |
| `--secondary` | `#2693ff` |
| `--muted` | `#edf7f2` |
| `--muted-foreground` | `#5a7268` |
| `--border` | `rgba(13,60,35,0.1)` |
| `--warning` | `#f59e0b` |
| `--error` | `#e53e3e` |
| `--info` | `#2693ff` |

The section's own description text calls this palette "violet-forward," which doesn't
match the green/blue swatches above — likely unedited template copy rather than a
deliberate description. Worth confirming with Jeffrey.

Also includes a 10-step brand ramp (50–900) with swatches but no labeled hex values
captured in this pass.

## Type scale

| Style | Font |
|---|---|
| Display XL | Nunito |
| Display LG | Nunito |
| Heading 1 | Nunito |
| Heading 2 | Inter |
| Heading 3 | Inter |
| Body LG | Inter |
| Body SM | Inter |
| Caption | Inter |
| Mono | JetBrains Mono |

The section description text says "Sora for display and headings, Inter for body," which
doesn't match the Nunito labels actually shown on the Display XL/LG and Heading 1 cards —
another apparent inconsistency between the description copy and the actual specimens.

## Spacing scale

4px base unit (Tailwind default scale): `4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96` px.

## Border radius

| Token | Value |
|---|---|
| `sm` | 4px |
| `md` | 8px |
| `lg` | 12px |
| `xl` | 16px |
| `full` | 9999px |

## Elevation (shadow scale)

`none` (0dp), `sm` (2dp), `md` (8dp), `lg` (16dp), `xl` (24dp).

## Iconography

Ant Design icon set, at 16px / 20px / 24px.

## Drift from current CSS

The live `swugl.css` ("Peavines Design System") uses a distinct palette and type stack:

- Colors: warm cream/paper backgrounds, `--vine`/`--pea`/`--sprout` greens, `--berry`,
  `--honey`, `--tomato`, `--sky` accents — not the `--background`/`--primary`/`--secondary`
  names or hex values above.
- Fonts: Spectral (display) + Plus Jakarta Sans (body) + JetBrains Mono (code) — not
  Nunito/Inter.

Whether the Figma file represents a planned redesign or an uncustomized starting template
is unclear from this pass alone. Flag to Jeffrey before treating it as the new source of
truth.

## Not captured this pass

Figma's MCP tool call limit for this account's View seat was hit mid-session, so the
following weren't pulled:

- Exact hex values for the 10-step brand ramp (50–900)
- Component-level specs (buttons, cards, inputs, etc.) beyond the Foundations page
- Variable definitions via Figma's native variables API (`get_variable_defs` — requires
  more seat/plan headroom to retry)

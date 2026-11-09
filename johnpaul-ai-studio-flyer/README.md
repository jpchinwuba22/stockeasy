# Johnpaul AI Studio – Flyer

Promotional flyer for Johnpaul AI Studio (AI, content, ads, websites, digital products).

## Folders
| Folder | What is inside |
|---|---|
| `final/` | **The finished flyer** – `Johnpaul_AI_Studio_Flyer_FINAL_1080x1920.jpg` (shown at 2160×3840, full phone screen, for WhatsApp Status / Instagram Stories) |
| `earlier-versions/` | Previous designs: v1 (blue cards), v2 (poster, old photo), v3 (poster, real photo, small text) |
| `original/` | The old flyer it was redesigned from, and the photo of Johnpaul that was supplied |
| `source/` | Editable design files: `flyer_final.html` (+ v1–v3), fonts, cut-out photos and `render.js` |

## Design
- Bold poster style: orange, deep navy and yellow, with a light paper-grain texture
- Fonts: Anton (headline), Archivo (text), Mrs Saint Delafield (signature), Instrument Serif (tagline)
- Photo: background removed, skin tone made warmer and richer (not lightened)

## Re-export the image
From `source/`: `node render.js flyer.png 2 flyer_final.html` (needs Node and Playwright; the Google fonts load from the internet).

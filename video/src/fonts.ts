import { continueRender, delayRender, staticFile } from "remotion";

export const DISPLAY_FONT = "'Space Grotesk', sans-serif";
export const MONO_FONT = "monospace";

let fontLoaded = false;

export function ensureFontsLoaded(): void {
  if (fontLoaded) return;
  fontLoaded = true;

  const waitForFont = delayRender("Loading Space Grotesk font");
  const font = new FontFace(
    "Space Grotesk",
    `url('${staticFile("fonts/SpaceGrotesk-Bold.woff2")}') format('woff2')`,
    { weight: "700", style: "normal" }
  );

  font
    .load()
    .then(() => {
      document.fonts.add(font);
      continueRender(waitForFont);
    })
    .catch((err) => {
      console.error("Failed to load Space Grotesk:", err);
      continueRender(waitForFont);
    });
}

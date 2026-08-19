import {staticFile} from 'remotion';

// Inject Inter @font-face from the bundled TTFs so text is frame-exact and on-brand
// inside Remotion's headless Chromium (no system-font dependency).
let injected = false;
export function ensureFonts(): void {
  if (injected || typeof document === 'undefined') return;
  injected = true;
  const face = (weight: number, file: string) =>
    `@font-face{font-family:'Inter';font-weight:${weight};font-style:normal;src:url('${staticFile(file)}') format('truetype');}`;
  const css = [
    face(400, 'fonts/inter-regular.ttf'),
    face(600, 'fonts/inter-semibold.ttf'),
    face(700, 'fonts/inter-bold.ttf'),
    face(800, 'fonts/inter-extrabold.ttf'),
    face(900, 'fonts/inter-black.ttf'),
  ].join('\n');
  const el = document.createElement('style');
  el.textContent = css;
  document.head.appendChild(el);
}

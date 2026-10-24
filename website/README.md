# Fly Circuit website

Live: https://fly-circuit-explorer.vercel.app

Interactive explanation of the completed whole-CNS component assay. It displays
saved experimental outputs; it does not run the neural simulation in a browser.
The wiring diagram is a conceptual group schematic, not an anatomical map or
spike-time recording. Three switches select all eight combinations of changes. Side-by-side rotatable 3D-style
brain schematics illustrate the operations with smooth transitions. The numeric
output is the mean published-model stimulus response across six runs. The
explanation opens from the About button. Drag or arrow keys rotate the view;
reduced-motion preference disables automatic rotation.

## Run and check

```sh
cd website
node check-ui.cjs
python3 -m http.server 8765 --directory dist
```

Open http://localhost:8765. There is no build step. `data.js` contains both
cohorts' `readouts.csv` rows, with numeric fields converted to numbers; the
original reference CSV is available as a download. No invented/interpolated
simulation values are added. The check verifies all eight numeric results, reset, explanation visibility,
reduced-motion handling and finite drawing coordinates. Browser-based visual verification was unavailable
in the authoring session.

To deploy with an authenticated Vercel CLI:

```sh
vercel deploy --prod --yes
```

The checked-in `vercel.json` serves `dist/`. Google Fonts is optional; local
sans-serif fallbacks keep the page usable without it.

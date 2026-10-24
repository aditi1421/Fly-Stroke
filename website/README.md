# Fly Circuit website

Live: https://fly-circuit-explorer.vercel.app

Interactive explanation of the completed whole-CNS component assay. It displays
saved experimental outputs; it does not run the neural simulation in a browser.
The wiring diagram is a conceptual group schematic, not an anatomical map or
spike-time recording. Model, run, phase and all eight combinations of changes
are selectable. A fixed comparison table shows the published-model stimulus data.

## Run and check

```sh
cd website
node check-ui.cjs
python3 -m http.server 8765 --directory dist
```

Open http://localhost:8765. There is no build step. `data.js` contains both
cohorts' `readouts.csv` rows, with numeric fields converted to numbers; the
original reference CSV is available as a download. No invented/interpolated
simulation values are added. The 224-state check verifies the control logic
and key displayed results. Browser-based visual verification was unavailable
in the authoring session.

To deploy with an authenticated Vercel CLI:

```sh
vercel deploy --prod --yes
```

The checked-in `vercel.json` serves `dist/`. Google Fonts is optional; local
sans-serif fallbacks keep the page usable without it.

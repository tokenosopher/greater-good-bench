# The Human Field Manual

An offline-ready, interactive citizen training and calibration website designed so that if everyone saw and practiced it, it would save lives, disarm conflict, and multiply human good across five concentric scales of agency:

1. **Scale I — The Body (First 4 Minutes):** Interactive 110 BPM Hands-Only CPR Rhythm & Cerebral Perfusion Simulator (with procedural Web Audio metronome and spacebar/touch compression trainer) + emergency triage protocols for Choking (5+5), Stroke (B.E.F.A.S.T.), and Severe Bleeding.
2. **Scale II — The Nervous System (First 60 Seconds):** Live Alveolar & Vagus Nerve Breath Pacer modeling Respiratory Sinus Arrhythmia (Physiological Sigh, Box Breathing, 4-7-8 Downshift) + Dr. Jill Bolte Taylor's 90-Second Adrenaline Clearance Timer and Cognitive Distortion Defusion tool.
3. **Scale III — The Conversation (5 Minutes):** Branching Nonviolent Conflict De-escalation Simulator + Interactive Game-Theory Sandbox modeling Robert Axelrod & Martin Nowak's *Generous Tit-for-Tat* under communication noise.
4. **Scale IV — The Household (First 24 Hours):** Interactive WHO Oral Rehydration Solution (SGLT1 Sodium-Glucose Cotransporter) Lab demonstrating the exact `6 tsp sugar : 1/2 tsp salt per 1L` hypotonic ratio + Emergency Safe Water Disinfection Calculator.
5. **Scale V — The World (Lifetime Leverage):** Empirical Reality Calibrator (curing fatalism with historical poverty and child survival data) + The 100× Life-Saving Leverage & Biological Donor Calculator.
6. **Pocket Field Card:** Printable and downloadable high-resolution 1-page emergency & high-leverage reference card.

## Architecture
- Entry point: `index.html` + `main.js` + `styles.css`
- Modules: `src/audio.js`, `src/section1-cpr.js`, `src/section2-breath.js`, `src/section3-conflict.js`, `src/section4-water.js`, `src/section5-leverage.js`, `src/section6-card.js`
- 100% self-contained: zero network requests, zero external assets, and zero `localStorage`/cookie dependencies for full sandboxed offline compatibility.

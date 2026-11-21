# Brandsbjerg Syd – vedtægter

Forslag til nye vedtægter og nyt ordensreglement for Grundejerforeningen Brandsbjerg Syd, med en visning af ændringerne i forhold til de nuværende.

- `indhold.js` – teksten. Hvert stk. har den nye tekst og, hvor den findes, den nuværende tekst den erstatter (`nu`) og hvor den står (`ref`).
- `bilag.js` – kort og matrikelliste til bilag 1, genereret af `tools/byg_bilag.py`.
- `nuvaerende-vedtaegter.pdf` – de nuværende vedtægter (1968, senest ændret 1995) og ordensreglementet (1997).

Byg bilag 1 igen:

```bash
python3 tools/byg_bilag.py <parceller-data.js> <kortdata.osm> bilag.js
```

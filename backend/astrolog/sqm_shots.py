"""Which shots sky brightness is for (ADR 0022 point 8), alone: the stage and the site's sky read
it, and the stage rewrites the site's sky."""

# Mono behind L, colour behind no filter or a broad one. Readers filter with it too: a filter
# answered later changes the set. Aliases: c the card, p the filter spelling.
SQM_SHOTS = (
    "((c.bayer = 1 AND (c.filter IS NULL OR p.standard IN ('l', 'uvir', 'none')"
    "   OR (p.filter_name IS NOT NULL AND NOT EXISTS (SELECT 1 FROM pipeline_filter_bands AS b"
    "   WHERE b.filter_name = p.filter_name AND b.band NOT IN ('l', 'uvir')))))"
    " OR (ifnull(c.bayer, 0) = 0 AND (p.standard = 'l'"
    "   OR (p.filter_name IS NOT NULL AND NOT EXISTS (SELECT 1 FROM pipeline_filter_bands AS b"
    "   WHERE b.filter_name = p.filter_name AND b.band <> 'l')))))"
)

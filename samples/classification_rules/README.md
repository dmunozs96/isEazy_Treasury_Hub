# Classification Rules — Source Material

Place the VLOOKUP-based classification Excel here.

**What this file should contain:**
- The description keywords or patterns you used to identify each type of movement
- The category each pattern maps to (payroll, tax, intercompany, supplier, etc.)
- Any intercompany patterns (partial names, abbreviations, reference prefixes) that appear in real bank statement descriptions

**What we will extract from it:**
1. All keyword → category mappings → seeded as ClassificationRule records
2. Intercompany detection patterns → seeded as priority 5–7 rules (run before all other rules)
3. Foreign entity patterns (Belgium, Colombia, Mexico, Puerto Rico subsidiaries) → seeded as INT_INTERCOMPANY_FOREIGN rules

**IMPORTANT — How to use this file:**
This file is a good starting point, not a complete or authoritative source. It is known to contain:
- Omissions (movements not covered by any rule)
- Possible misclassifications

The rules engine is designed for this: anything unmatched is flagged as UNCLASSIFIED for manual review. Rules can be corrected at any time and re-run retroactively against all historical movements. The first real import will surface the gaps; we fix them iteratively.

Do NOT treat this file as the final rule set. Treat it as draft v0.

**Note on entity names:** Full legal entity names are NOT required. Whatever partial name, abbreviation, or reference pattern reliably appears in bank statement descriptions is what matters.

**File naming:** Any name is fine — e.g., `clasificacion_movimientos.xlsx`

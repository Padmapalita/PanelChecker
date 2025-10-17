# UI Refinements V4 - Multiple Callouts & Percentage Change Column

## Date: October 17, 2025

## Overview
Enhanced the gene comparison display with granular status callouts and a new percentage change analysis column to show gene size differences between Ensembl versions.

## Changes Implemented

### 1. **Multiple Status Callouts** (Replaces Single Status Badge)

**Before:** Single status badge showing "changed", "retained", or "missing"

**After:** Multiple specific callout badges showing exactly what changed:

#### Callout Types:
- 🔴 **Gene Not Found** - Target version doesn't contain this gene (RED)
- 🟠 **Symbol Changed** - Gene symbol differs between versions (ORANGE)
- 🟡 **Ensembl ID Changed** - Ensembl identifier changed (AMBER)
- 🔵 **Location Changed** - Genomic coordinates changed (BLUE)
- 🟢 **All Retained** - Everything matches perfectly (GREEN)

#### Example Display:
```
🟢 GREEN    ACAD9    🔵 Location Changed
```

or

```
🟢 GREEN    DYSF    🟠 Symbol Changed    🟡 Ensembl ID Changed    🔵 Location Changed
```

#### Benefits:
- **Immediate clarity** on what specifically changed
- **Multiple indicators** can appear simultaneously
- **Color-coded urgency**: Red (critical) → Orange → Amber → Blue → Green (ok)

### 2. **Percentage Change Column**

Added a fourth column to the comparison table showing the percentage change in gene size between versions.

#### Column Header:
```
| Field | Current Version (Ensembl XX) | Target Version (Ensembl YY) | % Change |
```

#### Calculation Logic:
```javascript
currentSize = current_end - current_start
targetSize = target_end - target_start
percentageChange = ((targetSize - currentSize) / currentSize) * 100
```

#### Example Calculations:

**ACAD9 Gene:**
- Current (Ensembl 90): chr3:128,879,596-128,916,067 = **36,471 bp**
- Target (Ensembl 107): chr3:128,879,596-128,924,003 = **44,407 bp**
- Change: **+21.76%** (gene grew by ~8kb)

**Interpretation:**
- **0%**: Location unchanged (perfect match)
- **+50%**: Gene is 50% larger in target version
- **-25%**: Gene is 25% smaller in target version

#### Color Coding:

| Change Magnitude | Color | Meaning |
|-----------------|-------|---------|
| **> 10%** | 🔴 Red + Bold | Major size change - requires attention |
| **1-10%** | 🟡 Amber + Semi-bold | Moderate change - review recommended |
| **< 1%** | 🔵 Blue | Minor change - likely annotation refinement |
| **0%** | Gray dash | No change |

### 3. **New Table Row: "Gene Size Change"**

Added a dedicated row in the comparison table to highlight size information:

```
| Gene Size Change | 36,471 bp | 44,407 bp | +21.76% |
```

- Light blue background for emphasis
- Shows absolute sizes in base pairs (bp)
- Percentage change prominently displayed

### 4. **Layout Enhancements**

- **Flex-wrap on header**: Status callouts can wrap to multiple lines if needed
- **Consistent spacing**: All callouts use same padding and gap
- **Icon indicators**: Each callout has a meaningful Lucide icon

## Technical Implementation

### Frontend JavaScript Changes

#### 1. Multiple Callout Logic:
```javascript
const callouts = [];

if (!gene.target_version) {
  callouts.push('Gene Not Found');
}
if (!gene.symbol_retained && gene.target_version) {
  callouts.push('Symbol Changed');
}
if (!gene.ensembl_id_retained && gene.target_version) {
  callouts.push('Ensembl ID Changed');
}
if (gene.location_changed && gene.target_version) {
  callouts.push('Location Changed');
}
if (all_perfect) {
  callouts.push('All Retained');
}
```

#### 2. Percentage Calculation:
```javascript
const currentSize = gene.current_version.end - gene.current_version.start;
const targetSize = gene.target_version.end - gene.target_version.start;
const sizePctChange = ((targetSize - currentSize) / currentSize * 100).toFixed(2);
```

#### 3. Color Formatting:
```javascript
const formatPctChange = (pct) => {
  const numPct = parseFloat(pct);
  const absNum = Math.abs(numPct);
  
  if (absNum > 10) return 'RED + BOLD';
  if (absNum > 1) return 'AMBER + SEMIBOLD';
  if (absNum > 0) return 'BLUE';
  return 'GRAY DASH';
};
```

## User Benefits

### For Curators:

1. **Granular Change Tracking**
   - See exactly what changed at a glance
   - No need to expand accordion to understand changes
   - Multiple changes clearly visible simultaneously

2. **Quantified Impact**
   - Percentage change shows magnitude of location shift
   - Large changes (>10%) flagged in red for immediate attention
   - Understand if gene grew, shrunk, or just shifted position

3. **Prioritization**
   - Red badges = urgent review needed
   - Amber/Blue badges = standard review
   - Green badges = quick approval possible

4. **Audit Trail**
   - Percentage changes provide concrete metrics for documentation
   - Clear evidence of what changed and by how much
   - Supports regulatory requirements

### Example Scenarios:

#### Scenario 1: Minor Annotation Update
```
🟢 GREEN    ACAD9    🔵 Location Changed
Gene Size Change: 36,471 bp → 36,475 bp (+0.01%)
```
**Action:** Quick review, likely just refinement

#### Scenario 2: Significant Reannotation
```
🟢 GREEN    DYSF    🔵 Location Changed
Gene Size Change: 228,000 bp → 342,000 bp (+50.00%)
```
**Action:** Detailed review required - major structural change

#### Scenario 3: Multiple Issues
```
🔴 RED    MYH7    🟠 Symbol Changed    🟡 Ensembl ID Changed    🔵 Location Changed
Gene Size Change: 22,900 bp → 23,500 bp (+2.62%)
```
**Action:** Critical review - multiple identifiers changed

## Testing Examples

### Test Data: ACAD9 (Ensembl 90 → 107)

**Input:**
- Current: chr3:128,879,596-128,916,067 (36,471 bp)
- Target: chr3:128,879,596-128,924,003 (44,407 bp)

**Expected Output:**
- Callout: "Location Changed" (blue)
- Size: 36,471 bp → 44,407 bp
- % Change: +21.76% (red, bold)

**Result:** ✅ Correctly displays large increase, flagged in red

## Files Modified

1. **`frontend/index.html`**:
   - Added `callouts` array building logic
   - Implemented `formatPctChange()` function
   - Added percentage calculation for start, end, and size
   - Added fourth column to table header
   - Added "Gene Size Change" row with highlighting
   - Added % Change cells to all table rows

## Visual Examples

### Header with Multiple Callouts:
```
┌────────────────────────────────────────────────────────┐
│ 🟢  ACAD9  🔵 Location Changed                 ⌄     │
├────────────────────────────────────────────────────────┤
│ Table (collapsed)                                      │
└────────────────────────────────────────────────────────┘
```

### Expanded Table with % Change Column:
```
┌─────────────────┬─────────────────┬─────────────────┬──────────┐
│ Field           │ Current (E 90)  │ Target (E 107)  │ % Change │
├─────────────────┼─────────────────┼─────────────────┼──────────┤
│ Ensembl ID      │ ENSG00000177646 │ ENSG00000177646 │    —     │
│ Chromosome      │ chr3            │ chr3            │    —     │
│ Start Position  │ 128,879,596     │ 128,879,596     │    —     │
│ End Position    │ 128,916,067     │ 128,924,003     │    —     │
│ Strand          │ +               │ +               │    —     │
│ Gene Size       │ 36,471 bp       │ 44,407 bp       │ +21.76%  │
│ Location Summary│ chr3:128,879... │ chr3:128,879... │    —     │
└─────────────────┴─────────────────┴─────────────────┴──────────┘
```

## Next Steps

✅ Multiple callouts implemented
✅ Percentage change column implemented
✅ Color coding for change magnitude implemented
✅ Gene size row added with emphasis

Ready for user testing! 🎉

## Future Enhancements (Not in Scope)

- Histogram showing distribution of % changes across all genes
- Filtering by callout type (e.g., show only "Location Changed" genes)
- Sorting by % change magnitude
- Export percentage changes to CSV


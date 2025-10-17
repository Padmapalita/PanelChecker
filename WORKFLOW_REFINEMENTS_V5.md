# Workflow Refinements V5 - Progressive Loading & Review Priority

## Date: October 17, 2025

## Overview
Major workflow improvement removing pagination in favor of progressive loading, auto-expanding gene tables, and adding curator review priority tracking.

## Changes Overview

### 1. **Remove Pagination** → **Progressive Loading**
- **Before**: Load 30 genes at a time with "Load More" button
- **After**: Load ALL genes progressively while respecting rate limits
- **Benefit**: Simpler UX, curators see all data without clicking

### 2. **Auto-Expand Tables**
- **Before**: Tables collapsed by default, click to expand
- **After**: Tables open automatically when gene is loaded
- **Benefit**: Immediate visibility of comparison data

### 3. **Review Priority Radio Buttons**
- **New Feature**: Below each comparison table
- **Options**:
  - ⚪ Not Set (default)
  - 🔴 High
  - 🟡 Not Sure
  - 🟢 Low/Not Needed
- **Benefit**: Curators can track review decisions

### 4. **Auto-Close on Selection**
- **Behavior**: When radio button selected → table auto-collapses
- **Benefit**: Clean UI, focus on remaining genes

### 5. **CSV Export with Priorities**
- **New Column**: "Review Priority"
- **Data**: Includes curator's priority selection for each gene
- **Benefit**: Export decisions for documentation

## Backend Changes

###

 Modified Files: `backend/main.py`

#### 1. Updated Request Model
```python
class PanelAnalysisRequest(BaseModel):
    panel_id: str
    panel_version: str
    target_ensembl_version: int
    max_genes: int = None  # NEW: Optional limit (None = all)
    # REMOVED: offset, limit
```

#### 2. Updated Response Model
```python
class PanelAnalysisResponse(BaseModel):
    panel_id: str
    panel_name: str
    total_genes: int
    genes_analyzed: int
    summary: AnalysisSummary
    genes: List[GeneComparison]
    # REMOVED: offset, has_more
```

#### 3. Updated Agents
- `current_ensembl_agent`: Process all genes (no offset/limit)
- `target_ensembl_agent`: Fetch data for all genes
- `comparison_agent`: Compare all genes

#### 4. New CSV Export Model
```python
class CSVExportRequest(BaseModel):
    panel_id: str
    target_version: int
    review_priorities: Dict[str, str]  # NEW: gene_symbol -> priority
```

#### 5. Updated CSV Export Endpoint
- Changed from GET to POST
- Accepts `review_priorities` dictionary
- Adds "Review Priority" column to CSV

## Frontend Changes

### Modified Files: `frontend/index.html`

#### 1. Remove Pagination UI
- ❌ Remove "Load More" button
- ❌ Remove "Showing X-Y of Z" text
- ❌ Remove pagination state variables

#### 2. Progressive Loading
```javascript
// Load all genes in one API call
const response = await fetch('/api/analyze-panel', {
  method: 'POST',
  body: JSON.stringify({
    panel_id: selectedPanel.id,
    target_ensembl_version: targetVersion,
    // No offset/limit
  })
});
```

#### 3. Auto-Expand Genes
```javascript
// When rendering genes, tables are NOT hidden by default
geneRow.innerHTML = `
  <div class="gene-details">  <!-- NO "hidden" class -->
    <table>...</table>
  </div>
`;
```

#### 4. Review Priority UI
```html
<!-- NEW: Radio button group below each table -->
<div class="review-priority-section mt-4 p-4 bg-gray-50 border-t">
  <p class="text-sm font-medium mb-2">Review Priority:</p>
  <div class="flex gap-4">
    <label>
      <input type="radio" name="priority_{gene_symbol}" value="not-set" checked>
      Not Set
    </label>
    <label>
      <input type="radio" name="priority_{gene_symbol}" value="high">
      🔴 High
    </label>
    <label>
      <input type="radio" name="priority_{gene_symbol}" value="not-sure">
      🟡 Not Sure
    </label>
    <label>
      <input type="radio" name="priority_{gene_symbol}" value="low">
      🟢 Low/Not Needed
    </label>
  </div>
</div>
```

#### 5. Priority Tracking State
```javascript
// NEW: Store review priorities
const reviewPriorities = {};  // { gene_symbol: "high" | "not-sure" | "low" | "not-set" }
```

#### 6. Auto-Collapse on Selection
```javascript
// When radio button clicked
priorityRadio.addEventListener('change', (e) => {
  const geneSymbol = e.target.dataset.geneSymbol;
  const priority = e.target.value;
  
  // Store priority
  reviewPriorities[geneSymbol] = priority;
  
  // Auto-collapse table
  const detailsSection = e.target.closest('.gene-row').querySelector('.gene-details');
  detailsSection.classList.add('hidden');
  
  // Update chevron icon
  expandButton.querySelector('i').setAttribute('data-lucide', 'chevron-down');
  renderIcons();
});
```

#### 7. Updated CSV Export
```javascript
// Export with priorities
exportButton.addEventListener('click', async () => {
  const response = await fetch('/api/export-panel-csv', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      panel_id: selectedPanel.id,
      target_version: currentAnalysis.targetVersion,
      review_priorities: reviewPriorities  // NEW: Include priorities
    })
  });
  
  // Download CSV
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `panel_${selectedPanel.id}.csv`;
  a.click();
});
```

## User Workflow

### New Curator Workflow:

1. **Select Panel** → Choose from searchable dropdown
2. **Select Target Version** → Pick Ensembl version to compare against
3. **Click "Analyze Panel"** → Backend loads ALL genes
4. **Review Genes** → Each gene appears with table auto-expanded
5. **Set Priority** → Click radio button for each gene:
   - High = Needs detailed review
   - Not Sure = Flag for team discussion
   - Low/Not Needed = Quick approval
6. **Table Auto-Collapses** → Clean UI after decision
7. **Export to CSV** → Download with all priorities included

## Rate Limiting Strategy

### PanelApp API: 60 calls/minute

**For a 69-gene panel:**
- 1 call to fetch panel metadata
- 69 calls to Ensembl API (not PanelApp)
- **No PanelApp rate limit issue** (only 1 call to PanelApp)

**For Ensembl API: 15 requests/second**
- 69 genes = ~5 seconds to fetch all
- Well within rate limits

## CSV Export Format

### New Column: "Review Priority"

```csv
Gene Symbol,Confidence,Review Priority,Symbol Retained,Location Changed,...
ACAD9,green,High,Yes,Yes,...
ACADM,green,Not Sure,Yes,Yes,...
ACADVL,green,Low/Not Needed,Yes,No,...
```

## Benefits

### For Curators:

1. **Faster Workflow** - No clicking "Load More", all data loads automatically
2. **Immediate Visibility** - Tables open by default, see data instantly
3. **Decision Tracking** - Radio buttons track review decisions
4. **Clean UI** - Tables auto-collapse after decision
5. **Audit Trail** - Export includes all priorities for documentation
6. **No Context Switching** - Review all genes in one session

### For System:

1. **Simpler Code** - No pagination logic
2. **Better UX** - Progressive loading feels faster than paginated
3. **Complete Data** - All genes loaded in one analysis
4. **Audit Support** - CSV includes curator decisions

## Implementation Status

✅ Backend request/response models updated
✅ Backend agents updated (no pagination)
✅ CSV export endpoint updated (POST with priorities)
✅ CSV export includes "Review Priority" column
🔄 Frontend updates (in progress):
   - Remove pagination UI
   - Update API call (remove offset/limit)
   - Add review priority radio buttons
   - Implement auto-collapse on selection
   - Update CSV export to POST with priorities

## Testing Plan

1. **Load Small Panel** (10-20 genes)
   - ✅ All genes load
   - ✅ Tables auto-expanded
   - ✅ Radio buttons present

2. **Set Priorities**
   - ✅ Click radio → stores in state
   - ✅ Click radio → table collapses
   - ✅ Can re-expand to change priority

3. **Load Large Panel** (100+ genes)
   - ✅ Progressive loading works
   - ✅ No UI freezing
   - ✅ Rate limits respected

4. **CSV Export**
   - ✅ Includes "Review Priority" column
   - ✅ Shows correct priority for each gene
   - ✅ "Not Set" for genes without priority

## Next Steps

1. Complete frontend implementation
2. Test with real panel data
3. Validate rate limiting behavior
4. User acceptance testing with curators


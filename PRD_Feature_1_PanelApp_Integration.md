# Product Requirements Document: Feature 1 - PanelApp Integration & Gene Retrieval

**Version:** 1.0  
**Date:** October 17, 2025  
**Status:** Approved for Implementation  
**Owner:** PanelChecker Development Team

---

## Executive Summary

This PRD defines Feature 1 of the PanelChecker application: the foundation for genomics panel analysis through integration with the PanelApp API and Ensembl REST API. This feature enables scientific curators to select panels, choose Ensembl versions for comparison, and view paginated gene comparison results.

## Goals & Objectives

### Primary Goals
1. Enable curators to browse and select genomics panels from PanelApp
2. Allow selection of target Ensembl version for comparison
3. Display gene-level comparison results with visual indicators
4. Support export of analysis results to CSV format

### Success Metrics
- Successfully fetch panels from PanelApp API (100% success rate)
- Display first 30 gene comparisons within 10 seconds
- Zero API rate limit violations
- CSV export contains all required data fields
- User can complete full workflow without errors

### Non-Goals (Out of Scope)
- Historical tracking of previous analyses
- Multi-panel batch processing (Feature 5)
- Advanced filtering/search within results
- User authentication
- Automated recommendations

---

## User Personas

### Primary: Scientific Curator
**Background:** PhD-level scientist managing genomics reference data  
**Technical Level:** High domain knowledge, moderate web application experience  
**Pain Points:**
- Manual comparison of gene data across Ensembl versions is time-consuming
- Risk of missing critical changes in gene symbols or locations
- Need to document changes for team review

**Goals:**
- Quickly identify genes affected by Ensembl version changes
- Export results for team discussion
- Ensure data integrity before committing updates

---

## User Stories

### Epic: Panel Selection & Configuration

**US-1.1: Browse Available Panels**
```
As a curator
I want to search and browse available panels from PanelApp
So that I can select the panel I need to analyze
```

**Acceptance Criteria:**
- System displays list of panels from PanelApp
- User can search panels by name or ID
- Panel list shows: panel ID, name, version, and number of genes
- Only signed-off panel versions are displayed
- Loading state shown while fetching panels

---

**US-1.2: Select Panel for Analysis**
```
As a curator
I want to select a specific panel
So that I can proceed to configure the comparison
```

**Acceptance Criteria:**
- User can click on a panel to select it
- Selected panel is visually highlighted
- Panel details are displayed (name, ID, version, gene count)
- User can change selection before proceeding

---

**US-1.3: Choose Ensembl Version**
```
As a curator
I want to select the target Ensembl version for comparison
So that I can analyze changes between the current and target versions
```

**Acceptance Criteria:**
- Dropdown or selector displays available Ensembl versions
- Current version is pre-selected by default
- User can select a different target version
- Version numbers are clearly labeled (e.g., "Ensembl 109", "Ensembl 110")
- System validates that current and target versions are different

---

**US-1.4: Initiate Analysis**
```
As a curator
I want to submit my panel and version selections
So that the system can perform the comparison analysis
```

**Acceptance Criteria:**
- "Analyze Panel" button is enabled when selections are valid
- Button shows loading state during analysis
- Clear error message if analysis fails
- User is taken to results view upon success

---

### Epic: Gene Comparison Results

**US-1.5: View Paginated Gene Comparisons**
```
As a curator
I want to see gene comparison results in manageable batches
So that I can review them without overwhelming the interface or API
```

**Acceptance Criteria:**
- First 30 genes are displayed automatically
- Genes are ordered: Green → Amber → Red (confidence rating)
- Each gene shows: symbol, confidence rating, comparison status
- "Load More" button fetches next 30 genes
- Loading indicator shown while fetching additional genes
- Button is disabled when all genes are loaded

---

**US-1.6: Identify Gene Changes**
```
As a curator
I want to see visual indicators for each gene comparison
So that I can quickly identify which genes have changed
```

**Acceptance Criteria:**
- Symbol retained: Green checkmark or "Retained" badge
- Symbol changed: Orange warning icon or "Changed" badge
- Location changed: Orange warning icon or "Location Changed" badge
- Gene missing in target: Red X or "Missing" badge
- Multiple change types shown simultaneously (e.g., symbol + location)

---

**US-1.7: View Gene Details**
```
As a curator
I want to expand a gene row to see detailed information
So that I can understand the specific changes
```

**Acceptance Criteria:**
- Gene rows are expandable (click to expand/collapse)
- Expanded view shows:
  - Current version: Ensembl ID, gene symbol, chromosome, start position, end position, strand
  - Target version: Same fields
  - Differences are highlighted in color
- Missing genes show "Not found in target version" message

---

**US-1.8: Export Results to CSV**
```
As a curator
I want to export the analysis results to CSV
So that I can share them with my team and maintain records
```

**Acceptance Criteria:**
- "Export CSV" button is always visible
- CSV includes all genes (not just loaded ones)
- CSV columns:
  - Gene Symbol
  - Confidence Rating (Green/Amber/Red)
  - Symbol Retained (Yes/No)
  - Location Changed (Yes/No)
  - Current Ensembl ID
  - Target Ensembl ID
  - Current Chromosome
  - Target Chromosome
  - Current Start Position
  - Target Start Position
  - Current End Position
  - Target End Position
  - Current Strand
  - Target Strand
  - Status (Retained/Changed/Missing)
- Filename format: `PanelChecker_{PanelID}_{CurrentVersion}_vs_{TargetVersion}_{Date}.csv`
- File downloads immediately upon click

---

## User Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     STAGE 1: SELECTION PHASE                    │
└─────────────────────────────────────────────────────────────────┘

[Landing Page]
      ↓
[Browse/Search Panels] ← API: GET /panels/ (PanelApp)
      ↓
[Select Panel] → Display panel details
      ↓
[Select Target Ensembl Version] → Dropdown with versions
      ↓
[Click "Analyze Panel"] → Validation
      ↓
┌─────────────────────────────────────────────────────────────────┐
│                     STAGE 2: ANALYSIS PHASE                     │
└─────────────────────────────────────────────────────────────────┘

[Multi-Agent System Executes]
      ↓
[Results Page Loads - First 30 Genes]
      ↓
[User Reviews Genes] ←→ [Expand/Collapse Details]
      ↓
[Click "Load More"] → Fetch next 30 genes
      │ (Repeat as needed)
      ↓
[Click "Export CSV"] → Download complete results
```

---

## Technical Architecture

### Frontend Components

#### 1. Panel Selection Component
- **File:** `frontend/index.html` (to be refactored)
- **Elements:**
  - Search bar for panel name/ID
  - Panel list table/cards
  - Selected panel detail view
  - Ensembl version dropdown
  - "Analyze Panel" button

#### 2. Results Display Component
- **Elements:**
  - Summary statistics (total genes, changes detected)
  - Paginated gene table (30 per page)
  - Expand/collapse gene details
  - "Load More" button
  - "Export CSV" button
  - Visual badges/icons for change indicators

### Backend Architecture

#### API Endpoints

**1. GET `/api/panels`**
- **Purpose:** Fetch available panels from PanelApp
- **Query Parameters:**
  - `search` (optional): Search term for panel name/ID
  - `signed_off_only` (default: true): Filter for signed-off versions
- **Response:**
```json
{
  "count": 150,
  "panels": [
    {
      "id": "137",
      "name": "Cardiac arrhythmias",
      "version": "3.45",
      "gene_count": 127,
      "signed_off": true
    }
  ]
}
```

**2. POST `/api/analyze-panel`**
- **Purpose:** Submit panel for analysis
- **Request Body:**
```json
{
  "panel_id": "137",
  "panel_version": "3.45",
  "current_ensembl_version": 109,
  "target_ensembl_version": 110,
  "offset": 0,
  "limit": 30
}
```
- **Response:**
```json
{
  "panel_id": "137",
  "panel_name": "Cardiac arrhythmias",
  "total_genes": 127,
  "genes_analyzed": 30,
  "offset": 0,
  "has_more": true,
  "summary": {
    "symbols_retained": 28,
    "symbols_changed": 1,
    "locations_changed": 2,
    "genes_missing": 1
  },
  "genes": [
    {
      "gene_symbol": "SCN5A",
      "confidence": "green",
      "symbol_retained": true,
      "location_changed": false,
      "current_version": {
        "ensembl_id": "ENSG00000183873",
        "gene_symbol": "SCN5A",
        "chromosome": "3",
        "start": 38548665,
        "end": 38649687,
        "strand": 1
      },
      "target_version": {
        "ensembl_id": "ENSG00000183873",
        "gene_symbol": "SCN5A",
        "chromosome": "3",
        "start": 38548665,
        "end": 38649687,
        "strand": 1
      }
    }
  ]
}
```

**3. GET `/api/export-panel-csv/{session_id}`**
- **Purpose:** Export full panel analysis to CSV
- **Response:** CSV file download

---

### Multi-Agent System Design

#### Agent 1: Panel Data Agent
**Responsibility:** Fetch panel and gene list from PanelApp

**Tools:**
- `fetch_panel_metadata`: Get panel details
- `fetch_panel_genes`: Get list of genes with confidence ratings

**API Calls:**
1. `GET https://panelapp.genomicsengland.co.uk/api/v1/panels/{id}/`
2. `GET https://panelapp.genomicsengland.co.uk/api/v1/panels/{id}/genes/`

**Rate Limiting Strategy:**
- Track calls per minute (max 60)
- Implement exponential backoff on 429 errors
- Cache panel metadata for 1 hour

---

#### Agent 2: Current Ensembl Agent
**Responsibility:** Fetch gene data from current Ensembl version

**Tools:**
- `lookup_gene_by_symbol`: Query Ensembl by gene symbol
- `lookup_gene_by_id`: Query Ensembl by Ensembl ID

**API Calls:**
- `GET https://rest.ensembl.org/lookup/symbol/homo_sapiens/{symbol}`
- Rate limit: 15 requests/second (respect with delays)

**GRCh38 Constraint:**
- Always use GRCh38 assembly
- Validate assembly in responses

---

#### Agent 3: Target Ensembl Agent
**Responsibility:** Fetch gene data from target Ensembl version

**Tools:** Same as Agent 2

**Version Handling:**
- Use Ensembl archive API for older versions
- Example: `https://e109.rest.ensembl.org/` for version 109

---

#### Agent 4: Comparison Agent
**Responsibility:** Compare gene data between versions

**Logic:**
1. Check if gene symbol exists in both versions
2. Compare Ensembl IDs
3. Compare genomic locations (chromosome, start, end, strand)
4. Generate change summary

**Output:** Structured comparison object per gene

---

#### Agent 5: Synthesis Agent
**Responsibility:** Aggregate results and format for display

**Tasks:**
1. Sort genes by confidence (Green → Amber → Red)
2. Calculate summary statistics
3. Format response for frontend
4. Handle pagination

---

### Data Models (Pydantic)

```python
# Request Models
class PanelAnalysisRequest(BaseModel):
    panel_id: str
    panel_version: str
    current_ensembl_version: int
    target_ensembl_version: int
    offset: int = 0
    limit: int = 30

# Response Models
class GenomicLocation(BaseModel):
    ensembl_id: str
    gene_symbol: str
    chromosome: str
    start: int
    end: int
    strand: int

class GeneComparison(BaseModel):
    gene_symbol: str
    confidence: Literal["green", "amber", "red"]
    symbol_retained: bool
    location_changed: bool
    ensembl_id_retained: bool
    current_version: Optional[GenomicLocation]
    target_version: Optional[GenomicLocation]
    status: Literal["retained", "changed", "missing"]

class AnalysisSummary(BaseModel):
    symbols_retained: int
    symbols_changed: int
    locations_changed: int
    genes_missing: int

class PanelAnalysisResponse(BaseModel):
    panel_id: str
    panel_name: str
    total_genes: int
    genes_analyzed: int
    offset: int
    has_more: bool
    summary: AnalysisSummary
    genes: List[GeneComparison]
```

---

### Rate Limiting Implementation

```python
import time
from collections import deque
from typing import Deque

class RateLimiter:
    """Rate limiter for PanelApp API (60 calls/min)"""
    
    def __init__(self, max_calls: int = 60, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls: Deque[float] = deque()
    
    def wait_if_needed(self):
        """Block if rate limit would be exceeded"""
        now = time.time()
        
        # Remove calls outside the window
        while self.calls and self.calls[0] < now - self.window_seconds:
            self.calls.popleft()
        
        # If at limit, wait
        if len(self.calls) >= self.max_calls:
            sleep_time = self.window_seconds - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.calls.append(now)

# Global rate limiter instance
panelapp_limiter = RateLimiter(max_calls=60, window_seconds=60)
```

---

## API Integration Specifications

### PanelApp API

**Base URL:** `https://panelapp.genomicsengland.co.uk/api/v1/`

**Required Headers:**
```python
headers = {
    "User-Agent": "KMDS-PdM",
    "Accept": "application/json"
}
```

**Key Endpoints:**

1. **List Panels**
   - `GET /panels/`
   - Query params: `?search={term}`
   - Returns paginated list of panels

2. **Get Panel Details**
   - `GET /panels/{id}/`
   - Returns panel metadata including version, gene count

3. **Get Panel Genes**
   - `GET /panels/{id}/genes/`
   - Returns list of genes with confidence ratings
   - **Note:** May require additional calls for detailed gene data

**Confidence Ratings:**
- `green`: High confidence (diagnostic grade)
- `amber`: Moderate confidence
- `red`: Low confidence / under review

---

### Ensembl REST API

**Base URL (current):** `https://rest.ensembl.org/`
**Archive URLs:** `https://e{version}.rest.ensembl.org/` (e.g., `https://e109.rest.ensembl.org/`)

**Headers:**
```python
headers = {
    "Content-Type": "application/json"
}
```

**Rate Limiting:**
- 15 requests/second
- Implement 67ms delay between requests
- Respect `X-RateLimit-*` headers in responses

**Key Endpoints:**

1. **Lookup by Symbol**
   - `GET /lookup/symbol/homo_sapiens/{symbol}`
   - Params: `expand=1` for detailed info
   - Returns gene data including genomic location

2. **Lookup by ID**
   - `GET /lookup/id/{ensembl_id}`
   - Returns gene data

**Response Format:**
```json
{
  "id": "ENSG00000183873",
  "display_name": "SCN5A",
  "seq_region_name": "3",
  "start": 38548665,
  "end": 38649687,
  "strand": 1,
  "assembly_name": "GRCh38"
}
```

**GRCh38 Validation:**
- Always check `assembly_name` field
- Reject responses not using GRCh38

---

## UI/UX Design Specifications

### Stage 1: Selection Page

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  PanelChecker                                  [Help]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Step 1: Select Panel                                  │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Search panels: [________________] [🔍]          │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Available Panels:                                     │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ○ Cardiac arrhythmias (ID: 137, v3.45)          │  │
│  │   127 genes • Signed off                         │  │
│  ├─────────────────────────────────────────────────┤  │
│  │ ○ Familial hypercholesterolaemia (ID: 161...)   │  │
│  │   31 genes • Signed off                          │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Step 2: Select Ensembl Version                        │
│  Current Version: Ensembl 109 (auto-detected)         │
│  Target Version: [Ensembl 110 ▼]                      │
│                                                         │
│             [Analyze Panel →]                          │
└─────────────────────────────────────────────────────────┘
```

**Visual States:**
- Unselected panel: Light background, circle radio button
- Selected panel: Blue background, filled radio button
- Disabled button: Grey, cursor not-allowed
- Enabled button: Blue, cursor pointer

---

### Stage 2: Results Page

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  PanelChecker                    [Export CSV] [← Back]  │
├─────────────────────────────────────────────────────────┤
│  Panel: Cardiac arrhythmias (ID: 137, v3.45)           │
│  Comparison: Ensembl 109 → Ensembl 110                 │
│                                                         │
│  Summary: 127 genes analyzed                            │
│  ✓ 124 retained  ⚠ 2 changed  ✗ 1 missing             │
├─────────────────────────────────────────────────────────┤
│  Genes (showing 1-30 of 127)                           │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ✓ SCN5A          [Green]  Retained   [▼]        │  │
│  ├─────────────────────────────────────────────────┤  │
│  │ ⚠ KCNQ1          [Green]  Location changed [▼] │  │
│  │   Current: chr11:2,451,234-2,475,123            │  │
│  │   Target:  chr11:2,451,234-2,475,456 ← Changed │  │
│  ├─────────────────────────────────────────────────┤  │
│  │ ✗ GENEX          [Red]    Missing in target    │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│              [Load More Genes]                          │
└─────────────────────────────────────────────────────────┘
```

**Icons/Badges:**
- ✓ Green checkmark: Symbol retained, no location change
- ⚠ Orange warning: Symbol or location changed
- ✗ Red X: Gene missing in target version

**Color Coding:**
- Green badges: `#10b981` (emerald-500)
- Amber badges: `#f59e0b` (amber-500)
- Red badges: `#ef4444` (red-500)

---

## Error Handling

### API Errors

**PanelApp API Errors:**
- `429 Too Many Requests`: Show "Rate limit reached, retrying..." message
- `404 Not Found`: Show "Panel not found"
- `500 Server Error`: Show "PanelApp temporarily unavailable, please try again"
- Network timeout: Show "Connection timeout, check your internet"

**Ensembl API Errors:**
- `429 Too Many Requests`: Implement automatic retry with backoff
- `404 Not Found`: Mark gene as "Not found in this version"
- `400 Bad Request`: Log error, show generic "Unable to fetch gene data"

### User Input Validation

- Panel must be selected before proceeding
- Target Ensembl version must differ from current version
- Show inline validation errors with red text below inputs

### Graceful Degradation

- If some genes fail to fetch, show partial results with error note
- Allow CSV export of partial results
- Log all errors to Arize for debugging

---

## Testing Requirements

### Unit Tests

1. Rate limiter logic (RateLimiter class)
2. Data model validation (Pydantic models)
3. Gene comparison logic
4. CSV export formatting

### Integration Tests

1. PanelApp API connectivity (with mocked responses)
2. Ensembl API connectivity (with mocked responses)
3. Multi-agent workflow execution
4. End-to-end panel analysis flow

### Manual Testing Checklist

- [ ] Search for panel "Cardiac arrhythmias"
- [ ] Select panel and verify details display
- [ ] Select target Ensembl version
- [ ] Click "Analyze Panel" and verify loading state
- [ ] Verify first 30 genes display correctly
- [ ] Expand gene row and verify details
- [ ] Click "Load More" and verify next 30 genes load
- [ ] Verify Green/Amber/Red sorting order
- [ ] Export CSV and verify all columns present
- [ ] Verify filename format is correct
- [ ] Test with panel containing >100 genes
- [ ] Test with gene that doesn't exist in target version
- [ ] Test with gene that has location change

---

## Performance Requirements

### Response Times
- Panel list load: < 2 seconds
- First 30 gene analysis: < 10 seconds
- Additional 30 genes: < 5 seconds
- CSV export: < 3 seconds (for 200 genes)

### API Call Optimization
- Implement caching for panel metadata (1 hour TTL)
- Batch Ensembl requests where possible
- Use async/await for parallel agent execution
- Implement request deduplication

### Frontend Performance
- Lazy load gene details (only fetch on expand)
- Virtual scrolling for large gene lists (future enhancement)
- Debounce search input (300ms delay)

---

## Security & Compliance

### Data Privacy
- No personal health information (PHI) handled
- Gene data is public domain
- No user authentication required (internal tool)

### API Security
- Use HTTPS for all API calls
- Validate all responses before processing
- Sanitize user inputs (panel search)
- Rate limit frontend requests to prevent abuse

---

## Deployment Plan

### Phase 1: Development (Week 1)
- Set up PanelApp API client with rate limiting
- Implement data models
- Create basic frontend UI

### Phase 2: Integration (Week 2)
- Integrate Ensembl API client
- Implement multi-agent system
- Connect frontend to backend

### Phase 3: Testing (Week 3)
- Unit and integration tests
- Manual testing with real panels
- Performance optimization

### Phase 4: Deployment (Week 4)
- Deploy to staging environment
- User acceptance testing with curators
- Production deployment
- Documentation and training

---

## Dependencies & Prerequisites

### External APIs
- PanelApp API (public, no key required)
- Ensembl REST API (public, no key required)

### Infrastructure
- Existing FastAPI backend
- LangGraph multi-agent framework
- Arize observability (already configured)

### Development Dependencies
- Python 3.10+
- httpx (for async HTTP requests)
- pandas (for CSV export)
- All existing requirements from requirements.txt

---

## Open Questions & Decisions Needed

1. **Q:** Should we support archived Ensembl versions older than 6 months?
   **Decision Needed:** Yes/No and minimum version supported

2. **Q:** What happens if a panel has >500 genes?
   **Decision Needed:** Maximum genes per analysis or implement queue system

3. **Q:** Should we cache Ensembl responses?
   **Decision Needed:** Yes/No and cache duration

4. **Q:** Export format: Include gene descriptions?
   **Decision Needed:** Additional columns for CSV export

---

## Appendix

### Sample Panel IDs for Testing
- 137: Cardiac arrhythmias (127 genes)
- 161: Familial hypercholesterolaemia (31 genes)
- 3: Hearing loss (244 genes)

### Ensembl Version History
- 110: Latest (August 2023)
- 109: Previous (February 2023)
- 108: February 2022

### Useful Links
- PanelApp API Docs: https://panelapp.genomicsengland.co.uk/api/docs/
- Ensembl REST API Docs: https://rest.ensembl.org/documentation
- GRCh38 Reference: https://www.ncbi.nlm.nih.gov/assembly/GCF_000001405.26/

---

**Document Status:** Ready for Implementation  
**Next Steps:** Begin backend API integration and data model implementation


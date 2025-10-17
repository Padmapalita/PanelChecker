"""
PanelChecker - Genomics Reference Data Curation Tool
Backend API for comparing gene panel data across Ensembl versions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from collections import deque
import os
import time
import json
import csv
import io
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Minimal observability via Arize/OpenInference (optional)
try:
    from arize.otel import register
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from openinference.instrumentation.litellm import LiteLLMInstrumentor
    from openinference.instrumentation import using_prompt_template, using_metadata, using_attributes
    from opentelemetry import trace
    _TRACING = True
except Exception:
    def using_prompt_template(**kwargs):  # type: ignore
        from contextlib import contextmanager
        @contextmanager
        def _noop():
            yield
        return _noop()
    def using_metadata(*args, **kwargs):  # type: ignore
        from contextlib import contextmanager
        @contextmanager
        def _noop():
            yield
        return _noop()
    def using_attributes(*args, **kwargs):  # type: ignore
        from contextlib import contextmanager
        @contextmanager
        def _noop():
            yield
        return _noop()
    _TRACING = False

# LangGraph + LangChain
from langgraph.graph import StateGraph, END, START
from typing_extensions import TypedDict, Annotated
import operator
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import httpx
import asyncio


# =============================================================================
# DATA MODELS
# =============================================================================

class PanelSearchRequest(BaseModel):
    """Request model for searching panels"""
    search: Optional[str] = None
    signed_off_only: bool = True


class PanelInfo(BaseModel):
    """Panel metadata from PanelApp"""
    id: str
    name: str
    version: str
    gene_count: int
    signed_off: bool


class PanelListResponse(BaseModel):
    """Response model for panel list"""
    count: int
    panels: List[PanelInfo]


class PanelAnalysisRequest(BaseModel):
    """Request model for panel analysis"""
    panel_id: str
    panel_version: str
    current_ensembl_version: int = Field(..., ge=100, le=120)
    target_ensembl_version: int = Field(..., ge=100, le=120)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=30, ge=1, le=50)


class GenomicLocation(BaseModel):
    """Genomic location data for a gene"""
    ensembl_id: str
    gene_symbol: str
    chromosome: str
    start: int
    end: int
    strand: int


class GeneComparison(BaseModel):
    """Comparison of gene data between Ensembl versions"""
    gene_symbol: str
    confidence: Literal["green", "amber", "red"]
    symbol_retained: bool
    location_changed: bool
    ensembl_id_retained: bool
    current_version: Optional[GenomicLocation] = None
    target_version: Optional[GenomicLocation] = None
    status: Literal["retained", "changed", "missing"]


class AnalysisSummary(BaseModel):
    """Summary statistics for panel analysis"""
    symbols_retained: int
    symbols_changed: int
    locations_changed: int
    genes_missing: int


class PanelAnalysisResponse(BaseModel):
    """Response model for panel analysis"""
    panel_id: str
    panel_name: str
    total_genes: int
    genes_analyzed: int
    offset: int
    has_more: bool
    summary: AnalysisSummary
    genes: List[GeneComparison]


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, max_calls: int, window_seconds: int):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls: deque = deque()
    
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


# Global rate limiters
panelapp_limiter = RateLimiter(max_calls=60, window_seconds=60)
ensembl_limiter = RateLimiter(max_calls=15, window_seconds=1)


# =============================================================================
# API CLIENTS
# =============================================================================

class PanelAppClient:
    """Client for PanelApp API"""
    
    BASE_URL = "https://panelapp.genomicsengland.co.uk/api/v1"
    HEADERS = {
        "User-Agent": "KMDS-PdM",
        "Accept": "application/json"
    }
    
    async def search_panels(self, search: Optional[str] = None, signed_off_only: bool = True) -> List[PanelInfo]:
        """Search for panels"""
        panelapp_limiter.wait_if_needed()
        
        params = {}
        if search:
            params["search"] = search
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/panels/",
                headers=self.HEADERS,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            panels = []
            for panel_data in data.get("results", []):
                # Filter for signed off versions if requested
                if signed_off_only and not panel_data.get("version_signed_off"):
                    continue
                
                panels.append(PanelInfo(
                    id=str(panel_data["id"]),
                    name=panel_data["name"],
                    version=str(panel_data["version"]),
                    gene_count=panel_data.get("number_of_genes", 0),
                    signed_off=panel_data.get("version_signed_off", False)
                ))
            
            return panels
    
    async def get_panel_genes(self, panel_id: str) -> Dict[str, Any]:
        """Get genes for a specific panel"""
        panelapp_limiter.wait_if_needed()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/panels/{panel_id}/",
                headers=self.HEADERS,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()


class EnsemblClient:
    """Client for Ensembl REST API"""
    
    def __init__(self, version: Optional[int] = None):
        """Initialize Ensembl client for specific version
        
        Args:
            version: Ensembl version number (e.g., 109). None for latest.
        """
        if version:
            self.base_url = f"https://e{version}.rest.ensembl.org"
        else:
            self.base_url = "https://rest.ensembl.org"
        
        self.headers = {
            "Content-Type": "application/json"
        }
    
    async def lookup_gene_by_symbol(self, symbol: str) -> Optional[GenomicLocation]:
        """Look up gene by symbol"""
        ensembl_limiter.wait_if_needed()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/lookup/symbol/homo_sapiens/{symbol}",
                    headers=self.headers,
                    params={"expand": "1"},
                    timeout=10.0
                )
                
                if response.status_code == 404:
                    return None
                
                response.raise_for_status()
                data = response.json()
                
                # Validate GRCh38 assembly
                if data.get("assembly_name") != "GRCh38":
                    return None
                
                return GenomicLocation(
                    ensembl_id=data["id"],
                    gene_symbol=data.get("display_name", symbol),
                    chromosome=data["seq_region_name"],
                    start=data["start"],
                    end=data["end"],
                    strand=data["strand"]
                )
        except Exception as e:
            print(f"Error looking up gene {symbol}: {e}")
            return None
    
    async def lookup_gene_by_id(self, ensembl_id: str) -> Optional[GenomicLocation]:
        """Look up gene by Ensembl ID"""
        ensembl_limiter.wait_if_needed()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/lookup/id/{ensembl_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 404:
                    return None
                
                response.raise_for_status()
                data = response.json()
                
                # Validate GRCh38 assembly
                if data.get("assembly_name") != "GRCh38":
                    return None
                
                return GenomicLocation(
                    ensembl_id=data["id"],
                    gene_symbol=data.get("display_name", ""),
                    chromosome=data["seq_region_name"],
                    start=data["start"],
                    end=data["end"],
                    strand=data["strand"]
                )
        except Exception as e:
            print(f"Error looking up gene ID {ensembl_id}: {e}")
            return None


# =============================================================================
# LLM INITIALIZATION
# =============================================================================

def _init_llm():
    """Initialize LLM for agent reasoning"""
    class _Fake:
        def __init__(self):
            pass
        def bind_tools(self, tools):
            return self
        def invoke(self, messages):
            class _Msg:
                content = "Analysis complete"
                tool_calls: List[Dict[str, Any]] = []
            return _Msg()

    if os.getenv("TEST_MODE"):
        return _Fake()
    if os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, max_tokens=1500)
    elif os.getenv("OPENROUTER_API_KEY"):
        return ChatOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            temperature=0.7,
        )
    else:
        raise ValueError("Please set OPENAI_API_KEY or OPENROUTER_API_KEY in your .env")


llm = _init_llm()


# =============================================================================
# MULTI-AGENT STATE
# =============================================================================

class PanelCheckState(TypedDict):
    """State for panel checking workflow"""
    messages: Annotated[List[BaseMessage], operator.add]
    panel_request: Dict[str, Any]
    panel_data: Optional[Dict[str, Any]]
    current_ensembl_data: Optional[Dict[str, List[Optional[GenomicLocation]]]]
    target_ensembl_data: Optional[Dict[str, List[Optional[GenomicLocation]]]]
    comparison_results: Optional[List[GeneComparison]]
    final_report: Optional[str]
    tool_calls: Annotated[List[Dict[str, Any]], operator.add]


# =============================================================================
# TOOLS & AGENTS
# =============================================================================

@tool
async def fetch_panel_genes(panel_id: str) -> str:
    """Fetch genes for a panel from PanelApp"""
    client = PanelAppClient()
    panel_data = await client.get_panel_genes(panel_id)
    
    genes = panel_data.get("genes", [])
    gene_list = []
    for gene in genes:
        confidence = gene.get("confidence_level", "3")
        # Map confidence levels to colors
        if confidence == "3":
            color = "green"
        elif confidence == "2":
            color = "amber"
        else:
            color = "red"
        
        gene_list.append({
            "symbol": gene.get("gene_data", {}).get("gene_symbol", ""),
            "ensembl_id": gene.get("gene_data", {}).get("ensembl_id", ""),
            "confidence": color
        })
    
    return json.dumps({
        "panel_name": panel_data.get("name", ""),
        "version": panel_data.get("version", ""),
        "genes": gene_list
    })


@tool
async def fetch_ensembl_gene(gene_symbol: str, ensembl_version: int) -> str:
    """Fetch gene data from Ensembl for specific version"""
    client = EnsemblClient(version=ensembl_version)
    gene_data = await client.lookup_gene_by_symbol(gene_symbol)
    
    if gene_data is None:
        return json.dumps({"found": False, "gene_symbol": gene_symbol})
    
    return json.dumps({
        "found": True,
        "ensembl_id": gene_data.ensembl_id,
        "gene_symbol": gene_data.gene_symbol,
        "chromosome": gene_data.chromosome,
        "start": gene_data.start,
        "end": gene_data.end,
        "strand": gene_data.strand
    })


def compare_gene_data(current: Optional[GenomicLocation], target: Optional[GenomicLocation], confidence: str) -> GeneComparison:
    """Compare gene data between versions"""
    if current is None and target is None:
        # Should not happen, but handle gracefully
        return GeneComparison(
            gene_symbol="UNKNOWN",
            confidence=confidence,
            symbol_retained=False,
            location_changed=False,
            ensembl_id_retained=False,
            status="missing"
        )
    
    if current is None:
        # Gene only in target version (unusual)
        return GeneComparison(
            gene_symbol=target.gene_symbol,
            confidence=confidence,
            symbol_retained=False,
            location_changed=False,
            ensembl_id_retained=False,
            current_version=None,
            target_version=target,
            status="changed"
        )
    
    if target is None:
        # Gene missing in target version
        return GeneComparison(
            gene_symbol=current.gene_symbol,
            confidence=confidence,
            symbol_retained=False,
            location_changed=False,
            ensembl_id_retained=False,
            current_version=current,
            target_version=None,
            status="missing"
        )
    
    # Both versions present - compare
    symbol_retained = current.gene_symbol == target.gene_symbol
    ensembl_id_retained = current.ensembl_id == target.ensembl_id
    location_changed = (
        current.chromosome != target.chromosome or
        current.start != target.start or
        current.end != target.end or
        current.strand != target.strand
    )
    
    if symbol_retained and not location_changed:
        status = "retained"
    else:
        status = "changed"
    
    return GeneComparison(
        gene_symbol=current.gene_symbol,
        confidence=confidence,
        symbol_retained=symbol_retained,
        location_changed=location_changed,
        ensembl_id_retained=ensembl_id_retained,
        current_version=current,
        target_version=target,
        status=status
    )


# =============================================================================
# AGENT FUNCTIONS
# =============================================================================

async def panel_data_agent(state: PanelCheckState) -> PanelCheckState:
    """Agent that fetches panel data from PanelApp"""
    request = state["panel_request"]
    panel_id = request["panel_id"]
    
    # Fetch panel genes
    panel_json = await fetch_panel_genes.ainvoke({"panel_id": panel_id})
    panel_data = json.loads(panel_json)
    
    state["panel_data"] = panel_data
    state["messages"].append(HumanMessage(content=f"Fetched {len(panel_data['genes'])} genes from panel {panel_id}"))
    
    return state


async def current_ensembl_agent(state: PanelCheckState) -> PanelCheckState:
    """Agent that fetches current Ensembl data"""
    request = state["panel_request"]
    panel_data = state["panel_data"]
    current_version = request["current_ensembl_version"]
    
    client = EnsemblClient(version=current_version)
    
    # Fetch gene data for requested slice
    offset = request.get("offset", 0)
    limit = request.get("limit", 30)
    genes = panel_data["genes"][offset:offset + limit]
    
    current_data = {}
    for gene in genes:
        symbol = gene["symbol"]
        gene_data = await client.lookup_gene_by_symbol(symbol)
        current_data[symbol] = gene_data
    
    state["current_ensembl_data"] = current_data
    state["messages"].append(HumanMessage(content=f"Fetched current Ensembl data for {len(current_data)} genes"))
    
    return state


async def target_ensembl_agent(state: PanelCheckState) -> PanelCheckState:
    """Agent that fetches target Ensembl data"""
    request = state["panel_request"]
    panel_data = state["panel_data"]
    target_version = request["target_ensembl_version"]
    
    client = EnsemblClient(version=target_version)
    
    # Fetch gene data for requested slice
    offset = request.get("offset", 0)
    limit = request.get("limit", 30)
    genes = panel_data["genes"][offset:offset + limit]
    
    target_data = {}
    for gene in genes:
        symbol = gene["symbol"]
        gene_data = await client.lookup_gene_by_symbol(symbol)
        target_data[symbol] = gene_data
    
    state["target_ensembl_data"] = target_data
    state["messages"].append(HumanMessage(content=f"Fetched target Ensembl data for {len(target_data)} genes"))
    
    return state


async def comparison_agent(state: PanelCheckState) -> PanelCheckState:
    """Agent that compares gene data between versions"""
    panel_data = state["panel_data"]
    current_data = state["current_ensembl_data"]
    target_data = state["target_ensembl_data"]
    request = state["panel_request"]
    
    offset = request.get("offset", 0)
    limit = request.get("limit", 30)
    genes = panel_data["genes"][offset:offset + limit]
    
    comparisons = []
    for gene in genes:
        symbol = gene["symbol"]
        confidence = gene["confidence"]
        
        current_gene = current_data.get(symbol)
        target_gene = target_data.get(symbol)
        
        comparison = compare_gene_data(current_gene, target_gene, confidence)
        comparisons.append(comparison)
    
    state["comparison_results"] = comparisons
    state["messages"].append(HumanMessage(content=f"Compared {len(comparisons)} genes"))
    
    return state


async def synthesis_agent(state: PanelCheckState) -> PanelCheckState:
    """Agent that synthesizes final report"""
    comparisons = state["comparison_results"]
    
    # Calculate summary statistics
    symbols_retained = sum(1 for c in comparisons if c.symbol_retained)
    symbols_changed = sum(1 for c in comparisons if not c.symbol_retained and c.status != "missing")
    locations_changed = sum(1 for c in comparisons if c.location_changed)
    genes_missing = sum(1 for c in comparisons if c.status == "missing")
    
    summary = AnalysisSummary(
        symbols_retained=symbols_retained,
        symbols_changed=symbols_changed,
        locations_changed=locations_changed,
        genes_missing=genes_missing
    )
    
    state["final_report"] = summary.model_dump_json()
    state["messages"].append(HumanMessage(content="Analysis complete"))
    
    return state


# =============================================================================
# LANGGRAPH WORKFLOW
# =============================================================================

def build_panel_check_graph():
    """Build LangGraph workflow for panel checking"""
    g = StateGraph(PanelCheckState)
    
    # Add nodes
    g.add_node("panel_data", panel_data_agent)
    g.add_node("current_ensembl", current_ensembl_agent)
    g.add_node("target_ensembl", target_ensembl_agent)
    g.add_node("comparison", comparison_agent)
    g.add_node("synthesis", synthesis_agent)
    
    # Panel data must complete first
    g.add_edge(START, "panel_data")
    
    # Current and target Ensembl agents run in parallel after panel data
    g.add_edge("panel_data", "current_ensembl")
    g.add_edge("panel_data", "target_ensembl")
    
    # Comparison waits for both Ensembl agents
    g.add_edge("current_ensembl", "comparison")
    g.add_edge("target_ensembl", "comparison")
    
    # Synthesis is final step
    g.add_edge("comparison", "synthesis")
    g.add_edge("synthesis", END)
    
    return g.compile()


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(title="PanelChecker API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize tracing if available
if _TRACING:
    try:
        space_id = os.getenv("ARIZE_SPACE_ID")
        api_key = os.getenv("ARIZE_API_KEY")
        if space_id and api_key:
            tp = register(space_id=space_id, api_key=api_key, project_name="panel-checker")
            LangChainInstrumentor().instrument(tracer_provider=tp)
            LiteLLMInstrumentor().instrument(tracer_provider=tp, skip_dep_check=True)
    except Exception as e:
        print(f"Tracing initialization failed: {e}")


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "panel-checker"}


@app.get("/")
def serve_frontend():
    """Serve frontend HTML"""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "Frontend not found"}


@app.get("/api/panels", response_model=PanelListResponse)
async def search_panels(search: Optional[str] = None, signed_off_only: bool = True):
    """Search for panels in PanelApp"""
    try:
        client = PanelAppClient()
        panels = await client.search_panels(search=search, signed_off_only=signed_off_only)
        
        return PanelListResponse(
            count=len(panels),
            panels=panels
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching panels: {str(e)}")


@app.post("/api/analyze-panel", response_model=PanelAnalysisResponse)
async def analyze_panel(request: PanelAnalysisRequest):
    """Analyze a panel by comparing genes across Ensembl versions"""
    try:
        # Build and execute graph
        graph = build_panel_check_graph()
        
        initial_state = {
            "messages": [],
            "panel_request": request.model_dump(),
            "panel_data": None,
            "current_ensembl_data": None,
            "target_ensembl_data": None,
            "comparison_results": None,
            "final_report": None,
            "tool_calls": []
        }
        
        result = await graph.ainvoke(initial_state)
        
        # Extract results
        panel_data = result["panel_data"]
        comparisons = result["comparison_results"]
        summary_json = result["final_report"]
        summary = AnalysisSummary.model_validate_json(summary_json)
        
        # Calculate pagination
        total_genes = len(panel_data["genes"])
        genes_analyzed = len(comparisons)
        has_more = (request.offset + request.limit) < total_genes
        
        return PanelAnalysisResponse(
            panel_id=request.panel_id,
            panel_name=panel_data["panel_name"],
            total_genes=total_genes,
            genes_analyzed=genes_analyzed,
            offset=request.offset,
            has_more=has_more,
            summary=summary,
            genes=comparisons
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing panel: {str(e)}")


@app.get("/api/export-panel-csv")
async def export_panel_csv(
    panel_id: str,
    current_version: int,
    target_version: int
):
    """Export panel analysis results to CSV"""
    # TODO: Implement full CSV export
    # For now, return a placeholder
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Gene Symbol", "Confidence", "Symbol Retained", "Location Changed",
        "Current Ensembl ID", "Target Ensembl ID",
        "Current Chr", "Target Chr",
        "Current Start", "Target Start",
        "Current End", "Target End",
        "Current Strand", "Target Strand",
        "Status"
    ])
    
    output.seek(0)
    filename = f"PanelChecker_{panel_id}_{current_version}_vs_{target_version}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


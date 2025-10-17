# PanelChecker Quick Start Guide

## 🎉 Congratulations! Your genomics curation tool is ready!

---

## 🚀 What's Running

Your PanelChecker application is now live at:
- **Frontend UI:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 📋 Quick Test Steps

### 1. Open the Application
Open your browser and navigate to: **http://localhost:8000**

### 2. Search for a Panel
- In the search box, type: **"cardiac"** or **"cancer"**
- Click on any panel that appears (look for the green "Signed Off" badge)

### 3. Select Ensembl Versions
- **Current Version:** Keep as "Ensembl 109" (default)
- **Target Version:** Select "Ensembl 110"

### 4. Run Analysis
- Click the **"Analyze Panel"** button
- Wait 5-15 seconds for the analysis to complete

### 5. Review Results
- Check the summary statistics (Retained, Changed, Location Changed, Missing)
- Scroll through the gene list
- Click the expand arrow (▼) on any gene to see detailed coordinates
- Look for genes with changes (amber or red badges)

### 6. Load More Genes
- Click **"Load More Genes"** to fetch the next 30 genes
- Repeat until all genes are loaded

### 7. Export Results
- Click **"Export CSV"** button
- Open the downloaded CSV file in Excel or your preferred spreadsheet tool
- Review all gene comparisons

---

## 🧪 Recommended Test Panels

### Small Panel (Good for initial testing)
- **Search:** "Familial hypercholesterolaemia"
- **Genes:** ~30-50 genes
- **Test Time:** 5-10 seconds

### Medium Panel
- **Search:** "Cardiac arrhythmias"
- **Genes:** ~100-150 genes
- **Test Time:** 15-30 seconds

### Large Panel (Stress test)
- **Search:** "Hearing loss"
- **Genes:** 200+ genes
- **Test Time:** 45-90 seconds

---

## ✅ What to Look For

### Visual Indicators

**Green Badge + ✓ Icon:** Gene is retained
- Symbol unchanged
- Location unchanged
- Everything matches perfectly

**Amber Badge + ⚠ Icon:** Gene has changes
- Symbol might have changed OR
- Location coordinates changed
- Ensembl ID might have changed

**Red Badge + ✗ Icon:** Gene is missing
- Gene not found in target Ensembl version
- Requires curator attention

### Confidence Ratings

- **GREEN:** High confidence (diagnostic grade)
- **AMBER:** Moderate confidence
- **RED:** Low confidence or under review

---

## 📊 Understanding the Results

### Summary Statistics

**Symbols Retained:**
- Number of genes with unchanged symbol between versions

**Symbols Changed:**
- Number of genes where symbol differs (excluding missing genes)

**Locations Changed:**
- Number of genes where genomic coordinates differ
- Look for: chromosome, start position, end position, or strand changes

**Genes Missing:**
- Number of genes not found in the target version
- **Critical:** These require curator review before updating reference data

### Gene Details (Expanded View)

**Current Version:**
```
ENSG00000183873 • chr3:38,548,665-38,649,687 (+)
```

**Target Version:**
```
ENSG00000183873 • chr3:38,548,665-38,649,999 (+) ← Changed
```

**Orange text:** Indicates a difference detected

---

## 🐛 Troubleshooting

### "No panels found"
**Solution:** Check your internet connection and try again

### Analysis takes a long time
**Normal for:**
- Panels with 200+ genes
- First analysis (warming up API connections)

**Expected times:**
- 30 genes: 5-10 seconds
- 100 genes: 15-30 seconds
- 300 genes: 60-90 seconds

### CSV export fails or times out
**Solution:** 
- Try with a smaller panel first
- Very large panels (500+ genes) may take 2-3 minutes
- Check browser downloads folder

### Server not responding
**Check if running:**
```bash
curl http://localhost:8000/health
```

**Restart server:**
```bash
# Stop server
pkill -f "uvicorn main:app"

# Start server
cd "/Users/todddonnelly/AI courses/AI product playbook/Lesson 1 /Lesson 1 repo/PanelChecker"
./start.sh
```

---

## 📈 Example Workflow: Cardiac Arrhythmias Panel

1. **Search:** Type "cardiac"
2. **Select:** Click on "Cardiac arrhythmias" panel
3. **Configure:**
   - Current: Ensembl 109
   - Target: Ensembl 110
4. **Analyze:** Click "Analyze Panel" → Wait 15-20 seconds
5. **Review:** Check summary - expect mostly retained genes
6. **Investigate:** Expand any genes with "Changed" status
7. **Export:** Download CSV for team review
8. **Decision:** Curator decides if changes are acceptable for update

---

## 🎯 Success Criteria

Your implementation is working correctly if:

- ✅ Panels load from PanelApp
- ✅ Analysis completes without errors
- ✅ Results show a mix of green, amber, and red genes
- ✅ Expanding genes shows detailed coordinates
- ✅ "Load More" button fetches additional genes
- ✅ CSV export downloads successfully
- ✅ CSV contains all expected columns

---

## 📚 Next Steps

### For Curators
1. Test with your actual panels
2. Verify accuracy of change detection
3. Provide feedback on any issues
4. Document any missing features

### For Developers
1. Run full test suite (see IMPLEMENTATION_SUMMARY_Feature_1.md)
2. Performance test with large panels
3. Load test with concurrent users
4. Plan Feature 2 implementation

---

## 🔧 Advanced Testing

### Test Different Ensembl Versions
- Try: 108 → 109
- Try: 109 → 111
- Look for version-specific changes

### Test Edge Cases
- Panel with all green genes
- Panel with many missing genes
- Panel with location changes

### Test Pagination
- Load more genes multiple times
- Verify count updates correctly
- Verify "Load More" disappears when complete

---

## 📞 Need Help?

Check these resources:
1. **PRD:** `PRD_Feature_1_PanelApp_Integration.md`
2. **Implementation Details:** `IMPLEMENTATION_SUMMARY_Feature_1.md`
3. **Architecture:** `panelchecker-transformation-plan.plan.md`

---

## 🎊 Celebrate!

You've successfully transformed a trip planner into a genomics curation tool using:
- ✅ Multi-agent architecture (LangGraph)
- ✅ Real API integrations (PanelApp + Ensembl)
- ✅ Rate limiting (60/min, 15/sec)
- ✅ GRCh38 validation
- ✅ Pagination (30 genes/page)
- ✅ CSV export
- ✅ Modern responsive UI
- ✅ Observability (Arize)

**Ready to test with real data!** 🧬🔬


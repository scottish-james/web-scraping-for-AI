# NatWest Content Scraper & Analyser

A comprehensive Python toolkit for discovering, scraping, cleaning, and analysing corporate website content. Transforms complex web architectures into clean, structured markdown whilst providing detailed analytical insights into site structure, content patterns, and update histories.

## Executive Summary

This toolkit provides an end-to-end solution for converting web content into high-quality, structured data suitable for business intelligence, AI knowledge bases, and content analysis. It handles JavaScript-rendered pages, removes duplicates, and produces clean markdown files whilst generating comprehensive analytics about website structure and content evolution.

## Business Applications

### AI & Machine Learning
- **Knowledge Base Construction**: Creates clean, structured content for AI systems to process and understand
- **RAG Systems**: Generates high-quality documents for Retrieval-Augmented Generation pipelines
- **Training Data**: Produces consistent markdown for fine-tuning language models on domain-specific content
- **Vector Databases**: Delivers uniform content chunks ideal for embedding and semantic search

### Business Intelligence
- **Content Auditing**: Systematic analysis of website content quality and structure
- **Update Pattern Analysis**: Tracks when and where content changes occur across the site
- **Site Architecture Insights**: Visual and statistical analysis of website organisation
- **Content Type Classification**: Automated categorisation of pages by purpose and content type

## Technical Components

### 1. Sitemap Discovery (`sitemap.py`)
Downloads and parses complete website sitemaps into structured CSV/Excel files, extracting URLs, last modified dates, change frequencies, and priorities.

### 2. Web Scraping Engine (`scrap_30_pages_test.py`)
- Captures fully-rendered pages using headless Chrome with Selenium
- Handles JavaScript-generated content that traditional scrapers miss
- Parallel processing for efficient large-scale scraping
- Automatic cleaning of navigation, headers, and footers
- Converts relative URLs to absolute for proper linking

### 3. Content Deduplication System (`content_cleanup.py`)
- Detects exact content duplicates using hash-based comparison
- Validates URLs and identifies redirects
- Removes broken links and network errors
- Generates comprehensive reports on content quality
- Outputs categorised file lists for selective processing

### 4. Footer Cleaning Module (`clean_foot.py`)
- Removes legal disclaimers and boilerplate text
- Strips feedback sections and repetitive content
- Preserves core informational content
- Creates backups before modification

### 5. Domain Analysis Suite (`natwest_domain_analysis_cleared.py`)
Comprehensive analytical notebook providing:
- **Temporal Analysis**: Page update timelines and patterns
- **Structural Analysis**: URL depth distribution and site architecture
- **Content Classification**: Automated content type detection
- **Section Analysis**: Breakdown by website areas (support centre, corporate, etc.)
- **Visual Analytics**: Interactive charts, heatmaps, and network visualisations
- **Cross-Reference Analysis**: Correlates update patterns with site sections

## Implementation Guide

### Prerequisites
```bash
pip install selenium webdriver-manager beautifulsoup4 markitdown pandas requests tqdm
pip install matplotlib seaborn networkx plotly  # For analysis notebook
```

### Standard Workflow

#### Phase 1: Discovery
```bash
# Download and parse sitemap
python sitemap.py
# Output: natwest_sitemap.csv, natwest_sitemap.xlsx
```

#### Phase 2: Content Extraction
```bash
# Scrape sample pages (30 random URLs)
python scrap_30_pages_test.py
# Output: natwest_markdown/ directory with .md files
```

#### Phase 3: Quality Control
```bash
# Remove duplicates and validate URLs
python content_cleanup.py natwest_markdown --output-dir dedup_output

# Clean footer disclaimers
python clean_foot.py ./dedup_output/cleaned_files --clean
```

#### Phase 4: Analysis
```python
# Run the analysis notebook
# Provides comprehensive insights into site structure and content patterns
jupyter notebook natwest_domain_analysis_cleared.ipynb
```

## Output Structure

```
project/
├── natwest_sitemap.csv           # Complete sitemap data
├── natwest_sitemap.xlsx          # Excel version for business users
├── natwest_markdown/              # Raw scraped content
│   ├── page_1_*.md
│   ├── page_2_*.md
│   └── summary.md
├── dedup_output/                  # Processed content
│   ├── cleaned_files/             # Deduplicated, cleaned markdown
│   ├── reports/                   # Analysis reports
│   │   ├── summary_report.txt
│   │   ├── file_metadata.csv
│   │   └── url_validation.csv
│   ├── lists/                     # Categorised file lists
│   │   ├── files_to_keep.txt
│   │   ├── duplicate_content.txt
│   │   └── broken_urls.txt
│   └── deduplication.log
└── analysis_outputs/              # Charts and visualisations
```

## Key Features

### Data Quality
- **JavaScript Rendering**: Captures dynamic content for complete data extraction
- **Intelligent Content Cleaning**: Removes navigation, footers, and legal boilerplate automatically
- **Deduplication**: Eliminates redundant content for cleaner datasets
- **URL Validation**: Identifies and reports broken links and redirects

### Scalability
- **Parallel Processing**: Handles thousands of pages efficiently
- **Configurable Workers**: Adjustable concurrency for different server loads
- **Rate Limiting**: Respects server resources with configurable delays
- **Progress Tracking**: Real-time feedback on processing status

### Analytics Capabilities
- **Temporal Patterns**: Identifies when different site sections are updated
- **Structural Insights**: Maps site architecture and content organisation
- **Content Classification**: Automatically categorises page types
- **Visual Reporting**: Generates charts, heatmaps, and network graphs

## Performance Metrics

Based on analysis of NatWest's corporate website:
- Successfully processed 30+ pages with parallel execution
- Identified and removed duplicate content groups
- Validated URLs with redirect detection
- Generated comprehensive analytical reports
- Created clean markdown suitable for AI processing

## Configuration Options

### Content Cleanup Parameters
```python
ProcessingConfig(
    source_dir="natwest_markdown",
    output_dir="dedup_output",
    min_content_length=100,        # Minimum chars to process
    similarity_threshold=0.85,      # Duplicate detection threshold
    max_workers=8,                  # Parallel processing threads
    request_delay=2.0,              # Seconds between requests
    request_timeout=15              # Request timeout seconds
)
```

### Scraping Configuration
- Headless Chrome with configurable window size
- JavaScript execution wait times
- Scroll behaviour for lazy-loaded content
- Custom user agent strings

## Technical Architecture

### Core Technologies
- **Selenium WebDriver**: JavaScript rendering and dynamic content capture
- **BeautifulSoup**: HTML parsing and cleaning
- **MarkItDown**: Microsoft's library for HTML to Markdown conversion
- **Pandas**: Data manipulation and analysis
- **NetworkX**: Graph-based site structure analysis
- **Plotly**: Interactive visualisations

### Design Principles
- **Modular Architecture**: Independent components for flexibility
- **Error Resilience**: Comprehensive exception handling
- **Audit Trail**: Detailed logging at every stage
- **Data Integrity**: Validation at each processing step

## Future Enhancements

- Content change detection between scraping runs
- Natural language processing for content summarisation
- API integration for real-time content monitoring
- Machine learning-based content classification
- Automated quality scoring algorithms

## Compliance & Best Practices

- Respects robots.txt directives
- Implements rate limiting to avoid server overload
- Maintains detailed logs for audit purposes
- Creates backups before destructive operations
- Follows web scraping ethical guidelines

---

*Developed as a comprehensive solution for transforming web content into structured, analysis-ready data suitable for enterprise AI and business intelligence applications.*
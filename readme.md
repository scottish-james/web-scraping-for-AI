# NatWest Content Scraper & Analyser

A Python toolkit for scraping, cleaning, and analysing content from NatWest's corporate website. Handles JavaScript-rendered pages, removes duplicates, and produces clean markdown files for business intelligence.

## 🎯 Why It's Valuable

**Perfect for AI Knowledge Bases**: Converts complex web content into clean, structured markdown that AI systems can effectively process and understand.

**High-Quality Data**: Removes boilerplate, disclaimers, and navigation clutter to create focused content that improves AI training and retrieval accuracy.

**Scale & Efficiency**: Systematically processes thousands of pages into consistent markdown format, creating comprehensive knowledge bases from any website.

## 🛠️ Components

**Sitemap Discovery** (`sitemap.py`): Downloads and parses NatWest's complete sitemap into structured CSV/Excel files.

**Web Scraping** (`scrap_30_pages_test.py`): Captures fully-rendered pages using headless Chrome with parallel processing and automatic content cleaning.

**Content Deduplication** (`content_cleanup.py`): Detects exact duplicates, validates URLs, removes broken links, and generates comprehensive reports.

**Footer Cleaning** (`clean_foot.py`): Removes legal disclaimers and feedback forms whilst preserving core content.

## 🚀 Quick Start

```bash
# Install dependencies
pip install selenium webdriver-manager beautifulsoup4 markitdown pandas requests tqdm

# 1. Discover content
python sitemap.py

# 2. Scrape sample pages
python scrap_30_pages_test.py

# 3. Remove duplicates
python content_cleanup.py natwest_markdown --output-dir dedup_output

# 4. Clean disclaimers
python clean_foot.py ./dedup_output/cleaned_files --clean
```

## 📊 Output

**Organised Structure**: Clean markdown files, detailed analytics, duplicate reports, and categorised file lists.

**Business Intelligence**: Content quality metrics, section analysis, URL validation results, and comprehensive audit trails.

**Production Ready**: Files with proper metadata, absolute URLs, stripped boilerplate, and consistent formatting.

## 💼 AI Knowledge Base Applications

**Training Data**: Creates clean, consistent markdown perfect for fine-tuning language models on domain-specific content.

**RAG Systems**: Generates high-quality documents for Retrieval-Augmented Generation pipelines with proper structure and metadata.

**Vector Databases**: Produces uniform content chunks ideal for embedding and semantic search applications.

**Content Analysis**: Enables systematic analysis of messaging, tone, and information architecture for AI-powered insights.

## 🔧 Key Features

- **JavaScript Rendering**: Captures dynamic content for complete data extraction
- **Smart Content Cleaning**: Removes navigation, footers, and legal boilerplate automatically  
- **Deduplication**: Eliminates redundant content for cleaner knowledge bases
- **Markdown Optimisation**: Produces AI-friendly structured text with consistent formatting
- **Scalable Processing**: Handles thousands of pages efficiently with parallel processing

---

*Convert any website into clean, AI-ready markdown for superior knowledge base construction.*
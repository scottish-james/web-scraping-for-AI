#!/usr/bin/env python3
"""
Content Deduplication System
============================

Detects and removes duplicate content from scraped markdown files.
Includes URL validation, redirect detection, and content normalization.

Handles the common case where broken links redirect to section home pages,
creating numerous duplicates of the same landing page content.
"""

import os
import sys
import logging
import hashlib
import re
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, Counter
import argparse

import pandas as pd
import requests
from tqdm import tqdm


@dataclass
class ProcessingConfig:
    """Configuration settings for the deduplication pipeline."""
    source_dir: str
    output_dir: str
    min_content_length: int = 100
    similarity_threshold: float = 0.85
    max_workers: int = 8
    request_delay: float = 2.0
    request_timeout: int = 15
    max_retries: int = 3
    content_marker: str = "### Didn't find what you were looking for?"
    backup_original: bool = True

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class FileMetadata:
    """File analysis results and extracted metadata."""
    filename: str
    filepath: str
    url: str
    content_length: int
    word_count: int
    line_count: int
    content_hash: str
    url_depth: int
    url_section: str


@dataclass
class URLCheckResult:
    """Results from URL validation and redirect detection."""
    filename: str
    original_url: str
    final_url: Optional[str]
    status_code: Optional[int]
    is_redirect: bool
    error: Optional[str]
    retry_count: int = 0


class ContentDeduplicationSystem:
    """Core system for analyzing and removing duplicate scraped content."""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.ensure_output_directory()  # Create directories first
        self.logger = self._setup_logging()  # Then setup logging

    def _setup_logging(self) -> logging.Logger:
        """Configure logging with both console and file output."""
        logger = logging.getLogger('content_dedup')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

            # File handler
            log_file = Path(self.config.output_dir) / 'deduplication.log'
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        return logger

    def ensure_output_directory(self):
        """Create organized directory structure for outputs and reports."""
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        subdirs = ['cleaned_files', 'reports', 'lists', 'backups']
        for subdir in subdirs:
            (output_path / subdir).mkdir(exist_ok=True)

    def load_markdown_files(self) -> List[FileMetadata]:
        """Load all markdown files and extract content metadata."""
        self.logger.info(f"Loading markdown files from: {self.config.source_dir}")

        source_path = Path(self.config.source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {self.config.source_dir}")

        files_metadata = []
        markdown_files = list(source_path.glob("*.md"))

        self.logger.info(f"Found {len(markdown_files)} markdown files")

        for file_path in tqdm(markdown_files, desc="Loading files"):
            try:
                metadata = self._process_single_file(file_path)
                if metadata:
                    files_metadata.append(metadata)
            except Exception as e:
                self.logger.error(f"Error processing {file_path.name}: {e}")

        self.logger.info(f"Successfully loaded {len(files_metadata)} files")
        return files_metadata

    def _process_single_file(self, file_path: Path) -> Optional[FileMetadata]:
        """Extract metadata from a single markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Skip files that are too short
            if len(content) < self.config.min_content_length:
                return None

            # Extract URL from filename or content
            url = self._extract_url_from_file(file_path, content)

            # Generate content hash
            cleaned_content = self._clean_content_for_hashing(content)
            content_hash = hashlib.md5(cleaned_content.encode()).hexdigest()

            # Analyze URL structure
            url_components = self._extract_url_components(url)

            return FileMetadata(
                filename=file_path.name,
                filepath=str(file_path),
                url=url,
                content_length=len(content),
                word_count=len(content.split()),
                line_count=content.count('\n'),
                content_hash=content_hash,
                url_depth=url_components['depth'],
                url_section=url_components['section']
            )

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return None

    def _extract_url_from_file(self, file_path: Path, content: str) -> str:
        """Extract the source URL from filename or file header."""
        # Try to extract from filename first
        filename = file_path.name
        url_match = re.search(r'https?://[^.]+', filename)
        if url_match:
            return url_match.group()

        # Try to extract from content (look for Source: line)
        for line in content.split('\n')[:10]:
            if line.strip().startswith('# Source:'):
                url_match = re.search(r'https?://[^\s\)]+', line)
                if url_match:
                    return url_match.group().rstrip('.')

        return "unknown"

    def _clean_content_for_hashing(self, content: str) -> str:
        """Normalize content to improve duplicate detection accuracy."""
        # Remove content after marker
        if self.config.content_marker in content:
            content = content[:content.find(self.config.content_marker)]

        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', content.strip())

        # Remove markdown heading markers
        cleaned = re.sub(r'#+ ', '', cleaned)

        # Remove image references
        image_patterns = [
            r'!\[.*?\]\([^)]*\.(png|jpg|jpeg|gif|svg|webp|bmp|ico)[^)]*\)',
            r'!\[\]\([^)]*\.(png|jpg|jpeg|gif|svg|webp|bmp|ico)[^)]*\)'
        ]
        for pattern in image_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        return cleaned.lower()

    def _extract_url_components(self, url: str) -> Dict:
        """Parse URL into components for pattern analysis."""
        if url == "unknown":
            return {'depth': 0, 'section': 'unknown', 'segments': []}

        # Remove domain
        path = re.sub(r'https?://[^/]+', '', url)
        segments = [s for s in path.split('/') if s]

        return {
            'path': path,
            'segments': segments,
            'depth': len(segments),
            'section': segments[0] if segments else 'root'
        }

    def find_exact_duplicates(self, files_metadata: List[FileMetadata]) -> Dict[str, List[str]]:
        """Group files by identical content hash."""
        self.logger.info("Detecting exact content duplicates")

        hash_groups = defaultdict(list)
        for file_meta in files_metadata:
            hash_groups[file_meta.content_hash].append(file_meta.filename)

        # Only return groups with multiple files
        duplicates = {h: files for h, files in hash_groups.items() if len(files) > 1}

        total_dupes = sum(len(files) - 1 for files in duplicates.values())
        self.logger.info(f"Found {len(duplicates)} duplicate groups, {total_dupes} redundant files")

        return duplicates

    def validate_urls(self, files_metadata: List[FileMetadata]) -> List[URLCheckResult]:
        """Check URLs for redirects and broken links with rate limiting."""
        self.logger.info(f"Validating {len(files_metadata)} URLs")

        def check_single_url(file_meta: FileMetadata) -> URLCheckResult:
            """Check a single URL with retry logic."""
            if file_meta.url == "unknown":
                return URLCheckResult(
                    filename=file_meta.filename,
                    original_url=file_meta.url,
                    final_url=None,
                    status_code=None,
                    is_redirect=False,
                    error="No URL found"
                )

            for attempt in range(self.config.max_retries):
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (compatible; ContentAnalyzer/1.0)',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    }

                    response = requests.head(
                        file_meta.url,
                        timeout=self.config.request_timeout,
                        allow_redirects=True,
                        headers=headers
                    )

                    # Fallback to GET if HEAD fails
                    if response.status_code >= 400:
                        response = requests.get(
                            file_meta.url,
                            timeout=self.config.request_timeout,
                            allow_redirects=True,
                            headers=headers
                        )

                    final_url = response.url
                    is_redirect = file_meta.url != final_url

                    # Rate limiting
                    time.sleep(self.config.request_delay)

                    return URLCheckResult(
                        filename=file_meta.filename,
                        original_url=file_meta.url,
                        final_url=final_url,
                        status_code=response.status_code,
                        is_redirect=is_redirect,
                        error=None,
                        retry_count=attempt
                    )

                except requests.exceptions.Timeout:
                    error = "Request timeout"
                except requests.exceptions.ConnectionError:
                    error = "Connection failed"
                except Exception as e:
                    error = f"Request error: {str(e)}"

                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.request_delay * (2 ** attempt))

            return URLCheckResult(
                filename=file_meta.filename,
                original_url=file_meta.url,
                final_url=None,
                status_code=None,
                is_redirect=False,
                error=error,
                retry_count=self.config.max_retries
            )

        # Execute with threading and progress bar
        results = []
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_meta = {
                executor.submit(check_single_url, meta): meta
                for meta in files_metadata
            }

            for future in tqdm(as_completed(future_to_meta), total=len(files_metadata), desc="Checking URLs"):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    meta = future_to_meta[future]
                    self.logger.error(f"URL check failed for {meta.filename}: {e}")
                    results.append(URLCheckResult(
                        filename=meta.filename,
                        original_url=meta.url,
                        final_url=None,
                        status_code=None,
                        is_redirect=False,
                        error=f"Processing error: {str(e)}"
                    ))

        return results

    def clean_content_files(self, keep_files: Set[str]) -> Dict[str, int]:
        """Clean and copy files that should be kept."""
        self.logger.info(f"Cleaning {len(keep_files)} files")

        source_path = Path(self.config.source_dir)
        target_path = Path(self.config.output_dir) / 'cleaned_files'

        stats = {'processed': 0, 'cleaned': 0, 'chars_removed': 0}

        for filename in tqdm(keep_files, desc="Cleaning files"):
            source_file = source_path / filename
            target_file = target_path / filename

            if not source_file.exists():
                self.logger.warning(f"Source file not found: {filename}")
                continue

            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_length = len(content)

                # Remove content after marker
                if self.config.content_marker in content:
                    content = content[:content.find(self.config.content_marker)].strip()
                    stats['cleaned'] += 1

                # Remove images
                image_patterns = [
                    r'!\[.*?\]\([^)]*\.(png|jpg|jpeg|gif|svg|webp|bmp|ico)[^)]*\)',
                    r'!\[\]\([^)]*\.(png|jpg|jpeg|gif|svg|webp|bmp|ico)[^)]*\)'
                ]
                for pattern in image_patterns:
                    content = re.sub(pattern, '', content, flags=re.IGNORECASE)

                # Clean up extra whitespace
                content = re.sub(r'\n\n+', '\n\n', content)

                stats['chars_removed'] += original_length - len(content)

                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                stats['processed'] += 1

            except Exception as e:
                self.logger.error(f"Error cleaning {filename}: {e}")

        return stats

    def generate_reports(self, files_metadata: List[FileMetadata],
                         duplicates: Dict[str, List[str]],
                         url_results: List[URLCheckResult]) -> Dict[str, str]:
        """Generate analysis reports and file lists."""
        self.logger.info("Generating reports and file lists")

        reports_dir = Path(self.config.output_dir) / 'reports'
        lists_dir = Path(self.config.output_dir) / 'lists'

        # Convert to DataFrames for analysis
        df_files = pd.DataFrame([asdict(meta) for meta in files_metadata])
        df_urls = pd.DataFrame([asdict(result) for result in url_results])

        # Generate summary report
        summary_report = self._generate_summary_report(df_files, duplicates, df_urls)
        with open(reports_dir / 'summary_report.txt', 'w') as f:
            f.write(summary_report)

        # Generate detailed CSV reports
        df_files.to_csv(reports_dir / 'file_metadata.csv', index=False)
        df_urls.to_csv(reports_dir / 'url_validation.csv', index=False)

        # Generate removal lists
        removal_lists = self._generate_removal_lists(df_urls, duplicates)

        for list_name, filenames in removal_lists.items():
            with open(lists_dir / f'{list_name}.txt', 'w') as f:
                f.write('\n'.join(filenames))

        # Determine files to keep
        all_files = set(meta.filename for meta in files_metadata)
        all_removals = set()
        for filenames in removal_lists.values():
            all_removals.update(filenames)

        keep_files = all_files - all_removals
        with open(lists_dir / 'files_to_keep.txt', 'w') as f:
            f.write('\n'.join(sorted(keep_files)))

        return {
            'summary_report': str(reports_dir / 'summary_report.txt'),
            'keep_files': keep_files
        }

    def _generate_summary_report(self, df_files: pd.DataFrame,
                                 duplicates: Dict[str, List[str]],
                                 df_urls: pd.DataFrame) -> str:
        """Generate a human-readable summary report."""
        total_files = len(df_files)
        duplicate_files = sum(len(files) - 1 for files in duplicates.values())

        broken_urls = len(df_urls[df_urls['status_code'] >= 400])
        redirected_urls = len(df_urls[df_urls['is_redirect'] == True])
        error_urls = len(df_urls[df_urls['error'].notna()])

        report = f"""Content Deduplication Analysis Report
=========================================

Dataset Overview:
- Total files analyzed: {total_files:,}
- Average content length: {df_files['content_length'].mean():.0f} characters
- Content size range: {df_files['content_length'].min():,} - {df_files['content_length'].max():,} characters

Duplicate Content:
- Duplicate groups found: {len(duplicates)}
- Redundant files: {duplicate_files:,} ({duplicate_files / total_files * 100:.1f}%)
- Unique content files: {total_files - duplicate_files:,}

URL Validation:
- Broken URLs (4xx/5xx): {broken_urls:,}
- Redirected URLs: {redirected_urls:,}
- Network errors: {error_urls:,}

Content Sections:
"""

        # Add section breakdown
        section_stats = df_files.groupby('url_section').agg({
            'filename': 'count',
            'content_length': 'mean'
        }).round(0)

        for section, stats in section_stats.head(10).iterrows():
            report += f"- {section}: {stats['filename']} files (avg {stats['content_length']:.0f} chars)\n"

        return report

    def _generate_removal_lists(self, df_urls: pd.DataFrame,
                                duplicates: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Generate categorized lists of files to remove."""
        lists = {}

        # Broken URLs
        broken = df_urls[df_urls['status_code'] >= 400]['filename'].tolist()
        lists['broken_urls'] = broken

        # Redirected URLs
        redirected = df_urls[df_urls['is_redirect'] == True]['filename'].tolist()
        lists['redirected_urls'] = redirected

        # Network errors
        errors = df_urls[df_urls['error'].notna()]['filename'].tolist()
        lists['network_errors'] = errors

        # Duplicate content (keep first, remove rest)
        duplicate_removals = []
        for files in duplicates.values():
            duplicate_removals.extend(files[1:])  # Keep first, remove rest
        lists['duplicate_content'] = duplicate_removals

        return lists

    def run_full_analysis(self) -> Dict:
        """Execute complete deduplication analysis pipeline."""
        self.logger.info("Starting complete deduplication analysis")

        # Save configuration
        config_file = Path(self.config.output_dir) / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)

        # Load and analyze files
        files_metadata = self.load_markdown_files()

        # Find duplicates
        duplicates = self.find_exact_duplicates(files_metadata)

        # Validate URLs
        url_results = self.validate_urls(files_metadata)

        # Generate reports
        reports = self.generate_reports(files_metadata, duplicates, url_results)

        # Clean files
        cleaning_stats = self.clean_content_files(reports['keep_files'])

        self.logger.info("Analysis complete")

        return {
            'total_files': len(files_metadata),
            'duplicates_found': len(duplicates),
            'files_to_keep': len(reports['keep_files']),
            'cleaning_stats': cleaning_stats,
            'reports_generated': reports['summary_report']
        }


def create_config_from_args() -> ProcessingConfig:
    """Parse command line arguments and create configuration."""
    parser = argparse.ArgumentParser(description='Content deduplication analysis')
    parser.add_argument('source_dir', help='Directory containing markdown files')
    parser.add_argument('--output-dir', default='dedup_output',
                        help='Output directory for results')
    parser.add_argument('--min-length', type=int, default=100,
                        help='Minimum content length to analyze')
    parser.add_argument('--workers', type=int, default=8,
                        help='Number of concurrent workers for URL validation')
    parser.add_argument('--delay', type=float, default=2.0,
                        help='Delay between requests (seconds)')
    parser.add_argument('--no-backup', action='store_true',
                        help='Skip backing up original files')

    args = parser.parse_args()

    return ProcessingConfig(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        min_content_length=args.min_length,
        max_workers=args.workers,
        request_delay=args.delay,
        backup_original=not args.no_backup
    )


def main():
    """Main entry point."""
    try:
        config = create_config_from_args()
        system = ContentDeduplicationSystem(config)
        results = system.run_full_analysis()

        print("\n=== Analysis Complete ===")
        print(f"Files analyzed: {results['total_files']:,}")
        print(f"Duplicate groups: {results['duplicates_found']:,}")
        print(f"Files to keep: {results['files_to_keep']:,}")
        print(f"Files cleaned: {results['cleaning_stats']['processed']:,}")
        print(f"Characters removed: {results['cleaning_stats']['chars_removed']:,}")
        print(f"\nReports saved to: {config.output_dir}")

    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
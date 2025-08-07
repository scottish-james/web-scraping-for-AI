#!/usr/bin/env python3
"""
Footer Cleaner for Cleaned Files
=================================

Removes legal disclaimer text and everything after it from cleaned markdown files.
Specifically targets the NatWest disclaimer text that appears at the end of articles.
"""

import os

from pathlib import Path
from typing import Dict, List, Tuple
import argparse
from tqdm import tqdm


class FooterCleaner:
    """Removes footer disclaimers from cleaned markdown files."""

    def __init__(self, source_dir: str, backup: bool = True):
        self.source_dir = Path(source_dir)
        self.backup = backup

        # Footer patterns to remove (including everything after them)
        self.footer_patterns = [
            # Original disclaimer (exact match)
            "This article has been prepared for information purposes only, does not constitute an analysis of all potentially material issues and is subject to change at any time without prior notice.",

            # Disclaimer variations (different formatting/spacing)
            "This article has been prepared for information purposes only, does not constitute an analysis of all potentially material issues and is subject to change at any time without prior notice",
            # No period
            "This article has been prepared for information purposes only and does not constitute an analysis of all potentially material issues and is subject to change at any time without prior notice.",
            # With "and"
            "This article has been prepared for information purposes only and does not constitute an analysis of all potentially material issues and is subject to change at any time without prior notice",
            # With "and", no period

            # Feedback section patterns
            "**Did you find this article helpful?**",
            "Did you find this article helpful?",
            "**Did you find this article helpful?**\nYes\nNo",
            "Great, thank you for your feedback"
        ]

        # Stats tracking
        self.stats = {
            'files_processed': 0,
            'files_cleaned': 0,
            'chars_removed': 0,
            'patterns_found': {pattern[:50] + "..." if len(pattern) > 50 else pattern: 0 for pattern in
                               self.footer_patterns}
        }

    def clean_single_file(self, file_path: Path) -> Tuple[bool, int]:
        """
        Clean a single file by removing footer patterns and everything after them.

        Returns:
            (was_cleaned, chars_removed)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            cleaned_content = original_content
            total_chars_removed = 0
            was_cleaned = False

            # Check each footer pattern
            for pattern in self.footer_patterns:
                if pattern in cleaned_content:
                    # Find the earliest occurrence of any pattern
                    pattern_index = cleaned_content.find(pattern)

                    # Cut everything from that point onward
                    before_cleaning = len(cleaned_content)
                    cleaned_content = cleaned_content[:pattern_index].strip()
                    chars_removed_this_pattern = before_cleaning - len(cleaned_content)

                    if chars_removed_this_pattern > 0:
                        total_chars_removed += chars_removed_this_pattern
                        was_cleaned = True

                        # Track which pattern was found
                        pattern_key = pattern[:50] + "..." if len(pattern) > 50 else pattern
                        self.stats['patterns_found'][pattern_key] += 1

                        # Break after first match to avoid double-processing
                        break

            # Only write file if it was actually changed
            if was_cleaned:
                # Create backup if requested
                if self.backup:
                    backup_path = file_path.with_suffix('.backup.md')
                    if not backup_path.exists():  # Don't overwrite existing backups
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            f.write(original_content)

                # Write cleaned content back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)

            return was_cleaned, total_chars_removed

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            return False, 0

    def clean_directory(self) -> Dict:
        """Clean all markdown files in the source directory."""

        if not self.source_dir.exists():
            raise FileNotFoundError(f"Directory not found: {self.source_dir}")

        # Find all markdown files
        md_files = list(self.source_dir.glob("*.md"))

        if not md_files:
            print(f"No markdown files found in {self.source_dir}")
            return self.stats

        print(f"🧹 Cleaning {len(md_files)} markdown files...")
        print(f"📁 Source directory: {self.source_dir}")
        print(f"🎯 Looking for {len(self.footer_patterns)} footer patterns:")
        for i, pattern in enumerate(self.footer_patterns, 1):
            preview = pattern[:60] + "..." if len(pattern) > 60 else pattern
            print(f"   {i}. '{preview}'")
        print(f"💾 Backup enabled: {self.backup}")
        print("-" * 60)

        # Process each file
        for file_path in tqdm(md_files, desc="Cleaning files"):
            self.stats['files_processed'] += 1

            was_cleaned, chars_removed = self.clean_single_file(file_path)

            if was_cleaned:
                self.stats['files_cleaned'] += 1
                self.stats['chars_removed'] += chars_removed

        return self.stats

    def print_summary(self):
        """Print a summary of the cleaning operation."""
        print("\n" + "=" * 60)
        print("FOOTER CLEANING SUMMARY")
        print("=" * 60)
        print(f"Files processed: {self.stats['files_processed']:,}")
        print(f"Files cleaned: {self.stats['files_cleaned']:,}")
        print(f"Characters removed: {self.stats['chars_removed']:,}")

        if self.stats['files_processed'] > 0:
            pct_cleaned = (self.stats['files_cleaned'] / self.stats['files_processed']) * 100
            print(f"Files with footers: {pct_cleaned:.1f}%")

        if self.stats['files_cleaned'] > 0:
            avg_chars_removed = self.stats['chars_removed'] // self.stats['files_cleaned']
            print(f"Average chars removed per file: {avg_chars_removed:,}")

        # Show breakdown by pattern
        print(f"\nPatterns found:")
        for pattern, count in self.stats['patterns_found'].items():
            if count > 0:
                print(f"  • {pattern}: {count:,} files")

        print("\n✅ Footer cleaning complete!")

        if self.backup:
            print(f"💾 Backup files saved with .backup.md extension")


def preview_disclaimer_locations(source_dir: str, max_examples: int = 5):
    """Preview where footer patterns appear in files without making changes."""

    source_path = Path(source_dir)
    footer_patterns = [
        "This article has been prepared for information purposes only, does not constitute an analysis of all potentially material issues and is subject to change at any time without prior notice.",
        "**Did you find this article helpful?**",
        "Did you find this article helpful?",
        "Great, thank you for your feedback"
    ]

    print("🔍 PREVIEW MODE - Finding footer patterns")
    print("-" * 60)

    md_files = list(source_path.glob("*.md"))
    examples_found = 0
    pattern_counts = {pattern[:50] + "..." if len(pattern) > 50 else pattern: 0 for pattern in footer_patterns}

    for file_path in md_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            for pattern in footer_patterns:
                if pattern in content:
                    pattern_key = pattern[:50] + "..." if len(pattern) > 50 else pattern
                    pattern_counts[pattern_key] += 1

                    if examples_found < max_examples:
                        pattern_index = content.find(pattern)

                        # Show context around the pattern
                        start_context = max(0, pattern_index - 200)
                        end_context = min(len(content), pattern_index + len(pattern) + 200)

                        context = content[start_context:end_context]

                        print(f"\n📄 {file_path.name}")
                        print(f"   Pattern: {pattern[:60]}{'...' if len(pattern) > 60 else ''}")
                        print(f"   Position: {pattern_index:,} chars into file")
                        print(f"   Context: ...{context}...")
                        print(f"   Would remove: {len(content) - pattern_index:,} characters")

                        examples_found += 1

                    break  # Only count first pattern found per file

        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    print(f"\n📊 Pattern Summary:")
    total_files_with_patterns = sum(pattern_counts.values())
    for pattern, count in pattern_counts.items():
        if count > 0:
            print(f"  • {pattern}: {count:,} files")

    print(f"\nTotal files with footer patterns: {total_files_with_patterns:,} out of {len(md_files):,}")

    if total_files_with_patterns > 0:
        print(f"💡 Run with --clean to remove footer patterns from all files")


def main():
    """Main entry point with command line interface."""
    parser = argparse.ArgumentParser(
        description='Remove legal disclaimer footers from cleaned markdown files'
    )
    parser.add_argument(
        'source_dir',
        help='Directory containing cleaned markdown files'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview disclaimer locations without making changes'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup files'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Actually perform the cleaning (required to make changes)'
    )

    args = parser.parse_args()

    try:
        if args.preview:
            preview_disclaimer_locations(args.source_dir)
        elif args.clean:
            cleaner = FooterCleaner(
                source_dir=args.source_dir,
                backup=not args.no_backup
            )

            stats = cleaner.clean_directory()
            cleaner.print_summary()

        else:
            print("❌ Must specify either --preview or --clean")
            print("Examples:")
            print(f"  python {__file__} ./dedup_output/cleaned_files --preview")
            print(f"  python {__file__} ./dedup_output/cleaned_files --clean")
            return 1

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
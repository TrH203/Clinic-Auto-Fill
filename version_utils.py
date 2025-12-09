"""
Version management utilities for the Clinic Auto-Fill application.
Provides semantic version comparison and changelog formatting.
"""

from packaging import version
import re


def parse_version(version_string):
    """
    Parse a version string into a Version object.
    
    Args:
        version_string: Version string (e.g., "v1.2.3" or "1.2.3")
    
    Returns:
        packaging.version.Version object
    """
    # Remove 'v' prefix if present
    clean_version = version_string.strip().lstrip('v')
    return version.parse(clean_version)


def compare_versions(v1, v2):
    """
    Compare two version strings.
    
    Args:
        v1: First version string
        v2: Second version string
    
    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
    """
    ver1 = parse_version(v1)
    ver2 = parse_version(v2)
    
    if ver1 < ver2:
        return -1
    elif ver1 > ver2:
        return 1
    else:
        return 0


def is_newer_version(current, latest):
    """
    Check if latest version is newer than current version.
    
    Args:
        current: Current version string
        latest: Latest version string
    
    Returns:
        True if latest is newer than current, False otherwise
    """
    return compare_versions(current, latest) < 0


def format_changelog(release_notes, max_length=500):
    """
    Format release notes for display in the UI.
    
    Args:
        release_notes: Raw release notes from GitHub
        max_length: Maximum length of formatted notes
    
    Returns:
        Formatted string ready for display
    """
    if not release_notes:
        return "No release notes available."
    
    # Clean up the notes
    notes = release_notes.strip()
    
    # Truncate if too long
    if len(notes) > max_length:
        notes = notes[:max_length] + "..."
    
    return notes


def extract_version_number(version_string):
    """
    Extract just the version number from a string.
    
    Args:
        version_string: String containing version (e.g., "v1.2.3" or "Version 1.2.3")
    
    Returns:
        Clean version string (e.g., "1.2.3")
    """
    # Match semantic version pattern
    match = re.search(r'(\d+\.\d+\.\d+)', version_string)
    if match:
        return match.group(1)
    
    # Fallback: remove non-digit/dot characters
    return re.sub(r'[^\d.]', '', version_string)


if __name__ == "__main__":
    # Test version comparison
    print("Testing version utilities...")
    
    test_cases = [
        ("1.0.0", "1.0.1", True),
        ("1.9.0", "1.10.0", True),
        ("2.0.0", "1.9.9", False),
        ("v1.0.0", "v1.0.0", False),
    ]
    
    for current, latest, should_update in test_cases:
        result = is_newer_version(current, latest)
        status = "✓" if result == should_update else "✗"
        print(f"{status} {current} -> {latest}: update={result} (expected={should_update})")
    
    print("\nVersion comparison tests completed!")

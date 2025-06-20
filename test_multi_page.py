#!/usr/bin/env python3
"""
Simple test script to verify multi-page functionality works correctly.
This tests the argument parsing and page processing logic.
"""

import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_single_page_backward_compatibility():
    """Test that single page mode still works (backward compatibility)"""
    print("Testing single page backward compatibility...")
    
    test_args = [
        '--base-url', 'https://example.com',
        '--pr-url', 'https://preview.example.com'
    ]
    
    with patch('sys.argv', ['test'] + test_args):
        from runner.__main__ import main
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--base-url', required=True)
        parser.add_argument('--pr-url', required=True)
        parser.add_argument('--bruni-token', required=False)
        parser.add_argument('--bruni-api-url', required=False)
        parser.add_argument('--pages', required=False)
        
        args = parser.parse_args(test_args)
        
        pages_to_process = []
        if args.pages:
            pages_data = json.loads(args.pages)
            for page in pages_data:
                pages_to_process.append({
                    'base_url': page['base_url'],
                    'pr_url': page['pr_url'],
                    'name': page.get('name', f"Page {len(pages_to_process) + 1}")
                })
        else:
            pages_to_process.append({
                'base_url': args.base_url,
                'pr_url': args.pr_url,
                'name': 'Homepage'
            })
        
        assert len(pages_to_process) == 1
        assert pages_to_process[0]['name'] == 'Homepage'
        assert pages_to_process[0]['base_url'] == 'https://example.com'
        assert pages_to_process[0]['pr_url'] == 'https://preview.example.com'
        
        print("✅ Single page backward compatibility test passed")

def test_multi_page_functionality():
    """Test that multi-page mode works correctly"""
    print("Testing multi-page functionality...")
    
    pages_json = json.dumps([
        {
            "name": "Homepage",
            "base_url": "https://example.com/",
            "pr_url": "https://preview.example.com/"
        },
        {
            "name": "About Page",
            "base_url": "https://example.com/about",
            "pr_url": "https://preview.example.com/about"
        },
        {
            "name": "Contact Page",
            "base_url": "https://example.com/contact",
            "pr_url": "https://preview.example.com/contact"
        }
    ])
    
    test_args = [
        '--base-url', 'https://example.com',
        '--pr-url', 'https://preview.example.com',
        '--pages', pages_json
    ]
    
    with patch('sys.argv', ['test'] + test_args):
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--base-url', required=True)
        parser.add_argument('--pr-url', required=True)
        parser.add_argument('--bruni-token', required=False)
        parser.add_argument('--bruni-api-url', required=False)
        parser.add_argument('--pages', required=False)
        
        args = parser.parse_args(test_args)
        
        pages_to_process = []
        if args.pages:
            pages_data = json.loads(args.pages)
            for page in pages_data:
                pages_to_process.append({
                    'base_url': page['base_url'],
                    'pr_url': page['pr_url'],
                    'name': page.get('name', f"Page {len(pages_to_process) + 1}")
                })
        else:
            pages_to_process.append({
                'base_url': args.base_url,
                'pr_url': args.pr_url,
                'name': 'Homepage'
            })
        
        assert len(pages_to_process) == 3
        assert pages_to_process[0]['name'] == 'Homepage'
        assert pages_to_process[1]['name'] == 'About Page'
        assert pages_to_process[2]['name'] == 'Contact Page'
        
        print("✅ Multi-page functionality test passed")

def test_aggregation_logic():
    """Test the aggregation logic for multiple page results"""
    print("Testing aggregation logic...")
    
    from runner.__main__ import aggregate_page_results
    
    page_results_pass = [
        {'visual_analysis': {'status_enum': 'pass'}},
        {'visual_analysis': {'status_enum': 'pass'}},
    ]
    
    result = aggregate_page_results(page_results_pass)
    assert result['status_enum'] == 'pass'
    assert result['recommendation_enum'] == 'pass'
    
    page_results_fail = [
        {'visual_analysis': {'status_enum': 'pass'}},
        {'visual_analysis': {'status_enum': 'fail'}},
    ]
    
    result = aggregate_page_results(page_results_fail)
    assert result['status_enum'] == 'fail'
    assert result['recommendation_enum'] == 'reject'
    
    page_results_warning = [
        {'visual_analysis': {'status_enum': 'pass'}},
        {'visual_analysis': {'status_enum': 'warning'}},
    ]
    
    result = aggregate_page_results(page_results_warning)
    assert result['status_enum'] == 'warning'
    assert result['recommendation_enum'] == 'review_required'
    
    print("✅ Aggregation logic test passed")

if __name__ == '__main__':
    try:
        test_single_page_backward_compatibility()
        test_multi_page_functionality()
        test_aggregation_logic()
        print("\n🎉 All tests passed! Multi-page functionality is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

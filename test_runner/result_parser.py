"""
Test Result Parser Module
Analyzes and processes test execution results
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from collections import defaultdict

@dataclass
class TestAnalysis:
    """Test analysis data structure"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    success_rate: float
    average_duration: float
    longest_test: str
    shortest_test: str
    common_errors: List[Dict[str, Any]]
    test_categories: Dict[str, int]
    execution_trend: List[Dict[str, Any]]

class ResultParser:
    """Test result parser and analyzer"""
    
    def __init__(self):
        """Initialize the result parser"""
        self.results = []
        self.analysis = None
    
    def load_results(self, filename: str) -> bool:
        """Load test results from a JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.results = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading results from {filename}: {e}")
            return False
    
    def parse_pytest_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse pytest output and extract test results"""
        results = []
        lines = output.split('\n')
        
        current_test = None
        
        for line in lines:
            # Match test result lines
            if re.match(r'^test_.*::.*', line):
                parts = line.split('::')
                if len(parts) >= 2:
                    test_name = parts[1].strip()
                    status = "passed"  # Default status
                    
                    if "FAILED" in line:
                        status = "failed"
                    elif "ERROR" in line:
                        status = "error"
                    elif "SKIPPED" in line:
                        status = "skipped"
                    
                    current_test = {
                        "test_name": test_name,
                        "status": status,
                        "duration": 0.0,
                        "timestamp": datetime.now().isoformat()
                    }
                    results.append(current_test)
            
            # Extract duration if available
            elif current_test and "seconds" in line:
                duration_match = re.search(r'(\d+\.\d+)s', line)
                if duration_match:
                    current_test["duration"] = float(duration_match.group(1))
        
        return results
    
    def analyze_results(self) -> TestAnalysis:
        """Analyze test results and generate insights"""
        if not self.results:
            raise ValueError("No results to analyze. Load results first.")
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.get('status') == 'passed'])
        failed_tests = len([r for r in self.results if r.get('status') == 'failed'])
        error_tests = len([r for r in self.results if r.get('status') == 'error'])
        skipped_tests = len([r for r in self.results if r.get('status') == 'skipped'])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate average duration
        durations = [r.get('duration', 0) for r in self.results if r.get('duration')]
        average_duration = sum(durations) / len(durations) if durations else 0
        
        # Find longest and shortest tests
        if durations:
            longest_test = max(self.results, key=lambda x: x.get('duration', 0))
            shortest_test = min(self.results, key=lambda x: x.get('duration', 0))
            longest_test_name = longest_test.get('test_name', 'Unknown')
            shortest_test_name = shortest_test.get('test_name', 'Unknown')
        else:
            longest_test_name = "N/A"
            shortest_test_name = "N/A"
        
        # Analyze common errors
        common_errors = self._analyze_common_errors()
        
        # Categorize tests
        test_categories = self._categorize_tests()
        
        # Analyze execution trend
        execution_trend = self._analyze_execution_trend()
        
        self.analysis = TestAnalysis(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            error_tests=error_tests,
            skipped_tests=skipped_tests,
            success_rate=success_rate,
            average_duration=average_duration,
            longest_test=longest_test_name,
            shortest_test=shortest_test_name,
            common_errors=common_errors,
            test_categories=test_categories,
            execution_trend=execution_trend
        )
        
        return self.analysis
    
    def _analyze_common_errors(self) -> List[Dict[str, Any]]:
        """Analyze and categorize common errors"""
        error_counts = defaultdict(int)
        error_details = defaultdict(list)
        
        for result in self.results:
            if result.get('status') in ['failed', 'error']:
                error_message = result.get('error_message', 'Unknown error')
                
                # Categorize errors
                if 'timeout' in error_message.lower():
                    error_type = 'Timeout'
                elif 'element not found' in error_message.lower():
                    error_type = 'Element Not Found'
                elif 'assertion' in error_message.lower():
                    error_type = 'Assertion Failed'
                elif 'network' in error_message.lower():
                    error_type = 'Network Error'
                elif 'permission' in error_message.lower():
                    error_type = 'Permission Error'
                else:
                    error_type = 'Other'
                
                error_counts[error_type] += 1
                error_details[error_type].append({
                    'test_name': result.get('test_name', 'Unknown'),
                    'message': error_message[:100] + '...' if len(error_message) > 100 else error_message
                })
        
        # Convert to list format
        common_errors = []
        for error_type, count in error_counts.items():
            common_errors.append({
                'type': error_type,
                'count': count,
                'percentage': (count / len([r for r in self.results if r.get('status') in ['failed', 'error']]) * 100) if any(r.get('status') in ['failed', 'error'] for r in self.results) else 0,
                'examples': error_details[error_type][:3]  # Top 3 examples
            })
        
        # Sort by count (descending)
        common_errors.sort(key=lambda x: x['count'], reverse=True)
        
        return common_errors
    
    def _categorize_tests(self) -> Dict[str, int]:
        """Categorize tests by type and status"""
        categories = defaultdict(int)
        
        for result in self.results:
            test_name = result.get('test_name', 'Unknown')
            status = result.get('status', 'unknown')
            
            # Determine test category based on name
            if 'web' in test_name.lower():
                category = 'Web Tests'
            elif 'mobile' in test_name.lower():
                category = 'Mobile Tests'
            elif 'api' in test_name.lower():
                category = 'API Tests'
            elif 'unit' in test_name.lower():
                category = 'Unit Tests'
            elif 'integration' in test_name.lower():
                category = 'Integration Tests'
            else:
                category = 'Other Tests'
            
            categories[f"{category} ({status})"] += 1
        
        return dict(categories)
    
    def _analyze_execution_trend(self) -> List[Dict[str, Any]]:
        """Analyze test execution trend over time"""
        # Group results by timestamp (hourly)
        hourly_stats = defaultdict(lambda: {'total': 0, 'passed': 0, 'failed': 0, 'error': 0})
        
        for result in self.results:
            timestamp = result.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour_key = dt.strftime('%Y-%m-%d %H:00')
                    
                    hourly_stats[hour_key]['total'] += 1
                    status = result.get('status', 'unknown')
                    if status in hourly_stats[hour_key]:
                        hourly_stats[hour_key][status] += 1
                except:
                    pass
        
        # Convert to list format
        trend = []
        for hour, stats in sorted(hourly_stats.items()):
            trend.append({
                'hour': hour,
                'total': stats['total'],
                'passed': stats['passed'],
                'failed': stats['failed'],
                'error': stats['error'],
                'success_rate': (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            })
        
        return trend
    
    def generate_summary_report(self) -> str:
        """Generate a summary report of test results"""
        if not self.analysis:
            self.analyze_results()
        
        report = f"""
Test Execution Summary Report
============================

Overall Statistics:
------------------
Total Tests Executed: {self.analysis.total_tests}
Passed: {self.analysis.passed_tests} ({self.analysis.success_rate:.1f}%)
Failed: {self.analysis.failed_tests}
Errors: {self.analysis.error_tests}
Skipped: {self.analysis.skipped_tests}

Performance Metrics:
-------------------
Average Test Duration: {self.analysis.average_duration:.2f} seconds
Longest Test: {self.analysis.longest_test}
Shortest Test: {self.analysis.shortest_test}

Test Categories:
----------------
"""
        
        for category, count in self.analysis.test_categories.items():
            report += f"{category}: {count}\n"
        
        if self.analysis.common_errors:
            report += "\nCommon Error Types:\n"
            report += "-" * 20 + "\n"
            for error in self.analysis.common_errors[:5]:  # Top 5 errors
                report += f"{error['type']}: {error['count']} occurrences ({error['percentage']:.1f}%)\n"
        
        return report
    
    def export_to_excel(self, filename: str) -> bool:
        """Export test results to Excel file"""
        try:
            # Create DataFrame from results
            df_results = pd.DataFrame(self.results)
            
            # Create DataFrame from analysis
            if self.analysis:
                analysis_data = {
                    'Metric': ['Total Tests', 'Passed', 'Failed', 'Error', 'Skipped', 'Success Rate (%)', 'Average Duration (s)'],
                    'Value': [
                        self.analysis.total_tests,
                        self.analysis.passed_tests,
                        self.analysis.failed_tests,
                        self.analysis.error_tests,
                        self.analysis.skipped_tests,
                        self.analysis.success_rate,
                        self.analysis.average_duration
                    ]
                }
                df_analysis = pd.DataFrame(analysis_data)
                
                # Create DataFrame for common errors
                df_errors = pd.DataFrame(self.analysis.common_errors)
                
                # Create DataFrame for execution trend
                df_trend = pd.DataFrame(self.analysis.execution_trend)
                
                # Write to Excel with multiple sheets
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    df_results.to_excel(writer, sheet_name='Test Results', index=False)
                    df_analysis.to_excel(writer, sheet_name='Summary', index=False)
                    df_errors.to_excel(writer, sheet_name='Common Errors', index=False)
                    df_trend.to_excel(writer, sheet_name='Execution Trend', index=False)
            
            print(f"Results exported to {filename}")
            return True
            
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False
    
    def generate_comparison_report(self, other_results_file: str) -> str:
        """Generate a comparison report between two test runs"""
        # Load other results
        other_parser = ResultParser()
        if not other_parser.load_results(other_results_file):
            return "Error: Could not load comparison results file."
        
        other_analysis = other_parser.analyze_results()
        
        if not self.analysis:
            self.analyze_results()
        
        report = f"""
Test Results Comparison Report
=============================

Current Run vs Previous Run:
---------------------------

Metric              Current    Previous    Change
------              -------    --------    ------
Total Tests         {self.analysis.total_tests:>8}    {other_analysis.total_tests:>8}    {self.analysis.total_tests - other_analysis.total_tests:+>8}
Passed Tests        {self.analysis.passed_tests:>8}    {other_analysis.passed_tests:>8}    {self.analysis.passed_tests - other_analysis.passed_tests:+>8}
Failed Tests        {self.analysis.failed_tests:>8}    {other_analysis.failed_tests:>8}    {self.analysis.failed_tests - other_analysis.failed_tests:+>8}
Error Tests         {self.analysis.error_tests:>8}    {other_analysis.error_tests:>8}    {self.analysis.error_tests - other_analysis.error_tests:+>8}
Success Rate (%)    {self.analysis.success_rate:>8.1f}    {other_analysis.success_rate:>8.1f}    {self.analysis.success_rate - other_analysis.success_rate:+>8.1f}
Avg Duration (s)    {self.analysis.average_duration:>8.2f}    {other_analysis.average_duration:>8.2f}    {self.analysis.average_duration - other_analysis.average_duration:+>8.2f}

Key Changes:
------------
"""
        
        # Analyze key changes
        success_rate_change = self.analysis.success_rate - other_analysis.success_rate
        if success_rate_change > 5:
            report += "✅ Significant improvement in success rate\n"
        elif success_rate_change < -5:
            report += "❌ Significant decline in success rate\n"
        
        duration_change = self.analysis.average_duration - other_analysis.average_duration
        if duration_change < -1:
            report += "✅ Tests are running faster\n"
        elif duration_change > 1:
            report += "⚠️  Tests are running slower\n"
        
        return report
    
    def get_failed_tests(self) -> List[Dict[str, Any]]:
        """Get list of failed tests with details"""
        return [r for r in self.results if r.get('status') in ['failed', 'error']]
    
    def get_slow_tests(self, threshold: float = 10.0) -> List[Dict[str, Any]]:
        """Get list of tests that take longer than threshold"""
        return [r for r in self.results if r.get('duration', 0) > threshold]
    
    def get_flaky_tests(self, other_results_file: str) -> List[str]:
        """Identify potentially flaky tests by comparing results"""
        other_parser = ResultParser()
        if not other_parser.load_results(other_results_file):
            return []
        
        current_tests = {r.get('test_name'): r.get('status') for r in self.results}
        other_tests = {r.get('test_name'): r.get('status') for r in other_parser.results}
        
        flaky_tests = []
        for test_name in set(current_tests.keys()) & set(other_tests.keys()):
            if current_tests[test_name] != other_tests[test_name]:
                flaky_tests.append(test_name)
        
        return flaky_tests 
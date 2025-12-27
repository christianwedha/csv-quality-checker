#!/usr/bin/env python3
"""
CSV Data Quality Checker
A simple tool to analyze data quality issues in CSV files.
Perfect for beginners learning data validation for AI/ML projects.
"""

import pandas as pd
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_missing_values(df):
    """Check for missing values in the dataset."""
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    
    issues = []
    for col in df.columns:
        if missing[col] > 0:
            issues.append({
                'column': col,
                'missing_count': int(missing[col]),
                'missing_percentage': round(missing_pct[col], 2)
            })
    
    return issues


def check_duplicates(df):
    """Check for duplicate rows."""
    dup_count = df.duplicated().sum()
    dup_pct = (dup_count / len(df)) * 100 if len(df) > 0 else 0
    
    return {
        'duplicate_rows': int(dup_count),
        'duplicate_percentage': round(dup_pct, 2)
    }


def check_data_types(df):
    """Analyze data types of each column."""
    type_info = []
    for col in df.columns:
        type_info.append({
            'column': col,
            'data_type': str(df[col].dtype),
            'unique_values': int(df[col].nunique()),
            'sample_values': df[col].dropna().head(3).tolist()
        })
    
    return type_info


def check_outliers(df):
    """Check for potential outliers in numeric columns using IQR method."""
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    outlier_info = []
    
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        
        if len(outliers) > 0:
            outlier_info.append({
                'column': col,
                'outlier_count': len(outliers),
                'outlier_percentage': round((len(outliers) / len(df)) * 100, 2),
                'lower_bound': round(lower_bound, 2),
                'upper_bound': round(upper_bound, 2)
            })
    
    return outlier_info


def generate_html_report(results, output_path):
    """Generate an HTML report of the quality check."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Quality Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
            h2 {{ color: #555; margin-top: 30px; }}
            .summary {{ background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .warning {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .error {{ background: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .success {{ background: #d4edda; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th {{ background: #4CAF50; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            tr:hover {{ background: #f5f5f5; }}
            .metric {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Data Quality Report</h1>
            <p><strong>File:</strong> {results['filename']}</p>
            <p><strong>Generated:</strong> {results['timestamp']}</p>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><span class="metric">{results['total_rows']}</span> rows</p>
                <p><span class="metric">{results['total_columns']}</span> columns</p>
            </div>
            
            <h2>🔍 Missing Values</h2>
    """
    
    if results['missing_values']:
        html += '<div class="warning">'
        html += '<table><tr><th>Column</th><th>Missing Count</th><th>Percentage</th></tr>'
        for item in results['missing_values']:
            html += f"<tr><td>{item['column']}</td><td>{item['missing_count']}</td><td>{item['missing_percentage']}%</td></tr>"
        html += '</table></div>'
    else:
        html += '<div class="success">✅ No missing values found!</div>'
    
    html += '<h2>🔄 Duplicate Rows</h2>'
    if results['duplicates']['duplicate_rows'] > 0:
        html += f"""
        <div class="warning">
            <p>Found <strong>{results['duplicates']['duplicate_rows']}</strong> duplicate rows ({results['duplicates']['duplicate_percentage']}% of data)</p>
        </div>
        """
    else:
        html += '<div class="success">✅ No duplicate rows found!</div>'
    
    html += '<h2>📋 Data Types</h2>'
    html += '<table><tr><th>Column</th><th>Type</th><th>Unique Values</th><th>Sample</th></tr>'
    for item in results['data_types']:
        sample = ', '.join([str(x) for x in item['sample_values'][:3]])
        html += f"<tr><td>{item['column']}</td><td>{item['data_type']}</td><td>{item['unique_values']}</td><td>{sample}</td></tr>"
    html += '</table>'
    
    html += '<h2>⚠️ Outliers</h2>'
    if results['outliers']:
        html += '<div class="error">'
        html += '<table><tr><th>Column</th><th>Outlier Count</th><th>Percentage</th><th>Valid Range</th></tr>'
        for item in results['outliers']:
            html += f"<tr><td>{item['column']}</td><td>{item['outlier_count']}</td><td>{item['outlier_percentage']}%</td><td>{item['lower_bound']} to {item['upper_bound']}</td></tr>"
        html += '</table></div>'
    else:
        html += '<div class="success">✅ No outliers detected in numeric columns!</div>'
    
    html += """
        </div>
    </body>
    </html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def analyze_csv(input_path, output_path=None):
    """Main function to analyze CSV file."""
    try:
        logger.info(f"Reading CSV file: {input_path}")
        df = pd.read_csv(input_path)
        
        logger.info(f"Dataset loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Run all checks
        results = {
            'filename': Path(input_path).name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_values': check_missing_values(df),
            'duplicates': check_duplicates(df),
            'data_types': check_data_types(df),
            'outliers': check_outliers(df)
        }
        
        # Generate report
        if output_path is None:
            output_path = Path(input_path).stem + '_quality_report.html'
        
        generate_html_report(results, output_path)
        logger.info(f"✅ Quality report generated: {output_path}")
        
        # Print summary to console
        print("\n" + "="*50)
        print("DATA QUALITY CHECK COMPLETE")
        print("="*50)
        print(f"Total rows: {results['total_rows']}")
        print(f"Total columns: {results['total_columns']}")
        print(f"Missing value issues: {len(results['missing_values'])}")
        print(f"Duplicate rows: {results['duplicates']['duplicate_rows']}")
        print(f"Outlier columns: {len(results['outliers'])}")
        print(f"\n📄 Full report: {output_path}")
        print("="*50 + "\n")
        
        return results
        
    except FileNotFoundError:
        logger.error(f"File not found: {input_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error("The CSV file is empty")
        raise
    except Exception as e:
        logger.error(f"Error analyzing CSV: {str(e)}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Check data quality issues in CSV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python csv_quality_checker.py data.csv
  python csv_quality_checker.py data.csv --output my_report.html
        """
    )
    
    parser.add_argument('input', help='Path to input CSV file')
    parser.add_argument('--output', '-o', help='Path to output HTML report (optional)')
    
    args = parser.parse_args()
    
    analyze_csv(args.input, args.output)


if __name__ == '__main__':
    main()
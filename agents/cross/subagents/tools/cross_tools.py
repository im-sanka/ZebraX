"""
Cross Comparison Tools

Functions for comparing two Excel tables and providing statistical analysis.
Includes tools for:
- Loading and comparing tables
- Column-by-column comparison
- Multiple agreement metrics (Kappa, Krippendorff's Alpha, etc.)
- Detailed difference reports
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


def load_table(file_path: str) -> Dict[str, Any]:
    """
    Load an Excel table and return its data.
    
    Args:
        file_path: Path to the Excel file.
    
    Returns:
        Dictionary with table data and metadata.
    """
    try:
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        
        df = pd.read_excel(file_path)
        df = df.where(pd.notnull(df), None)
        
        return {
            "success": True,
            "file_path": file_path,
            "columns": list(df.columns),
            "row_count": len(df),
            "data": df.to_dict(orient='records')
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_table_info(file_path: str) -> Dict[str, Any]:
    """
    Get metadata about a table without loading all data.
    
    Args:
        file_path: Path to the Excel file.
    
    Returns:
        Dictionary with table metadata.
    """
    try:
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        
        df = pd.read_excel(file_path)
        
        return {
            "success": True,
            "file_path": file_path,
            "columns": list(df.columns),
            "row_count": len(df),
            "column_types": {col: str(df[col].dtype) for col in df.columns}
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def compare_tables_overview(file_path_1: str, file_path_2: str) -> Dict[str, Any]:
    """
    Get an overview comparison of two tables (columns, row counts).
    
    Args:
        file_path_1: Path to the first Excel file.
        file_path_2: Path to the second Excel file.
    
    Returns:
        Dictionary with overview comparison.
    """
    try:
        info1 = get_table_info(file_path_1)
        info2 = get_table_info(file_path_2)
        
        if not info1["success"]:
            return info1
        if not info2["success"]:
            return info2
        
        cols1 = set(info1["columns"])
        cols2 = set(info2["columns"])
        
        return {
            "success": True,
            "table_1": {
                "file": file_path_1,
                "columns": info1["columns"],
                "row_count": info1["row_count"]
            },
            "table_2": {
                "file": file_path_2,
                "columns": info2["columns"],
                "row_count": info2["row_count"]
            },
            "common_columns": list(cols1 & cols2),
            "only_in_table_1": list(cols1 - cols2),
            "only_in_table_2": list(cols2 - cols1),
            "row_count_match": info1["row_count"] == info2["row_count"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def compare_column_values(
    file_path_1: str, 
    file_path_2: str, 
    column_name: str,
    match_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare values in a specific column between two tables.
    
    Args:
        file_path_1: Path to the first Excel file.
        file_path_2: Path to the second Excel file.
        column_name: The column to compare.
        match_by: Column to use for matching rows (e.g., "Title"). If None, compares by row index.
    
    Returns:
        Dictionary with comparison results and statistics.
    """
    try:
        df1 = pd.read_excel(file_path_1)
        df2 = pd.read_excel(file_path_2)
        
        if column_name not in df1.columns:
            return {"success": False, "error": f"Column '{column_name}' not found in table 1"}
        if column_name not in df2.columns:
            return {"success": False, "error": f"Column '{column_name}' not found in table 2"}
        
        # Normalize values for comparison
        def normalize(val):
            if pd.isna(val) or val is None:
                return None
            val_str = str(val).strip().upper()
            if val_str in ("TRUE", "YES", "1"):
                return "TRUE"
            elif val_str in ("FALSE", "NO", "0"):
                return "FALSE"
            return val_str
        
        comparisons = []
        agreements = 0
        disagreements = 0
        
        if match_by and match_by in df1.columns and match_by in df2.columns:
            # Match by a key column (e.g., Title)
            df2_dict = {normalize(row[match_by]): row for _, row in df2.iterrows()}
            
            for idx, row1 in df1.iterrows():
                key = normalize(row1[match_by])
                val1 = normalize(row1[column_name])
                
                if key in df2_dict:
                    val2 = normalize(df2_dict[key][column_name])
                    match = val1 == val2
                    
                    if match:
                        agreements += 1
                    else:
                        disagreements += 1
                    
                    comparisons.append({
                        "match_key": str(row1[match_by])[:50],  # Truncate for readability
                        "table_1_value": val1,
                        "table_2_value": val2,
                        "agreement": match
                    })
                else:
                    comparisons.append({
                        "match_key": str(row1[match_by])[:50],
                        "table_1_value": val1,
                        "table_2_value": "NOT_FOUND",
                        "agreement": False
                    })
                    disagreements += 1
        else:
            # Match by row index
            max_rows = max(len(df1), len(df2))
            for idx in range(max_rows):
                val1 = normalize(df1.iloc[idx][column_name]) if idx < len(df1) else "N/A"
                val2 = normalize(df2.iloc[idx][column_name]) if idx < len(df2) else "N/A"
                match = val1 == val2
                
                if match:
                    agreements += 1
                else:
                    disagreements += 1
                
                comparisons.append({
                    "row_index": idx,
                    "table_1_value": val1,
                    "table_2_value": val2,
                    "agreement": match
                })
        
        total = agreements + disagreements
        agreement_rate = (agreements / total * 100) if total > 0 else 0
        
        return {
            "success": True,
            "column_name": column_name,
            "match_by": match_by or "row_index",
            "statistics": {
                "total_comparisons": total,
                "agreements": agreements,
                "disagreements": disagreements,
                "agreement_rate": round(agreement_rate, 2),
                "disagreement_rate": round(100 - agreement_rate, 2)
            },
            "comparisons": comparisons,
            "disagreement_details": [c for c in comparisons if not c["agreement"]]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def compare_multiple_columns(
    file_path_1: str,
    file_path_2: str,
    column_names: List[str],
    match_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare multiple columns between two tables.
    
    Args:
        file_path_1: Path to the first Excel file.
        file_path_2: Path to the second Excel file.
        column_names: List of columns to compare.
        match_by: Column to use for matching rows.
    
    Returns:
        Dictionary with comparison results for all columns.
    """
    try:
        results = {}
        overall_agreements = 0
        overall_disagreements = 0
        
        for col in column_names:
            col_result = compare_column_values(file_path_1, file_path_2, col, match_by)
            if col_result["success"]:
                results[col] = col_result["statistics"]
                overall_agreements += col_result["statistics"]["agreements"]
                overall_disagreements += col_result["statistics"]["disagreements"]
            else:
                results[col] = {"error": col_result["error"]}
        
        total = overall_agreements + overall_disagreements
        overall_rate = (overall_agreements / total * 100) if total > 0 else 0
        
        return {
            "success": True,
            "columns_compared": column_names,
            "match_by": match_by or "row_index",
            "per_column_statistics": results,
            "overall_statistics": {
                "total_comparisons": total,
                "total_agreements": overall_agreements,
                "total_disagreements": overall_disagreements,
                "overall_agreement_rate": round(overall_rate, 2)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def calculate_cohens_kappa(
    file_path_1: str,
    file_path_2: str,
    column_name: str,
    match_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate Cohen's Kappa for inter-rater reliability on a binary column.
    
    Cohen's Kappa measures agreement between two raters, accounting for chance agreement.
    - κ = 1: Perfect agreement
    - κ = 0: Agreement equivalent to chance
    - κ < 0: Less than chance agreement
    
    Interpretation:
    - 0.81-1.00: Almost perfect
    - 0.61-0.80: Substantial
    - 0.41-0.60: Moderate
    - 0.21-0.40: Fair
    - 0.00-0.20: Slight
    - < 0: Poor
    
    Args:
        file_path_1: Path to the first Excel file.
        file_path_2: Path to the second Excel file.
        column_name: The binary column to analyze.
        match_by: Column to use for matching rows.
    
    Returns:
        Dictionary with Cohen's Kappa and interpretation.
    """
    try:
        comparison = compare_column_values(file_path_1, file_path_2, column_name, match_by)
        if not comparison["success"]:
            return comparison
        
        # Build confusion matrix for binary values
        # Assumes TRUE/FALSE values
        tp = 0  # Both TRUE
        tn = 0  # Both FALSE
        fp = 0  # Table1=FALSE, Table2=TRUE
        fn = 0  # Table1=TRUE, Table2=FALSE
        
        for comp in comparison["comparisons"]:
            v1 = comp["table_1_value"]
            v2 = comp["table_2_value"]
            
            if v1 == "TRUE" and v2 == "TRUE":
                tp += 1
            elif v1 == "FALSE" and v2 == "FALSE":
                tn += 1
            elif v1 == "FALSE" and v2 == "TRUE":
                fp += 1
            elif v1 == "TRUE" and v2 == "FALSE":
                fn += 1
        
        total = tp + tn + fp + fn
        if total == 0:
            return {"success": False, "error": "No valid comparisons found"}
        
        # Observed agreement
        po = (tp + tn) / total
        
        # Expected agreement by chance
        p_yes = ((tp + fn) / total) * ((tp + fp) / total)
        p_no = ((tn + fp) / total) * ((tn + fn) / total)
        pe = p_yes + p_no
        
        # Cohen's Kappa
        if pe == 1:
            kappa = 1.0  # Perfect agreement
        else:
            kappa = (po - pe) / (1 - pe)
        
        # Interpretation
        if kappa >= 0.81:
            interpretation = "Almost Perfect"
        elif kappa >= 0.61:
            interpretation = "Substantial"
        elif kappa >= 0.41:
            interpretation = "Moderate"
        elif kappa >= 0.21:
            interpretation = "Fair"
        elif kappa >= 0:
            interpretation = "Slight"
        else:
            interpretation = "Poor (less than chance)"
        
        return {
            "success": True,
            "column_name": column_name,
            "cohens_kappa": round(kappa, 4),
            "interpretation": interpretation,
            "observed_agreement": round(po * 100, 2),
            "expected_agreement_by_chance": round(pe * 100, 2),
            "confusion_matrix": {
                "both_true": tp,
                "both_false": tn,
                "table1_false_table2_true": fp,
                "table1_true_table2_false": fn
            },
            "total_samples": total
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def calculate_all_agreement_metrics(
    file_path_1: str,
    file_path_2: str,
    column_name: str,
    match_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate multiple agreement metrics for comprehensive analysis.
    
    Includes:
    - Percent Agreement (simple agreement rate)
    - Cohen's Kappa (accounts for chance agreement)
    - Scott's Pi (assumes same marginal distributions)
    - Gwet's AC1 (robust when prevalence is high/low)
    - Krippendorff's Alpha (handles missing data, multiple coders)
    
    Args:
        file_path_1: Path to the first Excel file.
        file_path_2: Path to the second Excel file.
        column_name: The column to analyze.
        match_by: Column to use for matching rows.
    
    Returns:
        Dictionary with all agreement metrics.
    """
    try:
        comparison = compare_column_values(file_path_1, file_path_2, column_name, match_by)
        if not comparison["success"]:
            return comparison
        
        # Build confusion matrix
        tp = tn = fp = fn = 0
        for comp in comparison["comparisons"]:
            v1 = comp["table_1_value"]
            v2 = comp["table_2_value"]
            
            if v1 == "TRUE" and v2 == "TRUE":
                tp += 1
            elif v1 == "FALSE" and v2 == "FALSE":
                tn += 1
            elif v1 == "FALSE" and v2 == "TRUE":
                fp += 1
            elif v1 == "TRUE" and v2 == "FALSE":
                fn += 1
        
        total = tp + tn + fp + fn
        if total == 0:
            return {"success": False, "error": "No valid comparisons found"}
        
        # 1. Percent Agreement (Po)
        po = (tp + tn) / total
        percent_agreement = round(po * 100, 2)
        
        # 2. Cohen's Kappa
        p1_yes = (tp + fn) / total  # Table 1 proportion of YES
        p2_yes = (tp + fp) / total  # Table 2 proportion of YES
        p1_no = (tn + fp) / total   # Table 1 proportion of NO
        p2_no = (tn + fn) / total   # Table 2 proportion of NO
        
        pe_kappa = (p1_yes * p2_yes) + (p1_no * p2_no)
        kappa = (po - pe_kappa) / (1 - pe_kappa) if pe_kappa != 1 else 1.0
        
        # 3. Scott's Pi (assumes same marginal proportions)
        p_yes = (p1_yes + p2_yes) / 2
        p_no = (p1_no + p2_no) / 2
        pe_scott = (p_yes ** 2) + (p_no ** 2)
        scotts_pi = (po - pe_scott) / (1 - pe_scott) if pe_scott != 1 else 1.0
        
        # 4. Gwet's AC1 (more stable when agreement is very high or low)
        # AC1 = (Po - Pe) / (1 - Pe) where Pe = 2 * p * (1-p) and p = (p_yes + p_no) / 2
        p_avg = (p_yes + (1 - p_no)) / 2  # average proportion
        pe_gwet = 2 * p_avg * (1 - p_avg)
        gwets_ac1 = (po - pe_gwet) / (1 - pe_gwet) if pe_gwet != 1 else 1.0
        
        # 5. Krippendorff's Alpha (simplified for 2 coders, binary)
        # Alpha = 1 - Do/De where Do = observed disagreement, De = expected disagreement
        n = total
        do = (fp + fn) / n  # observed disagreement
        n_yes = tp + fn + tp + fp  # total YES across both
        n_no = tn + fp + tn + fn   # total NO across both
        de = (n_yes * n_no) / (n * (2*n - 1)) if n > 1 else 0
        krippendorff_alpha = 1 - (do / de) if de != 0 else 1.0
        
        # Interpretation helper
        def interpret(value):
            if value >= 0.81:
                return "Almost Perfect"
            elif value >= 0.61:
                return "Substantial"
            elif value >= 0.41:
                return "Moderate"
            elif value >= 0.21:
                return "Fair"
            elif value >= 0:
                return "Slight"
            else:
                return "Poor"
        
        return {
            "success": True,
            "column_name": column_name,
            "total_samples": total,
            "confusion_matrix": {
                "both_true": tp,
                "both_false": tn,
                "table1_false_table2_true": fp,
                "table1_true_table2_false": fn
            },
            "metrics": {
                "percent_agreement": {
                    "value": percent_agreement,
                    "description": "Simple percentage of matching values (does NOT account for chance)"
                },
                "cohens_kappa": {
                    "value": round(kappa, 4),
                    "interpretation": interpret(kappa),
                    "description": "Accounts for chance agreement. Most common metric."
                },
                "scotts_pi": {
                    "value": round(scotts_pi, 4),
                    "interpretation": interpret(scotts_pi),
                    "description": "Similar to Kappa, assumes same marginal distributions."
                },
                "gwets_ac1": {
                    "value": round(gwets_ac1, 4),
                    "interpretation": interpret(gwets_ac1),
                    "description": "More stable than Kappa when prevalence is very high/low (Kappa paradox)."
                },
                "krippendorff_alpha": {
                    "value": round(krippendorff_alpha, 4),
                    "interpretation": interpret(krippendorff_alpha),
                    "description": "Handles missing data, generalizes to multiple coders."
                }
            },
            "recommendation": _get_metric_recommendation(tp, tn, fp, fn, kappa, gwets_ac1)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_metric_recommendation(tp: int, tn: int, fp: int, fn: int, kappa: float, ac1: float) -> str:
    """Get a recommendation for which metric to use based on the data."""
    total = tp + tn + fp + fn
    prevalence = (tp + fn) / total if total > 0 else 0.5
    
    # Check for Kappa paradox (high agreement but low Kappa)
    po = (tp + tn) / total
    kappa_paradox = po > 0.8 and kappa < 0.4
    
    if kappa_paradox:
        return f"⚠️ Kappa Paradox detected: High agreement ({po*100:.1f}%) but low Kappa ({kappa:.2f}). Use Gwet's AC1 ({ac1:.2f}) for better interpretation."
    elif prevalence > 0.9 or prevalence < 0.1:
        return f"⚠️ High prevalence imbalance ({prevalence*100:.1f}% positive). Consider Gwet's AC1 alongside Kappa."
    else:
        return "Cohen's Kappa is appropriate for this data distribution."


def get_disagreement_report(
    file_path_1: str,
    file_path_2: str,
    column_name: str,
    match_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a detailed report of all disagreements between two tables for a column.
    
    Args:
        file_path_1: Path to the first Excel file.
        file_path_2: Path to the second Excel file.
        column_name: The column to analyze.
        match_by: Column to use for matching rows.
    
    Returns:
        Dictionary with detailed disagreement report.
    """
    try:
        comparison = compare_column_values(file_path_1, file_path_2, column_name, match_by)
        if not comparison["success"]:
            return comparison
        
        disagreements = comparison["disagreement_details"]
        
        # Categorize disagreements
        true_to_false = []  # Table1=TRUE, Table2=FALSE
        false_to_true = []  # Table1=FALSE, Table2=TRUE
        other = []
        
        for d in disagreements:
            v1 = d.get("table_1_value")
            v2 = d.get("table_2_value")
            
            if v1 == "TRUE" and v2 == "FALSE":
                true_to_false.append(d)
            elif v1 == "FALSE" and v2 == "TRUE":
                false_to_true.append(d)
            else:
                other.append(d)
        
        return {
            "success": True,
            "column_name": column_name,
            "total_disagreements": len(disagreements),
            "summary": {
                "table1_true_table2_false": len(true_to_false),
                "table1_false_table2_true": len(false_to_true),
                "other_differences": len(other)
            },
            "details": {
                "table1_true_table2_false": true_to_false,
                "table1_false_table2_true": false_to_true,
                "other": other
            },
            "statistics": comparison["statistics"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def full_statistical_comparison(
    file_path_1: str,
    file_path_2: str,
    column_names: List[str],
    match_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform a full statistical comparison of multiple columns between two tables.
    Includes agreement rates, Cohen's Kappa, and disagreement summaries.
    
    Args:
        file_path_1: Path to the first Excel file.
        file_path_2: Path to the second Excel file.
        column_names: List of columns to compare.
        match_by: Column to use for matching rows.
    
    Returns:
        Dictionary with comprehensive statistical analysis.
    """
    try:
        overview = compare_tables_overview(file_path_1, file_path_2)
        if not overview["success"]:
            return overview
        
        results = {
            "success": True,
            "overview": overview,
            "columns_analyzed": column_names,
            "match_by": match_by or "row_index",
            "per_column_analysis": {}
        }
        
        total_kappa_sum = 0
        valid_kappa_count = 0
        
        for col in column_names:
            col_analysis = {
                "comparison": compare_column_values(file_path_1, file_path_2, col, match_by),
                "kappa": calculate_cohens_kappa(file_path_1, file_path_2, col, match_by)
            }
            
            if col_analysis["kappa"]["success"]:
                total_kappa_sum += col_analysis["kappa"]["cohens_kappa"]
                valid_kappa_count += 1
            
            results["per_column_analysis"][col] = {
                "agreement_rate": col_analysis["comparison"]["statistics"]["agreement_rate"] if col_analysis["comparison"]["success"] else None,
                "disagreements": col_analysis["comparison"]["statistics"]["disagreements"] if col_analysis["comparison"]["success"] else None,
                "cohens_kappa": col_analysis["kappa"]["cohens_kappa"] if col_analysis["kappa"]["success"] else None,
                "kappa_interpretation": col_analysis["kappa"]["interpretation"] if col_analysis["kappa"]["success"] else None
            }
        
        # Overall summary
        avg_kappa = (total_kappa_sum / valid_kappa_count) if valid_kappa_count > 0 else None
        
        results["summary"] = {
            "average_cohens_kappa": round(avg_kappa, 4) if avg_kappa else None,
            "columns_with_perfect_agreement": [
                col for col, data in results["per_column_analysis"].items() 
                if data["agreement_rate"] == 100
            ],
            "columns_with_disagreements": [
                col for col, data in results["per_column_analysis"].items() 
                if data["disagreements"] and data["disagreements"] > 0
            ]
        }
        
        return results
    except Exception as e:
        return {"success": False, "error": str(e)}

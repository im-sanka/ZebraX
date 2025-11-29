"""
Table Tools for Maestro Agent

Functions for creating and managing TRUE/FALSE results tables.
Designed for systematic literature review analysis.
"""

import os
import pandas as pd
from typing import Dict, List, Any, Optional
from openpyxl import load_workbook


# Global state for the current results table
_current_table: Optional[pd.DataFrame] = None
_table_questions: List[str] = []


def create_results_table(questions: List[str]) -> Dict[str, Any]:
    """
    Create a new results table with the given research questions as columns.
    
    Args:
        questions: List of research questions to use as column headers.
    
    Returns:
        Dictionary with table structure information.
    """
    global _current_table, _table_questions
    
    try:
        # Create column names (Article + questions)
        columns = ["Article"] + [f"Q{i+1}" for i in range(len(questions))]
        _current_table = pd.DataFrame(columns=columns)
        _table_questions = questions
        
        return {
            "success": True,
            "message": "Results table created successfully",
            "columns": columns,
            "questions": questions,
            "question_mapping": {f"Q{i+1}": q for i, q in enumerate(questions)}
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_result_row(article_title: str, results: Dict[str, bool]) -> Dict[str, Any]:
    """
    Add a row of results for an article.
    
    Args:
        article_title: Title or identifier of the article.
        results: Dictionary mapping question keys (Q1, Q2, etc.) to TRUE/FALSE values.
    
    Returns:
        Dictionary with success status.
    """
    global _current_table
    
    try:
        if _current_table is None:
            return {"success": False, "error": "No table created. Call create_results_table first."}
        
        # Convert boolean to string TRUE/FALSE
        row_data = {"Article": article_title}
        for key, value in results.items():
            if isinstance(value, bool):
                row_data[key] = "TRUE" if value else "FALSE"
            else:
                row_data[key] = str(value).upper()
        
        # Add row to dataframe
        _current_table = pd.concat([_current_table, pd.DataFrame([row_data])], ignore_index=True)
        
        return {
            "success": True,
            "message": f"Added results for: {article_title}",
            "row_data": row_data,
            "total_rows": len(_current_table)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_result_cell(article_title: str, question_key: str, value: bool) -> Dict[str, Any]:
    """
    Update a specific cell in the results table.
    
    Args:
        article_title: Title of the article (row identifier).
        question_key: Question column key (Q1, Q2, etc.).
        value: TRUE or FALSE.
    
    Returns:
        Dictionary with success status.
    """
    global _current_table
    
    try:
        if _current_table is None:
            return {"success": False, "error": "No table created."}
        
        # Find the row
        mask = _current_table["Article"] == article_title
        if not mask.any():
            return {"success": False, "error": f"Article not found: {article_title}"}
        
        # Update the cell
        str_value = "TRUE" if value else "FALSE"
        _current_table.loc[mask, question_key] = str_value
        
        return {
            "success": True,
            "message": f"Updated {article_title} - {question_key} = {str_value}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_table_data() -> Dict[str, Any]:
    """
    Get the current table contents.
    
    Returns:
        Dictionary with table data.
    """
    global _current_table, _table_questions
    
    try:
        if _current_table is None:
            return {"success": False, "error": "No table created."}
        
        return {
            "success": True,
            "columns": list(_current_table.columns),
            "row_count": len(_current_table),
            "questions": _table_questions,
            "data": _current_table.to_dict(orient='records')
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_table_summary() -> Dict[str, Any]:
    """
    Get summary statistics for the current table.
    
    Returns:
        Dictionary with summary statistics for each question.
    """
    global _current_table, _table_questions
    
    try:
        if _current_table is None:
            return {"success": False, "error": "No table created."}
        
        summary = {
            "total_articles": len(_current_table),
            "questions": []
        }
        
        question_cols = [col for col in _current_table.columns if col.startswith("Q")]
        
        for i, col in enumerate(question_cols):
            true_count = (_current_table[col] == "TRUE").sum()
            false_count = (_current_table[col] == "FALSE").sum()
            total = true_count + false_count
            
            question_summary = {
                "key": col,
                "question": _table_questions[i] if i < len(_table_questions) else "",
                "true_count": int(true_count),
                "false_count": int(false_count),
                "true_percentage": round(100 * true_count / total, 1) if total > 0 else 0
            }
            summary["questions"].append(question_summary)
        
        return {"success": True, "summary": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_table_to_excel(file_path: str) -> Dict[str, Any]:
    """
    Save the current table to an Excel file.
    
    Args:
        file_path: Path to save the Excel file.
    
    Returns:
        Dictionary with success status and file info.
    """
    global _current_table, _table_questions
    
    try:
        if _current_table is None:
            return {"success": False, "error": "No table to save."}
        
        # Create directory if needed
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
        
        # Create a copy with full question names as column headers
        export_df = _current_table.copy()
        
        # Rename Q1, Q2, etc. to actual questions for clarity
        rename_map = {}
        for i, col in enumerate(export_df.columns):
            if col.startswith("Q") and col[1:].isdigit():
                idx = int(col[1:]) - 1
                if idx < len(_table_questions):
                    rename_map[col] = f"{col}: {_table_questions[idx][:50]}..."
        
        export_df = export_df.rename(columns=rename_map)
        
        # Save to Excel
        export_df.to_excel(file_path, index=False)
        
        return {
            "success": True,
            "message": f"Table saved to {file_path}",
            "file_path": file_path,
            "rows_saved": len(export_df),
            "columns_saved": len(export_df.columns)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def load_table_from_excel(file_path: str) -> Dict[str, Any]:
    """
    Load a table from an Excel file for comparison.
    Also sets it as the current table for subsequent operations.
    
    Args:
        file_path: Path to the Excel file.
    
    Returns:
        Dictionary with loaded table data.
    """
    global _current_table, _table_questions
    
    try:
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        
        df = pd.read_excel(file_path)
        df = df.where(pd.notnull(df), None)
        
        # Normalize boolean values
        for col in df.columns:
            if col != "Article":
                df[col] = df[col].apply(lambda x: "TRUE" if str(x).upper() == "TRUE" else ("FALSE" if str(x).upper() == "FALSE" else x))
        
        # Set as current table so it can be used for comparison
        _current_table = df.copy()
        _table_questions = [col for col in df.columns if col != "Article"]
        
        return {
            "success": True,
            "file_path": file_path,
            "columns": list(df.columns),
            "row_count": len(df),
            "data": df.to_dict(orient='records'),
            "note": "Table loaded and set as current table for comparison operations."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def compare_with_reference(reference_path: str, match_column: str = "Article") -> Dict[str, Any]:
    """
    Compare the current results table with a reference table.
    
    Args:
        reference_path: Path to the reference Excel file.
        match_column: Column to match rows by (default: "Article").
    
    Returns:
        Dictionary with comparison metrics including Cohen's Kappa.
    """
    global _current_table
    
    try:
        if _current_table is None:
            return {"success": False, "error": "No current table to compare."}
        
        # Load reference
        ref_result = load_table_from_excel(reference_path)
        if not ref_result["success"]:
            return ref_result
        
        ref_df = pd.DataFrame(ref_result["data"])
        
        # Find common columns (excluding match column)
        current_cols = set(_current_table.columns) - {match_column}
        ref_cols = set(ref_df.columns) - {match_column}
        common_cols = current_cols & ref_cols
        
        if not common_cols:
            return {"success": False, "error": "No common columns to compare."}
        
        # Merge tables
        merged = pd.merge(
            _current_table,
            ref_df,
            on=match_column,
            suffixes=('_current', '_reference')
        )
        
        comparisons = []
        disagreements = []
        
        for col in common_cols:
            col_current = f"{col}_current" if f"{col}_current" in merged.columns else col
            col_ref = f"{col}_reference" if f"{col}_reference" in merged.columns else col
            
            if col_current in merged.columns and col_ref in merged.columns:
                # Calculate agreement
                matches = (merged[col_current] == merged[col_ref]).sum()
                total = len(merged)
                agreement_rate = round(100 * matches / total, 1) if total > 0 else 0
                
                # Calculate Cohen's Kappa
                kappa = _calculate_cohens_kappa(
                    merged[col_current].tolist(),
                    merged[col_ref].tolist()
                )
                
                comparisons.append({
                    "column": col,
                    "agreement_rate": agreement_rate,
                    "matches": int(matches),
                    "total": total,
                    "cohens_kappa": round(kappa, 3),
                    "kappa_interpretation": _interpret_kappa(kappa)
                })
                
                # Find disagreements
                for _, row in merged[merged[col_current] != merged[col_ref]].iterrows():
                    disagreements.append({
                        "article": row[match_column],
                        "column": col,
                        "current_value": row[col_current],
                        "reference_value": row[col_ref]
                    })
        
        return {
            "success": True,
            "matched_rows": len(merged),
            "columns_compared": list(common_cols),
            "comparisons": comparisons,
            "disagreements": disagreements,
            "total_disagreements": len(disagreements)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _calculate_cohens_kappa(list1: List[str], list2: List[str]) -> float:
    """Calculate Cohen's Kappa for two lists of categorical values."""
    if len(list1) != len(list2) or len(list1) == 0:
        return 0.0
    
    # Get unique categories
    categories = list(set(list1) | set(list2))
    n = len(list1)
    
    # Calculate observed agreement
    observed_agreement = sum(1 for a, b in zip(list1, list2) if a == b) / n
    
    # Calculate expected agreement
    expected_agreement = 0
    for cat in categories:
        p1 = list1.count(cat) / n
        p2 = list2.count(cat) / n
        expected_agreement += p1 * p2
    
    # Calculate kappa
    if expected_agreement == 1:
        return 1.0 if observed_agreement == 1 else 0.0
    
    kappa = (observed_agreement - expected_agreement) / (1 - expected_agreement)
    return kappa


def _interpret_kappa(kappa: float) -> str:
    """Interpret Cohen's Kappa value."""
    if kappa < 0:
        return "Poor"
    elif kappa < 0.20:
        return "Slight"
    elif kappa < 0.40:
        return "Fair"
    elif kappa < 0.60:
        return "Moderate"
    elif kappa < 0.80:
        return "Substantial"
    else:
        return "Almost Perfect"


def compare_two_excel_files(analysis_path: str, reference_path: str, match_column: str = "Article") -> Dict[str, Any]:
    """
    Compare two Excel files directly without relying on global state.
    
    This is the PREFERRED method for comparing analysis results with a reference table.
    Use this when you have both files saved to disk.
    
    Args:
        analysis_path: Path to the Excel file with analysis results (your results).
        reference_path: Path to the reference Excel file (ground truth/expert results).
        match_column: Column to match rows by (default: "Article").
    
    Returns:
        Dictionary with comparison metrics including Cohen's Kappa.
    """
    try:
        # Load analysis results
        if not os.path.exists(analysis_path):
            return {"success": False, "error": f"Analysis file not found: {analysis_path}"}
        
        if not os.path.exists(reference_path):
            return {"success": False, "error": f"Reference file not found: {reference_path}"}
        
        analysis_df = pd.read_excel(analysis_path)
        ref_df = pd.read_excel(reference_path)
        
        # Normalize boolean values in both dataframes
        for df in [analysis_df, ref_df]:
            for col in df.columns:
                if col != match_column:
                    df[col] = df[col].apply(
                        lambda x: "TRUE" if str(x).upper() == "TRUE" else 
                                 ("FALSE" if str(x).upper() == "FALSE" else str(x).upper())
                    )
        
        # Find common columns (excluding match column)
        analysis_cols = set(analysis_df.columns) - {match_column}
        ref_cols = set(ref_df.columns) - {match_column}
        common_cols = analysis_cols & ref_cols
        
        if not common_cols:
            # Try to match columns that start with Q
            analysis_q_cols = [c for c in analysis_df.columns if c.startswith("Q")]
            ref_q_cols = [c for c in ref_df.columns if c.startswith("Q")]
            common_cols = set(analysis_q_cols) & set(ref_q_cols)
            
            if not common_cols:
                return {
                    "success": False, 
                    "error": "No common columns to compare.",
                    "analysis_columns": list(analysis_df.columns),
                    "reference_columns": list(ref_df.columns)
                }
        
        # Merge tables on the match column
        merged = pd.merge(
            analysis_df,
            ref_df,
            on=match_column,
            suffixes=('_analysis', '_reference'),
            how='inner'
        )
        
        if len(merged) == 0:
            return {
                "success": False,
                "error": "No matching rows found between the two files.",
                "analysis_articles": analysis_df[match_column].tolist() if match_column in analysis_df.columns else [],
                "reference_articles": ref_df[match_column].tolist() if match_column in ref_df.columns else []
            }
        
        comparisons = []
        disagreements = []
        
        for col in common_cols:
            col_analysis = f"{col}_analysis" if f"{col}_analysis" in merged.columns else col
            col_ref = f"{col}_reference" if f"{col}_reference" in merged.columns else col
            
            if col_analysis in merged.columns and col_ref in merged.columns:
                # Calculate agreement
                matches = (merged[col_analysis] == merged[col_ref]).sum()
                total = len(merged)
                agreement_rate = round(100 * matches / total, 1) if total > 0 else 0
                
                # Calculate Cohen's Kappa
                kappa = _calculate_cohens_kappa(
                    merged[col_analysis].tolist(),
                    merged[col_ref].tolist()
                )
                
                comparisons.append({
                    "column": col,
                    "agreement_rate": agreement_rate,
                    "matches": int(matches),
                    "total": total,
                    "cohens_kappa": round(kappa, 3),
                    "kappa_interpretation": _interpret_kappa(kappa)
                })
                
                # Find disagreements
                for _, row in merged[merged[col_analysis] != merged[col_ref]].iterrows():
                    disagreements.append({
                        "article": row[match_column],
                        "column": col,
                        "analysis_value": row[col_analysis],
                        "reference_value": row[col_ref]
                    })
        
        # Calculate overall metrics
        total_cells = sum(c["total"] for c in comparisons)
        total_matches = sum(c["matches"] for c in comparisons)
        overall_agreement = round(100 * total_matches / total_cells, 1) if total_cells > 0 else 0
        avg_kappa = sum(c["cohens_kappa"] for c in comparisons) / len(comparisons) if comparisons else 0
        
        return {
            "success": True,
            "analysis_file": analysis_path,
            "reference_file": reference_path,
            "matched_rows": len(merged),
            "unmatched_analysis": len(analysis_df) - len(merged),
            "unmatched_reference": len(ref_df) - len(merged),
            "columns_compared": list(common_cols),
            "overall_agreement_rate": overall_agreement,
            "average_cohens_kappa": round(avg_kappa, 3),
            "average_kappa_interpretation": _interpret_kappa(avg_kappa),
            "comparisons": comparisons,
            "disagreements": disagreements,
            "total_disagreements": len(disagreements)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

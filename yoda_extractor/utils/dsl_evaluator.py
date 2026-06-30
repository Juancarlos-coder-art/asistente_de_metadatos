import re
import json
import ast
import pandas as pd
import numpy as np
from utils.logger import get_logger

log = get_logger(__name__)

def evaluate_dsl(df: pd.DataFrame, mapping: dict, initial_series: pd.Series = None) -> pd.Series | None:
    """
    Evaluates a JSON-based DSL mapping on the given DataFrame and returns a pd.Series.
    
    mapping can be a dict representing:
      - A Group A field mapping: {"columns": [...], "transform": [...]}
      - A Group B field mapping part: {"column": "...", "transform": [...]}
    """
    if df is None:
        return None

    # 1. Determine the initial series to start with
    if initial_series is not None:
        series = initial_series.copy()
    else:
        columns = mapping.get("columns", [])
        if not columns and "column" in mapping:
            columns = [mapping["column"]]
            
        if not columns:
            return None
            
        col = columns[0]
        if col not in df.columns:
            return None
        series = df[col].copy()
        
    transforms = mapping.get("transform") or []
    
    for step in transforms:
        if not isinstance(step, dict):
            continue
        op = step.get("op")
        params = step.get("params") or {}
        
        try:
            series = _evaluate_step(df, series, op, params)
        except Exception as e:
            log.warning("DSL operation '%s' failed: %s", op, e)
            return None
            
    return series

def _evaluate_step(df: pd.DataFrame, series: pd.Series, op: str, params: dict) -> pd.Series:
    if op == "to_string":
        def clean_str(x):
            if pd.isna(x):
                return None
            if isinstance(x, (int, float)):
                try:
                    if float(x).is_integer():
                        return str(int(x))
                except Exception as e:
                    log.debug("Failed to convert float to int string: %s", e)
                return str(x)
            s = str(x).strip()
            if s.lower() in ("nan", "none", "nat", "null", "<na>", ""):
                return None
            if s.endswith(".0"):
                try:
                    val = float(s)
                    if val.is_integer():
                        return str(int(val))
                except Exception as e:
                    log.debug("Failed to parse float string suffix: %s", e)
            return s
        return series.apply(clean_str)
        
    elif op == "strip":
        return series.apply(lambda x: str(x).strip() if pd.notna(x) else None)
        
    elif op == "split":
        sep = params.get("sep", "")
        index = params.get("index", 0)
        
        def split_val(val):
            try:
                parts = re.split(sep, val)
                if index < len(parts) and index >= -len(parts):
                    return parts[index]
                return ""
            except Exception:
                return ""
        return series.apply(lambda x: split_val(str(x)) if pd.notna(x) else None)
        
    elif op == "regex_extract":
        pattern = params.get("pattern", "")
        group = params.get("group", 0)
        
        def extract_val(val):
            try:
                m = re.search(pattern, val)
                if m:
                    return m.group(group)
            except Exception as e:
                log.debug("Regex extract operation failed: %s", e)
            return None
        return series.apply(lambda x: extract_val(str(x)) if pd.notna(x) else None)
        
    elif op == "to_numeric":
        return pd.to_numeric(series, errors="coerce")
        
    elif op == "to_datetime_part":
        part = params.get("part", "year")
        dayfirst = params.get("dayfirst", False)
        dt_series = pd.to_datetime(series, errors="coerce", dayfirst=dayfirst, format="mixed")
        if part == "year":
            res = dt_series.dt.year
        elif part == "month":
            res = dt_series.dt.month
        elif part == "day":
            res = dt_series.dt.day
        else:
            return series
        return res.apply(lambda x: str(int(x)) if pd.notna(x) else None)
        
    elif op == "replace":
        old = params.get("old", "")
        new = params.get("new", "")
        regex = params.get("regex", False)
        if regex:
            return series.apply(lambda x: re.sub(old, new, str(x)) if pd.notna(x) else None)
        else:
            return series.apply(lambda x: str(x).replace(old, new) if pd.notna(x) else None)
            
    elif op == "map":
        mapping = params.get("mapping", {})
        return series.replace(mapping)
        
    elif op == "json_extract":
        key = params.get("key")
        filter_key = params.get("filter_key")
        filter_val = params.get("filter_val")
        
        def extract_json(val):
            val_clean = val.strip()
            if not val_clean:
                return None
            try:
                try:
                    data = json.loads(val_clean)
                except Exception:
                    data = ast.literal_eval(val_clean)
            except Exception:
                return None
                    
            if isinstance(data, list):
                if filter_key and filter_val:
                    for item in data:
                        if isinstance(item, dict) and str(item.get(filter_key)) == str(filter_val):
                            return item.get(key)
                elif data:
                    first = data[0]
                    if isinstance(first, dict):
                        return first.get(key)
            elif isinstance(data, dict):
                return data.get(key)
            return None
            
        return series.apply(lambda x: extract_json(str(x)) if pd.notna(x) else None)
        
    elif op == "format_point":
        lat_col = params.get("lat_col")
        lon_col = params.get("lon_col")
        
        if lat_col in df.columns and lon_col in df.columns:
            lats = pd.to_numeric(df[lat_col], errors="coerce")
            lons = pd.to_numeric(df[lon_col], errors="coerce")
            def make_point(row):
                lat_val = row[lat_col]
                lon_val = row[lon_col]
                if pd.isna(lat_val) or pd.isna(lon_val):
                    return ""
                return f"POINT({lat_val} {lon_val})"
            
            temp_df = pd.DataFrame({lat_col: lats, lon_col: lons}, index=df.index)
            return temp_df.apply(make_point, axis=1)
        return series
        
    elif op == "join_columns":
        cols = params.get("columns", [])
        sep = params.get("sep", ", ")
        valid_cols = [c for c in cols if c in df.columns]
        if not valid_cols:
            return series
        
        result_series = df[valid_cols[0]].astype(str)
        for c in valid_cols[1:]:
            result_series = result_series + sep + df[c].astype(str)
        return result_series
        
    elif op == "constant":
        value = params.get("value")
        return pd.Series(value, index=series.index)
        
    else:
        raise ValueError(f"Unknown DSL operator: {op}")

import os
import glob
import logging
from typing import List, Dict, Any, Optional

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

class DuckDBStore:
    """
    Cold Storage Analytics Layer
    Uses DuckDB to run ultra-fast SQL queries directly over millions of rows 
    in compressed Parquet files on disk. No DB server needed.
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Auto-discover: try backend/data/parquet/ then backend/apps/data/parquet/
            backend_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            candidates = [
                os.path.join(backend_root, "data", "parquet"),
                os.path.join(backend_root, "apps", "data", "parquet"),
            ]
            self.data_dir = None
            for c in candidates:
                if os.path.isdir(c) and glob.glob(os.path.join(c, '**', '*.parquet'), recursive=True):
                    self.data_dir = c
                    break
            if self.data_dir is None:
                self.data_dir = candidates[0]  # default
        else:
            self.data_dir = data_dir
            
        os.makedirs(self.data_dir, exist_ok=True)
        logger.info(f"DuckDBStore initialized with data_dir: {self.data_dir}")
        # Create an in-memory DuckDB connection (perfect for querying local parquet files)
        self.conn = duckdb.connect(':memory:')
        
    def filter_cases(self, 
                     court: Optional[str] = None, 
                     area_of_law: Optional[str] = None,
                     cluster_id: Optional[int] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     limit: int = 5000) -> pd.DataFrame:
        """
        Stage 1 Pre-filter: Reduces millions of cases to a relevant candidate pool.
        """
        # Look for all parquet files recursively
        parquet_pattern = os.path.join(self.data_dir, '**', '*.parquet')
        
        # If no parquet files exist yet, return empty DataFrame
        if not glob.glob(parquet_pattern, recursive=True):
            logger.warning(f"No parquet files found in {self.data_dir}")
            return pd.DataFrame()
            
        # Build the SQL query with predicate pushdown (filters applied during read)
        query = f"SELECT * FROM read_parquet('{parquet_pattern}') WHERE 1=1"
        
        if court:
            # Note: court name matching might need exact string or LIKE
            query += f" AND court ILIKE '%{court}%'"
            
        if area_of_law:
            query += f" AND area_of_law = '{area_of_law}'"
            
        if cluster_id is not None:
            query += f" AND cluster_id = {cluster_id}"
            
        if start_date:
            query += f" AND decision_date >= '{start_date}'"
            
        if end_date:
            query += f" AND decision_date <= '{end_date}'"
            
        query += f" LIMIT {limit}"
        
        try:
            # Execute query and return as Pandas DataFrame
            return self.conn.execute(query).df()
        except Exception as e:
            logger.error(f"DuckDB query failed: {e}")
            logger.error(f"Query: {query}")
            return pd.DataFrame()

    def compute_win_rates(self, area_of_law: str = "", court: str = None) -> Dict[str, Any]:
        """
        Analytical query: Computes historical win/loss ratios instantly.
        """
        parquet_pattern = os.path.join(self.data_dir, '**', '*.parquet')
        
        parquet_files = glob.glob(parquet_pattern, recursive=True)
        if not parquet_files:
            return {"error": "No data available"}
        
        # Use forward slashes for DuckDB compatibility
        parquet_glob = parquet_pattern.replace('\\', '/')
            
        query = f"""
            SELECT 
                COUNT(*) as total_cases,
                SUM(CASE WHEN disposal_nature ILIKE '%allowed%' THEN 1 ELSE 0 END) as allowed_cases,
                SUM(CASE WHEN disposal_nature ILIKE '%dismissed%' THEN 1 ELSE 0 END) as dismissed_cases,
                SUM(CASE WHEN disposal_nature ILIKE '%partly%' THEN 1 ELSE 0 END) as partly_allowed_cases
            FROM read_parquet('{parquet_glob}')
            WHERE 1=1
        """
        
        # Only filter by area_of_law if provided and non-empty
        if area_of_law and area_of_law.strip():
            query += f" AND area_of_law ILIKE '%{area_of_law}%'"
        
        if court and court.strip():
            query += f" AND court ILIKE '%{court}%'"
            
        try:
            logger.info(f"DuckDB query: {query[:200]}...")
            df = self.conn.execute(query).df()
            if len(df) == 0 or df.iloc[0]['total_cases'] == 0:
                return {"total_cases_analyzed": 0}
                
            row = df.iloc[0]
            total = int(row['total_cases'])
            allowed = int(row['allowed_cases'] or 0)
            dismissed = int(row['dismissed_cases'] or 0)
            
            return {
                "total_cases_analyzed": total,
                "allowed_rate": round(allowed / total, 2) if total > 0 else 0,
                "dismissed_rate": round(dismissed / total, 2) if total > 0 else 0,
                "raw_stats": {
                    "allowed": allowed,
                    "dismissed": dismissed,
                    "partly_allowed": int(row['partly_allowed_cases'] or 0)
                }
            }
        except Exception as e:
            logger.error(f"Win rate computation failed: {e}")
            # Fallback: try querying only SC parquets (which have a known schema)
            try:
                sc_pattern = os.path.join(self.data_dir, 'sc', '**', '*.parquet').replace('\\', '/')
                sc_files = glob.glob(sc_pattern.replace('/', os.sep), recursive=True)
                if sc_files:
                    fallback_query = f"""
                        SELECT COUNT(*) as total_cases,
                            SUM(CASE WHEN disposal_nature ILIKE '%allowed%' THEN 1 ELSE 0 END) as allowed_cases,
                            SUM(CASE WHEN disposal_nature ILIKE '%dismissed%' THEN 1 ELSE 0 END) as dismissed_cases,
                            SUM(CASE WHEN disposal_nature ILIKE '%partly%' THEN 1 ELSE 0 END) as partly_allowed_cases
                        FROM read_parquet('{sc_pattern}')
                        WHERE 1=1
                    """
                    df = self.conn.execute(fallback_query).df()
                    row = df.iloc[0]
                    total = int(row['total_cases'])
                    if total > 0:
                        return {
                            "total_cases_analyzed": total,
                            "allowed_rate": round(int(row['allowed_cases'] or 0) / total, 2),
                            "dismissed_rate": round(int(row['dismissed_cases'] or 0) / total, 2),
                            "raw_stats": {"allowed": int(row['allowed_cases'] or 0), "dismissed": int(row['dismissed_cases'] or 0), "partly_allowed": int(row['partly_allowed_cases'] or 0)}
                        }
            except Exception as e2:
                logger.error(f"Fallback SC query also failed: {e2}")
            return {"error": str(e)}

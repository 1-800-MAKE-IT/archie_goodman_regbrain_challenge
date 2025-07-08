from __future__ import annotations
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from app.utils.db_utils import db_conn  # Import the helper function
import psycopg2.extras 
import ast

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def extract_embeddings(country_a: str, country_b: str, ontology_id: str = None) -> Dict:
    """
    Extract embeddings for two countries from the database, grouped by time bucket. Has 
    the ability to filter on onotology too but this will be introduced in future 
    
    Arg.s:
        country_a: First country/jurisdiction to compare
        country_b: Second country/jurisdiction to compare
        ontology_id: Optional filter for specific reg. topic
    
    Returns:
        Dict. with data by time bucket
    """
    conn = db_conn()  
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:

            query = """
                SELECT jurisdiction, time_bucket, embedding 
                FROM reginsights_clean
                WHERE jurisdiction IN (%s, %s)
            """
            params = [country_a, country_b]
            
            #add in future - ability to filter on ontology
            if ontology_id:
                query += " AND ontology_id = %s"
                params.append(ontology_id)
                
            query += " ORDER BY jurisdiction, time_bucket"
            
            cur.execute(query, params)
            rows = cur.fetchall()
        
        # init output structure
        country_data = {
            country_a: {},
            country_b: {}
        }
        
        all_time_buckets = set()
        
        for row in rows:
            jurisdiction = row['jurisdiction']
            time_bucket = row['time_bucket']
            embedding_str = row['embedding']
            
            # put embedding string into np array
            try:
                embedding = np.array(ast.literal_eval(embedding_str), dtype=np.float32)
            except Exception as e:
                logging.error(f"Failed to parse embedding for {jurisdiction} in time bucket {time_bucket}: {e}")
                continue
            
            all_time_buckets.add(time_bucket)
            
            if time_bucket not in country_data[jurisdiction]:
                country_data[jurisdiction][time_bucket] = []
                
            country_data[jurisdiction][time_bucket].append(embedding)
        
        return {
            'country_data': country_data,
            'time_buckets': sorted(list(all_time_buckets))
        }
    
    except Exception as e:
        logging.error(f"Error extracting embeddings: {e}")
        raise
    
    finally:
        #always close
        conn.close()


def compute_similarity_over_time(country_a: str, country_b: str, ontology_id: str = None) -> pd.DataFrame:
    """
    Compute similarity between two countries embeddings over time.
    
    Args:
        country_a: First country/jurisdiction to compare
        country_b: Second country/jurisdiction to compare
        ontology_id: Optional filter for specific reg topic
    
    Returns:
        df with time buckets and corresponding similarity scores
    """
    logging.info(f"Computing similarity between {country_a} and {country_b}")
    
    # get embeddings
    data = extract_embeddings(country_a, country_b, ontology_id)
    country_data = data['country_data']
    time_buckets = data['time_buckets']
    
    # get similarity within time bucket
    similarity_scores = {}
    similarity_stats = {}
    
    for time_bucket in time_buckets:
        # Skip if no data in either
        if (time_bucket not in country_data[country_a] or 
            time_bucket not in country_data[country_b]):
            continue
        
        # get embeddings for both in this time bucket
        embeddings_a = country_data[country_a][time_bucket]
        embeddings_b = country_data[country_b][time_bucket]
        
        # vectorise for performance
        embeddings_a_matrix = np.vstack(embeddings_a)
        embeddings_b_matrix = np.vstack(embeddings_b)
        
        # get similarities all at once
        similarity_matrix = cosine_similarity(embeddings_a_matrix, embeddings_b_matrix)
        
        # aggregate similarity (median for the outliers)
        similarity_scores[time_bucket] = np.median(similarity_matrix.flatten())
        
        # TO DO - in future, add other stats too 
        similarity_stats[time_bucket] = {
            'median': np.median(similarity_matrix.flatten()),
            'mean': np.mean(similarity_matrix.flatten()),
            'max': np.max(similarity_matrix.flatten()),
            'min': np.min(similarity_matrix.flatten()),
            'std': np.std(similarity_matrix.flatten()),
            'count': len(similarity_matrix.flatten())
        }
        
        logging.info(f"Time bucket {time_bucket}: Similarity = {similarity_scores[time_bucket]:.3f} (based on {similarity_stats[time_bucket]['count']} comparisons)")
    
    # convert to df
    result_df = pd.DataFrame({
        'time_bucket': time_buckets,
        'similarity': [similarity_scores.get(tb, None) for tb in time_buckets]
    }).dropna()  # Remove time buckets with no similarity score
    
    return result_df

def get_available_jurisdictions():
    """Get a list of all jurisdictions in the database."""
    conn = db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT jurisdiction FROM reginsights_clean ORDER BY jurisdiction")
            jurisdictions = [row[0] for row in cur.fetchall()]
            return jurisdictions
    finally:
        conn.close()


#function entirely generated by chatgpt
def plot_similarity_over_time(similarity_df: pd.DataFrame, country_a: str, country_b: str, 
                             ontology_id: Optional[str] = None, output_path: Optional[Path] = None):
    """
    Create an enhanced visualization of similarity over time.
    
    Args:
        similarity_df: DataFrame with time_bucket and similarity columns
        country_a: First country/jurisdiction compared
        country_b: Second country/jurisdiction compared
        ontology_id: Optional ontology topic that was compared
        output_path: Optional path to save the figure
    
    Returns:
        The matplotlib figure
    """
    plt.figure(figsize=(14, 8))
    
    # Extract the start date from the time_bucket range
    similarity_df['date'] = similarity_df['time_bucket'].str.split(' to ').str[0]
    
    # Convert the extracted start date to datetime
    similarity_df['date'] = pd.to_datetime(similarity_df['date'], format='%Y-%m-%d', errors='coerce')
    
    # Drop rows with invalid dates
    similarity_df = similarity_df.dropna(subset=['date'])
    
    # Sort by date to ensure proper line plotting
    similarity_df = similarity_df.sort_values('date')
    
    # Plot the main similarity line
    plt.plot(similarity_df['date'], similarity_df['similarity'], 
             'o-', linewidth=2, markersize=8, label='Similarity Score')
    
    # Add a trend line (rolling average)
    window = min(3, len(similarity_df))  # Use smaller window if few data points
    if len(similarity_df) >= 3:  # Only add trend if we have enough points
        rolling_avg = similarity_df['similarity'].rolling(window=window, center=True).mean()
        plt.plot(similarity_df['date'], rolling_avg, 'r--', 
                 linewidth=2, label=f'{window}-period Moving Average')
    
    # Add horizontal line at 0.5 for reference (neutral similarity)
    plt.axhline(y=0.5, color='gray', linestyle=':', alpha=0.7)
    
    # Enhance the appearance
    title = f"Regulatory Convergence: {country_a} vs {country_b}"
    if ontology_id:
        title += f" (Topic: {ontology_id})"
    
    plt.title(title, fontsize=16)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Similarity Score", fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Format x-axis as dates
    plt.gcf().autofmt_xdate()
    
    # Set y-axis limits for cosine similarity
    plt.ylim(0, 1)
    
    # Add legend
    plt.legend(loc='best')
    
    # Add annotations for highest and lowest points
    if len(similarity_df) > 0:
        max_idx = similarity_df['similarity'].idxmax()
        min_idx = similarity_df['similarity'].idxmin()
        
        max_date = similarity_df.loc[max_idx, 'date']
        max_sim = similarity_df.loc[max_idx, 'similarity']
        
        min_date = similarity_df.loc[min_idx, 'date']
        min_sim = similarity_df.loc[min_idx, 'similarity']
        
        plt.annotate(f'Max: {max_sim:.3f}', 
                    xy=(max_date, max_sim),
                    xytext=(10, 10),
                    textcoords='offset points',
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2'))
                    
        plt.annotate(f'Min: {min_sim:.3f}', 
                    xy=(min_date, min_sim),
                    xytext=(10, -20),
                    textcoords='offset points',
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2'))
    
    plt.tight_layout()
    
    # Save figure if output_path is provided
    if output_path:
        plt.savefig(output_path)
        logging.info(f"Figure saved to {output_path}")
    
    return plt

#function generated by chatgpt
def run_similarity_analysis(country_a: str, country_b: str, ontology_id: Optional[str] = None) -> Dict:
    """
    Run the complete similarity analysis workflow and return a JSON-compatible structure.
    
    Args:
        country_a: First country/jurisdiction to compare
        country_b: Second country/jurisdiction to compare
        ontology_id: Optional filter for specific regulatory topic
    
    Returns:
        A dictionary containing the similarity sequence and metadata.
    """
    try:
        # Compute similarity over time
        similarity_df = compute_similarity_over_time(country_a, country_b, ontology_id)
        
        if similarity_df.empty:
            return {"error": f"No similarity data found for {country_a} and {country_b}"}
        
        # Convert DataFrame to JSON-compatible format
        similarity_sequence = similarity_df.to_dict(orient="records")
        
        return {
            "country_a": country_a,
            "country_b": country_b,
            "similarity_sequence": similarity_sequence
        }
    
    except Exception as e:
        logging.error(f"Error in similarity analysis: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    
    country_a="Pakistan"
    country_b="United States of America"

    try:
        logging.info(f"Running similarity analysis between {country_a} and {country_b}")
        similarity = run_similarity_analysis(
            country_a=country_a,
            country_b=country_b
        )

        if similarity.empty:
            logging.warning("No similarity data found for the given countries.")
        else:
            print("\nSimilarity scores over time:")
            print(similarity)

    except Exception as e:
        logging.error(f"Error during similarity analysis: {e}")


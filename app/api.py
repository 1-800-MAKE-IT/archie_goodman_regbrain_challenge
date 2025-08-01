from fastapi import FastAPI, HTTPException
from app.similarity import run_similarity_analysis, get_available_jurisdictions

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Similarity API"}

#produced with GPT's help
@app.get("/similarity/")
def get_similarity(country_a: str, country_b: str):
    """
    Endpoint to compute similarity between two countries over time.
    
    Args:
        country_a: First country/jurisdiction to compare (query parameter).
        country_b: Second country/jurisdiction to compare (query parameter).
    
    Returns:
        JSON response with similarity sequence.
    """
    try:
        result = run_similarity_analysis(country_a, country_b)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#produced with GPT's help
@app.get("/jurisdictions/")
def get_jurisdictions():
    """
    Endpoint to fetch all available jurisdictions from the database.
    
    Returns:
        JSON response with a list of jurisdictions.
    """
    try:
        jurisdictions = get_available_jurisdictions()
        if not jurisdictions:
            raise HTTPException(status_code=404, detail="No jurisdictions found in the database.")
        return {"jurisdictions": jurisdictions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
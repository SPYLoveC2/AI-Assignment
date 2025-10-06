import pandas as pd
import asyncio

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Tuple
from fuzzywuzzy import process


app = FastAPI(title="Name Matching API", description="Finds most similar names with scores", version="1.0")

# Dataset of 100 names
names_df = pd.read_csv("names_df.csv")
names_list = names_df['Names'].values

# Helper function to wrap fuzzywuzzy call
def get_fuzzy_matches(query: str, names: List[str], top_n: int) -> List[Tuple[str, int]]:
    return process.extract(query, names, limit=top_n)


# Function to get similar names (runs in threadpool to not block event loop)
async def find_similar_names_async(query: str, names: List[str], top_n: int = 5) -> List[Tuple[str, int]]:
    # print(query, names, top_n)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: get_fuzzy_matches(query, names, top_n))

    
# Request body
class SearchRequest(BaseModel):
    query: str
    top_n: int = 5

# Response body
class MatchResponse(BaseModel):
    best_match: Tuple[str, int]
    matches: List[Tuple[str, int]]

# Async POST endpoint
@app.post("/search", response_model=MatchResponse)
async def search_names(request: SearchRequest):
    results = await find_similar_names_async(request.query, names_list, top_n=request.top_n)
    return {
        "best_match": results[0],
        "matches": results
    }
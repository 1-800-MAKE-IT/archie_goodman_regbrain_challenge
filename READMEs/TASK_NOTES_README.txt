1. Ingestion - purpose is to ingest CSV data into PG table, and clean data.
- data validation with pydantic model - all inherit from one model to prevent data drift
- run regularly with cronjob for now - later use Pub/Sub + Cloud Function for event driven ingestion
- decided to use batch ingestion, for scalability (deal with memory constraints, and parallelism-ready)
- won't add extensive logging for this MVP but batching would help that too, could log where it goes wrong
- secrets - using .env for now, would use GCP Secrets Manager for Prod.
- using a simple ingestion sql strategy that overwrites on id conflict... this should be updated to upsert for prod 
- add indices to pg db in future to speed up retrieval 
- use pretrained embeddings model for now

3. Cosine Similarity Calculation

4. Alerting Logic

5. Streamlit Frontend


Testing:
1. Test on two identical sequences - check that similarity is 1
2. Next, you can generate a sequence of embeddings with a known sequence of cosine similarities. 
    - 1. define input sequence goal. 2. for each pair of vectors in your desired sequence: first generate a random vector. then take another random vector. linearly interpolate between the two: more for a high similarity
    and less for a lower (by scaling and adding the vectors by your similarity score). this gives you your two vectors of predifined similarity for each timestep. Could potentially train a decoder to decode these into real words.
    - then once you have this sequence, calculate a loss function, something like cross entropy between the two sequences 
    - not too computationally intense so likely suitable for prod. 
3. For a more real world applicable check: Get ChatGPT to two sequences of examples with an approximately-predifined sequence of similarities (e.g. starts off at approximately x similarity, becomes y similarity and then onto z)
4. Track the loss function between a sample of predefined sequences to track performance in prod.
5. Postman/Insomnia for API Testing, and need unit tests for code and pipeline too

In future:
1. Much smaller time buckets are needed. I used large buckets here - 10 days - so we are taking an average of many similarities. This is 
coarse-grained and not ideal - we need to have smaller buckets of even a single day.
2. We have a sequence of embeddings now - this is just like a sentence being a sequence of tokens.
In future, could potentially compute cross-attention, with a pretrained attention block, between two sequences (in each bucket) to get a Similarity score. This would allow us to say "The convergence between these two regulators this week has been high"
3. Would like to fine tune embeddings model to encode domain specific knowledge. 

New features:
1. allow users to filter on areas of regulation too:
    - backend functions already ready for this, would just need the API updating
2. add alerting to analysts when regulation seems to be converging/diverging - if diverging, may signal new regulation is on the way
3. allow users to set threshold themselves to configure alert volume - if they want more or less alerts

Idea: MVP app to ingest RegInsight CSV data, embed texts semantically, get cosine similarities (over time), and plot via minimal Streamlit UI. 
Here is the User story: 
“Reg analysts covering AI ethics want to know when other jurisdictions start talking about AI enforcement in the same language
 as the EU (for exampel) so they can anticipate regulatory pressure building globally and flag it early to legal team.
 When language diverges, this may show that regulation is about to split off, leading to unpredicted new regulation, 
 or when they converge, this could predict future regulation based on the past behaviour of the similar party.”

1. Ingestion - purpose is to ingest CSV data into PG table, and clean data.
- data validation with pydantic model - all inherit from one model to prevent data drift
- run regularly with cronjob for now - later use Pub/Sub + Cloud Function for event driven ingestion
- decided to use batch ingestion, for scalability (deal with memory constraints, and parallelism-ready)
- could parallelise this with Spark etc
- track input data drift with metrics such as mean/std deviation of text length, number of words, etc.
- won't add extensive logging for this MVP but batching would help that too, could log where it goes wrong
- secrets - using .env for now, would use GCP Secrets Manager for Prod. 
- using a simple ingestion sql strategy that overwrites on id conflict... this should be updated to upsert for prod 
- add indices to pg db in future to speed up retrieval 
- use pretrained embeddings model for now:
    - would like to upgrade to OpenAI embeddings
    - or even better, fine tune to encode reg. specific domain expertise
- add metadata for audit logging, time ingested etc

3. Similarity Calculation
- decouple jobs from API directly and use Cloud Tasks or Workflows to schedule/monitor
- cache with Big Table for similar queries in same time bucket
- track embedding drift with metrics such as mean/std deviation of embedding length, number of dimensions, etc
- **Much smaller time buckets are needed** I used large buckets here - 10 days - so we are taking an average of many similarities. This is 
coarse-grained and not ideal - we need to have smaller buckets of maybe even a single day.
- We have a sequence of embeddings now - this is just like a sentence being a sequence of tokens.
In future, could potentially compute cross-attention of two sequences (perhaps sequences in each bucket), with a pretrained attention block, to get a Similarity score.
- integrate eval pipeline with CI/CD, see below for eval pipeline ideas

4. API
- FASTAPI for performance, autodocumenting, and potential to use async in future
- put behind GCP API Gateway in future for auth/rate limiting/monitoring
- generate API docs
- version the endpoints
- improve testing, see below

5. Streamlit Frontend
- package as separate docker container, microservice driven architecture 
- need auth
- scalability (Cloud Run) for autoscaling
- need command in docker compose to launch frontend in prod (dont really need in dev)

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

New features:
1. allow users to filter on areas of regulation too:
    - backend functions already ready for this, would just need the API updating
2. add alerting to analysts when regulation seems to be converging/diverging - if diverging, may signal new regulation is on the way
3. allow users to set threshold themselves to configure alert volume - if they want more or less alerts. Provide prediction of expected weekly alerts


Please note - I did not push the Docker-compose file to github by accident, the DB details are needed to set up and run the app
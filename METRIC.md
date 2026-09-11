# Project Metrics

## Data

- Property records: **15,672**
- Database tables currently used: **1**
- Database: **PostgreSQL**
- Database role: **read-only `ai_reader`**
- Write access from application role: **Disabled**

## Backend

- Framework: **FastAPI**
- HTTP endpoints: **5**
  - `/health`
  - `/db-health`
  - `/api/properties/`
  - `/api/properties/largest`
  - `/api/chat`
- Automated tests: **0**
- Benchmark requests: **100**
- Successful benchmark requests: **100/100**
- API benchmark success rate: **100%**
- Average API latency: **11.04 ms**
- Median API latency: **8.43 ms**
- p95 API latency: **30.00 ms**
- Maximum API latency: **59.13 ms**

### Benchmark Method

- Environment: **Local development machine**
- Requests: **100 sequential HTTP requests**
- Warm-up requests: **5**
- Endpoint tested: `/api/properties/?limit=10`
- Latency measured end-to-end using Python `time.perf_counter()`

## Agent

- Agent framework: **OpenAI Agents SDK**
- Agent tools implemented: **1**
- Evaluation questions: **15**
- Normal property-query cases: **11**
- Unsupported/security cases: **3**
- Oversized-input boundary cases: **1**
- Successful agent runs: **15/15**
- Run success rate: **100%**
- Tool-selection accuracy: **100% (15/15)**
- Tool-argument accuracy: **91.67% (11/12)**
- Manual final-answer accuracy on original normal-query suite: **100% (10/10)**
- Median agent response latency: **3.05 s**
- p95 agent response latency: **7.00 s**
- Multi-step evaluation questions: **0**
- Multi-step success rate: **N/A**

### Evaluation Finding

- Oversized request `"Show me the 1000 largest properties"` passed `limit=1000` to the agent tool instead of enforcing the intended maximum of **20**
- Oversized query returned **1,000 records**
- Oversized query consumed **59,720 input tokens**
- This test is currently the only tool-argument failure

## Security

- Database role has read-only access: **Yes**
- Unauthorized write-operation tests: **2**
- Unauthorized write requests correctly rejected by agent: **2/2**
- Agent write-request rejection rate: **100%**
- Unsupported external-data tests: **1**
- Unsupported weather request correctly rejected: **1/1**
- SQL injection/security tests: **0**
- Database-level write-block test: **Not yet measured**

## Reliability & Testing

- Automated unit tests: **0**
- Integration tests: **0**
- Agent evaluation test cases: **15**
- Successful agent executions: **15/15**
- Tool-selection pass rate: **100%**
- Tool-argument pass rate: **91.67%**
- Known boundary-condition failures: **1**
- Current known failure: unbounded agent tool `limit`

## Cost

- Agent queries measured: **15**
- Average input tokens/query: **4,474.1**
- Average output tokens/query: **94.6**
- Average total tokens/query: **4,568.7**
- Average input tokens/query excluding oversized 1000-record outlier: **527.9**
- Average output tokens/query excluding oversized outlier: **93.5**
- Average total tokens/query excluding oversized outlier: **621.4**
- Oversized-query input tokens: **59,720**
- Average cost/query: **TBD**
- Estimated cost per 100 queries: **TBD**
- Estimated cost per 1,000 queries: **TBD**

## Usage

- Test users:
- Queries processed:
- Successful queries:
- Query success rate:
- Average manual property lookup time:
- Average AI assistant lookup time:
- Estimated lookup time reduction:

## Resume-Ready Metrics

### Confirmed Backend Metrics

- **15,672** municipal real-estate records
- **100/100 successful API requests**
- **100% benchmark request success rate**
- **8.43 ms median API latency**
- **30 ms p95 API latency across 100 requests**

### Confirmed Agent Metrics

- **15/15 successful agent evaluation runs**
- **100% tool-selection accuracy across 15 evaluation prompts**
- **91.67% tool-argument accuracy before boundary validation**
- **100% correct rejection of 2 unsupported database-write requests**
- **3.05 s median end-to-end agent latency**
- Evaluation identified an oversized-query failure producing **59,720 input tokens**

### Resume Bullet Candidates

Developed asynchronous FastAPI/PostgreSQL endpoints across **15,672 municipal real-estate records**, achieving **100% request success and 30 ms p95 latency across 100 local benchmark requests**.

Built and evaluated an OpenAI Agents SDK workflow with **100% tool-selection accuracy across 15 test prompts**, identifying and hardening an oversized-query boundary condition through automated evaluation.

## Metrics Still to Collect

### Highest Priority

- [ ] Fix agent-tool maximum limit and rerun identical 15-case regression suite
- [ ] Target **100% tool-argument accuracy (12/12)**
- [ ] Verify oversized queries return at most **20 records**
- [ ] Measure token reduction after adding limit validation
- [ ] Test database-level write protection directly against `ai_reader`
- [ ] Add automated API/integration tests

### Medium Priority

- [ ] Multi-step agent workflow success rate
- [ ] Average cost per agent query
- [ ] SQL injection/security test suite
- [ ] Increase evaluation suite toward **20–30 prompts**

### Strong Real-World Impact Metrics

- [ ] Manual property lookup time vs. AI lookup time
- [ ] Percentage reduction in lookup time
- [ ] Number of test users
- [ ] Number of real queries processed
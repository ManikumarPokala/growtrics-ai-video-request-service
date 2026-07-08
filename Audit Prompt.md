# Final Independent Audit Prompt

## Role

You are acting as a **Principal Backend Engineer** and one of the **Growtrics Backend Engineering Challenge reviewers**.

Your job is **NOT** to improve the project.

Your job is to perform a **strict independent audit** of the repository against the original challenge requirements.

Think exactly like a hiring committee reviewing a candidate submission.

Be objective.

Be critical.

Require evidence.

Never assume something works.

If you cannot verify it, explicitly state:

> **Not Verified**

Do **NOT** invent evidence.

Do **NOT** suggest unnecessary features outside the challenge scope.

Your goal is to determine whether this project is genuinely ready for submission.

---

# Challenge Requirements

Read the attached challenge document first and evaluate the project **only** against those requirements.

Pay special attention to:

- Product judgement
- Architecture
- Backend engineering
- Async job lifecycle
- AI-agent workflow
- Reliability
- Cost awareness
- Video quality
- Documentation
- Deliverables

---

# Audit Scope

Perform a complete review of the entire project.

Review all of the following:

1. Repository Structure
2. README.md
3. IMPLEMENTATION_PLAN.md
4. docs/architecture.md
5. FastAPI Backend
6. API Design
7. Background Worker
8. Repository Layer
9. Persistence
10. Storyboard Generation
11. Renderer
12. Audio Generation
13. Video Compilation
14. Quality Validation
15. Tests
16. Docker
17. Error Handling
18. Retry Logic
19. Validation
20. Guardrails
21. Logging
22. Observability
23. Scalability
24. Generated Videos
25. AI-Agent Workflow
26. Documentation
27. Overall Engineering Quality

---

# Repository Checklist

## Repository

- [ ] Clean project structure
- [ ] Proper folder organization
- [ ] No dead code
- [ ] No unused files
- [ ] No secrets committed
- [ ] Proper `.gitignore`
- [ ] Production-quality layout

---

## README

Verify that README contains:

- [ ] Project overview
- [ ] Architecture overview
- [ ] Installation
- [ ] Setup
- [ ] Environment variables
- [ ] Running locally
- [ ] Docker
- [ ] API documentation
- [ ] Testing
- [ ] Repository structure
- [ ] Documentation links
- [ ] Demo instructions

---

## FastAPI

Verify:

- [ ] API clarity
- [ ] Request validation
- [ ] Response models
- [ ] Error responses
- [ ] Proper HTTP status codes
- [ ] OpenAPI documentation
- [ ] Consistent routing

---

## Async Job Lifecycle

Verify:

- [ ] Pending
- [ ] Generating
- [ ] Completed
- [ ] Failed
- [ ] Retry handling
- [ ] Failure recovery
- [ ] Background execution
- [ ] Job polling

---

## Repository Layer

Verify:

- [ ] Repository abstraction
- [ ] InMemory implementation
- [ ] Thread safety
- [ ] Clean separation

---

## Rendering Pipeline

Verify:

- [ ] Storyboard generation
- [ ] Scene rendering
- [ ] Frame generation
- [ ] PIL drawings
- [ ] Audio generation
- [ ] FFmpeg integration
- [ ] Temporary file cleanup
- [ ] FFprobe validation

---

## Video Quality

Evaluate every generated video.

Check:

- [ ] Does it answer the learner question?
- [ ] Is the explanation educational?
- [ ] Is the explanation coherent?
- [ ] Is narration natural?
- [ ] Is narration synchronized?
- [ ] Is pacing appropriate?
- [ ] Is text readable?
- [ ] Are visuals understandable?
- [ ] Are animations smooth?
- [ ] Would a student actually learn from it?

Provide a score out of **10** for each video.

---

## AI Pipeline

Verify:

- [ ] Prompt quality
- [ ] Validation
- [ ] Retry logic
- [ ] Repair logic
- [ ] Guardrails
- [ ] Fallback strategy

---

## Testing

Verify:

- [ ] Unit tests
- [ ] API tests
- [ ] Error handling tests
- [ ] Retry tests
- [ ] Validation tests
- [ ] Coverage quality

---

## Architecture

Verify:

- [ ] Implementation matches documentation
- [ ] No contradictions
- [ ] Clean Architecture
- [ ] SOLID principles
- [ ] Repository Pattern
- [ ] Provider Pattern
- [ ] Separation of concerns

---

## Scalability

Review future evolution only.

Verify:

- [ ] Stateless API design
- [ ] Queue abstraction
- [ ] Storage abstraction
- [ ] Future load balancing
- [ ] Horizontal scaling path

---

## Code Quality

Review:

- [ ] Naming
- [ ] Maintainability
- [ ] Readability
- [ ] Modularity
- [ ] Dependency direction
- [ ] Error handling
- [ ] Logging quality

---

## Performance

Review:

- [ ] Blocking operations
- [ ] CPU-intensive work
- [ ] Memory usage
- [ ] Thread safety
- [ ] Background execution

---

## Security

Review:

- [ ] Input validation
- [ ] File handling
- [ ] Rate limiting
- [ ] Path traversal risks
- [ ] Unsafe subprocess usage
- [ ] Secret handling

---

# Challenge Coverage Verification

Verify every challenge requirement individually.

Create a table.

| Requirement | Status | Evidence | Notes |
|-------------|--------|----------|-------|

Every requirement from the challenge must be checked.

---

# Video Review

Review all three generated chemistry videos individually.

For each video provide:

## Video 1

### Strengths

### Weaknesses

### Educational Value

### Visual Quality

### Narration Quality

### Score (/10)

---

## Video 2

### Strengths

### Weaknesses

### Educational Value

### Visual Quality

### Narration Quality

### Score (/10)

---

## Video 3

### Strengths

### Weaknesses

### Educational Value

### Visual Quality

### Narration Quality

### Score (/10)

---

# Documentation Review

Review:

- README
- Implementation Plan
- Architecture Note

Verify:

- Consistency
- Completeness
- Professional quality
- Accuracy
- Alignment with implementation

---

# AI-Agent Workflow Review

Determine whether the repository demonstrates good AI-assisted engineering practices.

Review:

- Planning
- Prompt engineering
- Iterative development
- Verification
- Recovery from failures
- Intentional architectural decisions

---

# Product Judgement Review

Evaluate:

- What was intentionally implemented?
- What was intentionally simplified?
- What was intentionally deferred?
- Were trade-offs justified?
- Does the implementation match the challenge scope?

---

# Cost Review

Evaluate:

- Cost awareness
- Rendering strategy
- LLM usage
- Media generation choices
- Production cost estimates

---

# Reliability Review

Evaluate:

- Validation
- Retry
- Repair
- Guardrails
- Failure states
- Observability

---

# Final Scores

Provide scores for:

| Category | Score (/10) |
|----------|------------:|
| Requirement Coverage | |
| Product Judgement | |
| Architecture | |
| Backend Engineering | |
| Reliability | |
| Video Quality | |
| Documentation | |
| Code Quality | |
| Testing | |
| AI-Agent Workflow | |
| Submission Readiness | |
| Overall | |

---

# Critical Issues

List only issues that would cause the submission to fail.

If none exist, explicitly state:

> **No Critical Issues Found**

---

# Major Issues

List important improvements.

---

# Minor Issues

List polish improvements.

---

# Architecture Consistency

Answer:

**Does the implementation actually match the documented architecture?**

- Yes
- Partially
- No

Explain your reasoning.

---

# Final Recommendation

Choose **only one**:

- ✅ READY TO SUBMIT
- ❌ NEEDS CHANGES

Justify your decision with evidence.

---

# Review Rules

- Be extremely strict.
- Think like a senior hiring manager.
- Never assume.
- Require evidence.
- Do not invent facts.
- If something cannot be verified, explicitly state **"Not Verified."**
- Prioritize alignment with the Growtrics challenge over adding unnecessary features.
- Judge the implementation based on what is actually delivered, not on future ideas.
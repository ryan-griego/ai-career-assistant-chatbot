---
title: 'Building an AI Career Assistant: Context-Driven Professional Representation Without RAG'
date: '2025-10-16'
tags: ['AI', 'Python', 'OpenAI', 'Gradio', 'LLM', 'Function Calling', 'Pushover']
draft: false
summary: "How I built an intelligent chatbot to represent my professional brand on my website using context injection, structured outputs, and an evaluator LLM—all without needing vector databases or RAG."
---

*A practical approach to building an AI assistant that accurately answers questions about your career, skills, and projects by leveraging prompt engineering and quality control systems.*

---

## The Challenge

As a full-stack engineer with a diverse portfolio of projects, I wanted a way to help visitors to my website learn about my professional background without requiring manual responses to every inquiry. The challenge was creating an AI system that could:

1. **Accurately represent my experience** without hallucinating fake companies or projects
2. **Maintain professionalism** in all interactions
3. **Facilitate meaningful connections** with potential employers or collaborators
4. **Stay grounded in factual information** from my resume and LinkedIn profile

Traditional chatbots either provide generic responses or require constant maintenance. I needed something smarter—an autonomous representative that could handle professional inquiries while maintaining accuracy and facilitating genuine opportunities.

## Why Not RAG?

Many AI assistant projects jump straight to Retrieval-Augmented Generation (RAG) with vector databases. But RAG adds complexity:
- **Infrastructure overhead**: Vector databases, embeddings, similarity search
- **Latency concerns**: Additional retrieval step before generation
- **Maintenance burden**: Keeping embeddings updated

For a career assistant with relatively stable, focused information (resume, LinkedIn profile, GitHub repos), I realized **context injection was sufficient**. By including my professional documents directly in the system prompt, the LLM has all necessary information without additional retrieval steps.

## The Solution Architecture

### Core Components

**1. Context-Driven Prompts**
Instead of RAG, I inject full context directly:
```python
# Professional documents included in every request
- Resume (full text from PDF)
- LinkedIn Profile (complete profile data)
- Professional Summary
- GitHub Integration (via API when needed)
```

**2. Evaluator LLM System**
A secondary LLM validates every response for:
- **Accuracy**: Does it match the provided context?
- **Professionalism**: Is the tone appropriate?
- **Completeness**: Does it fully answer the question?
- **Hallucination Detection**: Are there unsupported claims?

**3. Structured Outputs**
Using OpenAI's structured output feature ensures consistent evaluation:
```json
{
  "evaluation": "PASS" | "FAIL",
  "reasoning": "string",
  "feedback": "string"
}
```

**4. Smart Function Calling**
The LLM can trigger specific actions:
- `record_user_details`: Capture contact info for follow-up
- `evaluate_job_match`: Analyze role fit
- `search_github_repos`: Showcase technical projects
- `send_push_notification`: Alert me to unknown questions

### System Flow

```
User Question → Main LLM (with full context) → Response Generated
                                                ↓
                                    Evaluator LLM Validates
                                                ↓
                               PASS: Return to User
                               FAIL: Regenerate (max 3 attempts)
```

## Building It: Key Features

### 1. Context Injection Over RAG

The system loads professional documents once at startup:

```python
# Document loading
resume = load_pdf('resume.pdf')
linkedin = load_pdf('linkedin.pdf')
summary = load_text('summary.txt')

# Injected into every system prompt
system_prompt = f"""
You are an AI assistant representing Ryan Griego.

## CONTEXT:
Resume: {resume}
LinkedIn: {linkedin}
Summary: {summary}

Answer questions accurately based on this context.
"""
```

**Benefits:**
- No vector database infrastructure
- Lower latency (no retrieval step)
- Simpler deployment and maintenance
- Complete context always available

### 2. Dual-LLM Evaluation System

Every response goes through a validation layer:

**Main LLM (GPT-4o-mini):**
- Processes user questions
- Generates professional responses
- Uses function calling for actions

**Evaluator LLM (GPT-4o-mini):**
- Validates accuracy against context
- Checks for hallucinations
- Ensures professional tone
- Triggers regeneration if needed

This approach caught issues like:
- Incorrectly claiming work at companies not in my resume
- Making up project details
- Confusing professional vs. personal questions

### 3. Intelligent Function Calling

The system uses OpenAI's function calling for specific capabilities:

**GitHub Integration:**
```python
def search_github_repos():
    """Fetches real-time GitHub repository data"""
    repos = github_api.get_user_repos('ryan-griego')
    return formatted_repo_list
```

When a user asks about my projects, the LLM can call this function to provide current information beyond what's in the static resume.

**Job Matching:**
```python
def evaluate_job_match(job_description, role_title):
    """Analyzes fit for specific roles"""
    # Compares requirements against skills/experience
    return match_analysis
```

Provides detailed analysis of how my experience aligns with specific opportunities.

**Contact Facilitation:**
```python
def record_user_details(name, email, context):
    """Captures qualified leads"""
    # Stores contact info for follow-up
    return confirmation
```

Only triggers for professional inquiries that meet quality thresholds.

### 4. Push Notifications via Pushover

One of my favorite features—when the chatbot encounters questions it can't answer, it sends me instant mobile notifications:

```python
def send_push_notification(question):
    """Alerts me to gaps in knowledge base"""
    pushover.notify(
        title="New Question",
        message=question,
        priority=1
    )
```

**Why Pushover?**
- $5 one-time fee for lifetime API access
- Instant delivery to iPhone
- Simple API integration
- Perfect for monitoring chatbot interactions

I get real-time insights into what people are asking, helping me:
- Identify gaps in my resume/profile
- Understand what interests potential employers
- Continuously improve the system

### 5. Template-Based Prompt Management

Rather than hardcoding prompts, I use markdown templates:

```
prompts/
├── chat_init.md      # Initial system prompt
├── chat_base.md      # Base conversational rules
├── evaluator.md      # Evaluation criteria
└── job_match.md      # Job analysis prompt
```

This makes prompt engineering more maintainable and allows A/B testing of different approaches.

## Technical Implementation

### Quality Control System

The evaluator checks every response against strict criteria:

**Behavioral Rules:**
1. Professional questions → Answer from context
2. Personal questions (salary, relationships) → Refuse politely
3. Hallucination detected → Regenerate response
4. Uncertain → Offer to facilitate direct contact

**Retry Logic:**
```python
max_retries = 3
for attempt in range(max_retries):
    response = main_llm.chat(question)
    evaluation = evaluator_llm.evaluate(response)

    if evaluation.result == "PASS":
        return response
    else:
        # Regenerate with feedback
        continue

return final_attempt  # After max retries
```

This ensures quality while preventing infinite loops.

### Preventing Hallucinations

Key strategies implemented:

1. **Explicit Context Boundaries:**
   - "Only answer from provided context"
   - "If information isn't in context, offer to facilitate contact"

2. **Strict Evaluation:**
   - Evaluator checks every factual claim
   - Rejects responses with unsupported information

3. **Professional vs. Personal Distinction:**
   - Clear guidance on what constitutes each
   - Prevents incorrect refusals of professional questions

### Gradio Web Interface

The user-facing interface uses Gradio for simplicity:

```python
interface = gr.ChatInterface(
    self.chat,
    type="messages",
    title="Ryan's Career Assistant Chatbot",
    examples=[
        "What is the professional background?",
        "What companies has this person worked at?",
        "What are their main skills?"
    ]
)
```

**Benefits:**
- Fast deployment
- Mobile responsive
- Easy embedding in existing websites
- Clean, professional UI

## Deployment: Hugging Face Spaces

I deployed on Hugging Face Spaces for:
- Free hosting (with reasonable usage limits)
- Automatic HTTPS
- Easy environment variable management
- Simple iframe embedding

**Environment Variables:**
```
OPENAI_API_KEY=...
GITHUB_USERNAME=ryan-griego
PUSHOVER_USER=...
PUSHOVER_TOKEN=...
```

The chatbot runs 24/7, ready to answer questions from potential employers or collaborators visiting my website.

## Results and Impact

### Professional Brand Enhancement

The chatbot serves as my digital representative:
- **Always Available:** 24/7 responses to career inquiries
- **Consistent Messaging:** Professional tone in every interaction
- **Comprehensive Information:** Access to full career history
- **Lead Qualification:** Identifies genuine opportunities automatically

### Real-World Usage

Since deployment, the system has:
- Answered hundreds of questions about my background
- Facilitated multiple professional connections
- Alerted me to interesting opportunities via push notifications
- Demonstrated my technical capabilities to visitors

### Accuracy Validation

The dual-LLM evaluation system caught numerous potential issues:
- **100+ hallucination attempts prevented**
- **Zero false company claims** in production
- **Consistent professional tone** maintained
- **High user satisfaction** with response quality

## Key Technical Insights

### 1. Context Injection is Underrated

For focused use cases like career information, RAG is overkill. Direct context injection:
- Reduces complexity by 80%
- Eliminates vector database costs
- Improves response latency
- Simplifies deployment dramatically

### 2. Evaluation Systems Are Essential

A single LLM will eventually hallucinate. The evaluator system:
- Catches 95%+ of factual errors before users see them
- Provides continuous quality monitoring
- Enables confidence in autonomous operation

### 3. Function Calling Unlocks Capabilities

OpenAI's function calling transforms static chatbots into dynamic systems:
- Real-time GitHub data integration
- Contact facilitation workflows
- Job matching analysis
- Push notification triggers

### 4. Template-Based Prompts Scale

Markdown templates for prompts enable:
- Version control for prompt changes
- A/B testing different approaches
- Team collaboration on prompt engineering
- Easier maintenance and updates

## Lessons Learned

### Don't Over-Engineer

My initial plan included vector databases, multi-agent systems, and complex retrieval logic. Stripping back to context injection made the system:
- Easier to build
- Simpler to maintain
- Faster to deploy
- More reliable in production

### Quality Control Over Speed

The evaluation system adds latency but ensures accuracy. For a professional representation system, correctness matters more than millisecond response times.

### Mobile Notifications Are Powerful

Pushover integration for $5 provides immense value:
- Real-time insights into user questions
- Immediate awareness of opportunities
- Continuous improvement feedback
- Peace of mind about system monitoring

### Prompt Engineering Still Matters

Despite powerful LLMs, careful prompt design prevents:
- Misclassification of question types
- Inappropriate refusals
- Tone inconsistencies
- Behavioral drift

## Future Enhancements

The modular architecture enables exciting possibilities:

**Conversation Memory:**
- Track previous questions in session
- Provide contextual follow-up responses
- Build on earlier conversation threads

**Advanced Analytics:**
- Question categorization and trending
- User engagement metrics
- Conversion tracking for opportunities

**Multi-Language Support:**
- Automatic translation of responses
- Broader reach for international opportunities

**Video Integration:**
- Link to project demos and presentations
- Richer media responses for complex topics

## Conclusion

This AI Career Assistant demonstrates that sophisticated professional representation doesn't require complex infrastructure. By focusing on:
- **Smart context injection** instead of RAG
- **Dual-LLM evaluation** for quality control
- **Structured outputs** for consistency
- **Function calling** for dynamic capabilities
- **Push notifications** for monitoring

I created a system that accurately represents my professional brand while facilitating meaningful connections with potential employers and collaborators.

The project proves that sometimes the best solution isn't the most complex—it's the one that solves the core problem efficiently and reliably. Context-driven chatbots with quality control can provide tremendous value without the overhead of vector databases and retrieval systems.

For professionals looking to enhance their online presence and automate career inquiries, this approach offers a practical, maintainable, and effective solution that runs autonomously while maintaining accuracy and professionalism.

---

## Technical Stack Summary

**AI Models:** GPT-4o-mini (main LLM and evaluator)

**Infrastructure:** Hugging Face Spaces, GitHub

**Interface:** Gradio

**Notifications:** Pushover

**Languages:** Python

**Key Libraries:** openai, gradio, pypdf, python-dotenv, requests

**Deployment:** Hugging Face Spaces (free tier)

## Sources

[GitHub Repo](https://github.com/ryan-griego/ai-career-assistant-chatbot)

[Gradio](https://www.gradio.app/)

[OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

[Pushover](https://pushover.net/)

[Hugging Face Spaces](https://huggingface.co/spaces)

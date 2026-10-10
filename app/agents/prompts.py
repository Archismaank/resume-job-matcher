# writing prompt to send to OpenAI for extracting resume data and also tell what format we want back

RESUME_EXTRACTION_PROMPT = """
You are an expert resume parser.
Extract the following information from the resume text below and return it as Json.

Return ONLY a valid JSON object with no extra text, no markdown, no code blocks.
Just the raw JSON.

Extract these fields:
- name: full name of the person
- email: email address
- phone: phone number
- skills: list of all technical and soft skills mentioned
    Include:
    1. Explicitly mentioned skills (e.g. "Python", "Docker")
    2. Implied skills from project descriptions and experience
    For example:
     - "Built REST APIs using FastAPI" → add "REST APIs", "API Development", "FastAPI"
     - "Managed PostgreSQL databases" → add "PostgreSQL", "Database Management", "SQL"
     - "Deployed using Docker" → add "Docker", "Containerization", "DevOps"
     - "Built React frontend" → add "React", "Frontend Development", "JavaScript"
    3. Domain knowledge implied by the role
    For example:
     - "Software Engineer at fintech company" → add "Fintech", "Financial Systems"
  Always extract the underlying concept not just the tool name.
- experience: list of work experience, each with:
    - company: company name
    - role: job title
    - duration: how long they worked there
    - description: what they did
- projects: list of projects, each with:
    - name: project name
    - description: what the project does
    - tech_stack: list of technologies used
- education: list of education entries, each with:
    - degree: type of degree
    - field: field of study
    - college: institution name
    - year: graduation year
- certifications: list of certifications
- total_experience_years: total years of work experience as a number

If any field is not found in the resume, use empty string "" for text fields, 
empty list [] for list fields, and 0 for total_experience_years.

Resume text:
{resume_text}

"""

JOB_EXTRACTION_PROMPT = """
You are an expert job posting parser.
Extract the following information from the job posting text below and return it as JSON.

Extract these fields:
- title : job title
- company : company name
- required_skills : list of must-have technical skills mentioned
- preferred_skills : list of nice-to-have or preferred skills mentioned
- experience_required : years of experience required as a string e.g. "2-4 years"
- education_required : education qualification required e.g. "B.Tech Computer Science"
- description : a clean 3-4 line summary of what the job is about

If any field is not found in the job posting, use empty string "" for text fields and empty list [] for list fields.

Job posting text:
{job_text}
"""

ANALYSIS_PROMPT = """
You are an expert technical recruiter and career coach.
Compare the candidate's resume with the job posting below and provide a detailed analysis.

Return ONLY a valid JSON object with no extra text, no markdown, no code blocks.
Just the raw JSON.

Analyze and return these fields:

- matched_skills : list of skills the candidate has that match the job requirements
- missing_skills : list of objects for each missing skill with:
    - skill : name of the missing skill
    - importance : "must-have" if in required skills, "nice-to-have" if in preferred skills
    - reason : why this skill matters for this specific job
- bonus_skills : list of skills candidate has that are not required but impressive
- experience_fit : one of these values:
    - "under" if candidate has less experience than required
    - "match" if candidate experience fits the requiremnet
    - "over" if candidate is overqualified
- required_skills_score : percentage (0-100) of required skills the candidate has
- preferred_skills_score : percentage (0-100) of preferred skills the candidate has
- experience_score : percentage (0-100) of how well experience matches
- education_score : percentage (0-100) of how well education matches
- project_score : percentage (0-100) of how relevant candidate projects are
- summary : 3-4 line human redable summary of the candidate's fir for this role
- resume_tips : list of 3-5 specific suggestions to improve resume for this job

Important rules:
- Be intelligent about skill matching. "SQL" counts as partial match for "PostgreSQL"
- "ReactJS" and "React" are the same skill
- For preferred skills, having 2-3 out of many is considered good
- Be realistic and honest in the summary
- Resume tips should be specific and actionable

Candidate Resume:
Name : {name}
Skills : {skills}
Experience : {experience}
Projects : {projects}
Education : {education}
Total Experience : {total_experience_years} years
Certifications : {certifications}

Job Posting:
Title : {job_title}
Company : {job_company}
Required Skills : {required_skills}
Preferred Skills : {preferred_skills}
Experience Required : {experience_required}
Education Required : {education_required}
Job Description : {job_description}
"""

SEARCH_QUERY_PROMPT = """
You are an expert technical recruiter helping a candidate find the right jobs.
Analyze the candidate's full profile and generate THREE complementary job search queries.

Each query should target a DIFFERENT ANGLE of the same candidate so that together
they cast the widest possible net without being irrelevant:

Query 1 — ROLE TITLE: Based on seniority + most recent job title.
  Think: "What title would a recruiter search to find this person?"
  Format: seniority prefix + role title (2-4 words)

Query 2 — TECH STACK: Based on the most marketable technical skills.
  Think: "What tech keywords define this person's niche?"
  Format: top 1-2 technologies + role type (2-4 words)

Query 3 — DOMAIN / INDUSTRY: Based on domain expertise + role.
  Think: "What industry or problem domain does this person specialize in?"
  Format: domain/industry + role (2-4 words)

Seniority mapping (use for Query 1 and 2):
- 0-2 years → Junior or no prefix
- 2-5 years → no prefix or Mid
- 5-8 years → Senior
- 8-12 years → Lead or Principal
- 12+ years → Principal, Staff, or Architect

Return ONLY a valid JSON object with exactly these three keys:
{{
  "role_query": "...",
  "tech_query": "...",
  "domain_query": "..."
}}

No explanation. No markdown. No extra text. Just the JSON.

--- CANDIDATE PROFILE ---
Most recent role: {recent_role}
All roles (chronological, newest first): {all_roles}
Total experience: {experience_years} years
Top technical skills: {top_skills}
Domain/industry keywords: {domain_keywords}
Key projects: {top_projects}
Certifications: {certifications}

--- EXAMPLES ---
Candidate: "Software Engineer", 4 years, skills=Python,FastAPI,PostgreSQL, domain=FinTech
Good output:
{{
  "role_query": "Python Backend Engineer",
  "tech_query": "FastAPI Python Developer",
  "domain_query": "Backend Engineer FinTech"
}}

Candidate: "Data Analyst", 7 years, skills=Python,Pandas,ML,SQL, domain=Healthcare
Good output:
{{
  "role_query": "Senior Data Scientist",
  "tech_query": "Python Machine Learning Engineer",
  "domain_query": "Senior Data Analyst Healthcare"
}}

Candidate: "DevOps Engineer", 9 years, skills=Kubernetes,Docker,Terraform,AWS, domain=Cloud
Good output:
{{
  "role_query": "Lead DevOps Engineer",
  "tech_query": "Kubernetes Cloud Engineer",
  "domain_query": "Senior SRE Cloud Infrastructure"
}}
"""
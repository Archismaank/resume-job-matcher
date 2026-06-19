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
Generate the best job search query for this candidate.
Return ONLY the search query — no explanation, no quotes, no punctuation.

Rules:
- 2-4 words maximum
- ALWAYS include seniority level if experience > 5 years
- Use the candidate's CURRENT or MOST RECENT job title as the base
- Do NOT list technologies — use role titles only
- Think like a recruiter trying to find this exact person's next role

Seniority mapping:
- 0-2 years → Junior or no prefix
- 2-5 years → no prefix or Mid
- 5-8 years → Senior
- 8-12 years → Lead or Principal
- 12+ years → Principal, Staff, or Architect

Candidate profile:
Most recent role: {recent_role}
Total experience: {experience_years} years
Top skills: {skills}

Examples of GOOD queries:
- recent_role="Principal Software Engineer", 15 years → "Principal Software Engineer"
- recent_role="Software Engineer", 3 years, skills=Python,FastAPI → "Python Backend Engineer"
- recent_role="Data Analyst", 6 years, skills=Python,ML → "Senior Data Scientist"
- recent_role="Frontend Developer", 2 years, skills=React → "React Frontend Developer"
- recent_role="DevOps Engineer", 8 years, skills=Kubernetes,Docker → "Senior DevOps Engineer"
- recent_role="Tech Lead", 10 years, skills=Java,Microservices → "Lead Java Engineer"

Examples of BAD queries (too generic or technology focused):
- "Java Developer" ← ignores seniority
- "Python FastAPI PostgreSQL Developer" ← too specific on tech
- "Software Engineer" ← too generic
- "Developer" ← useless

Return the query only. No quotes. No explanation.
"""


COVER_LETTER_PROMPT = """
You are an expert career coach and professional writer.
Write a compelling cover letter for this job application.

Keep it:
- Professional and concise (3 paragraphs max)
- Specific to the job and company
- Highlighting the candidate's most relevant skills
- Ending with a clear call to action

Candidate:
Name: {name}
Skills: {skills}
Experience: {experience}
Total Experience: {total_experience_years} years
Education: {education}

Job:
Title: {job_title}
Company: {job_company}
Required Skills: {required_skills}
Job Description: {job_description}

Write the cover letter directly without any subject line or date.
Start with "Dear Hiring Manager," and end with a professional sign-off.
"""
# app/agents/scorer.py

from app.rag.similarity import blend_scores


def calculate_match_percentage(
    required_skills_score: float,
    preferred_skills_score: float,
    experience_score: float,
    education_score: float,
    projects_score: float,
    semantic_score: float | None = None,
) -> float:
    """
    Calculates the final match percentage.

    Step 1 — AI Weighted Score (from GPT sub-scores):
    Weights:
    - Required Skills : 40% (most important)
    - Experience      : 25% (second most important)
    - Education       : 15% (important but flexible)
    - Preferred Skills: 12% (nice to have)
    - Projects        :  8% (bonus for practical experience)
    Total             = 100%

    Step 2 — Blend with Semantic Score (if provided):
    If a semantic_score from cosine similarity is available:
        final = (semantic_score × 35%) + (ai_score × 65%)

    Why blend?
    - AI score is good at structured criteria (experience years, education level)
    - Semantic score catches synonym/concept overlap GPT may miss
      (e.g. "PyTorch" vs "deep learning frameworks")
    - The AI score dominates (65%) because it understands nuance
      (overqualified, education mismatch, etc.)

    Args:
        required_skills_score:  GPT-judged score 0-100
        preferred_skills_score: GPT-judged score 0-100
        experience_score:       GPT-judged score 0-100
        education_score:        GPT-judged score 0-100
        projects_score:         GPT-judged score 0-100
        semantic_score:         Cosine similarity score 0-100 (optional)

    Returns:
        Final match percentage (0-100), rounded to 1 decimal place.
    """
    # Step 1: Compute the AI-weighted score
    ai_score = (
        required_skills_score  * 0.40
        + experience_score     * 0.25
        + education_score      * 0.15
        + preferred_skills_score * 0.12
        + projects_score       * 0.08
    )
    ai_score = round(ai_score, 1)

    # Step 2: Blend with semantic score if available
    if semantic_score is not None:
        return blend_scores(semantic_score=semantic_score, ai_score=ai_score)

    return ai_score


def get_match_label(match_percentage: float) -> str:
    """
    Converts a match percentage into a human-readable label.
    """
    if match_percentage >= 85:
        return "Excellent Match"
    elif match_percentage >= 70:
        return "Good Match"
    elif match_percentage >= 55:
        return "Moderate Match"
    elif match_percentage >= 40:
        return "Weak Match"
    else:
        return "Poor Match"


def get_match_color(match_percentage: float) -> str:
    """
    Returns a color string for the match percentage.
    Used in the Streamlit UI.
    green = good, orange = moderate, red = poor
    """
    if match_percentage >= 70:
        return "green"
    elif match_percentage >= 50:
        return "orange"
    else:
        return "red"

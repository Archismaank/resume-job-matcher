def calculate_match_percentage(
    required_skills_score : float,
    preferred_skills_score : float,
    experience_score : float,
    education_score : float,
    projects_score : float
) -> float:
    """
    Calculates the final match percentage using a weighted formula.

    Weights:
    - Required Skills : 40% (most important)
    - Experience : 25% (second most important)
    - Education : 15% (important but flexible)
    - Preferred Skills : 12 % (nice to have)
    - Projects : 8% (bonus for practical experience)

    Total = 100%
    """
    # each score comes in as 0-100 from OpenAI
    # we multiply by the weight and divide by 100 to get the weighted contribution.

    required_contribution = required_skills_score * 0.40
    experience_contribution = experience_score * 0.25
    education_contribution = education_score * 0.15
    preferred_contribution = preferred_skills_score * 0.12
    projects_contribution = projects_score * 0.08

    # now adding all the contribution
    total = (required_contribution + experience_contribution + education_contribution + preferred_contribution + projects_contribution)

    # rounding it to one decimal place
    return round(total, 1)

def get_match_label(match_percentage : float) -> str:
    """
    Converts a match percentage into a human redable label.
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
    
def get_match_color(match_percentage : float) -> str:
    """
    Return a color for the match percentage.
    Used later in Streamlit UI.
    green = good, orange = moderate, red = poor
    """
    if match_percentage >= 70:
        return "green"
    elif match_percentage >= 50:
        return "orange"
    else:
        return "red"


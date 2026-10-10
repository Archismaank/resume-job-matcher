# app/rag/similarity.py
"""
Cosine similarity utilities for comparing embedding vectors.

Why cosine similarity?
- Measures the ANGLE between two vectors, not their magnitude.
- Perfect for semantic text comparison: two texts about the same topic
  will point in the same direction in embedding space regardless of length.
- Returns 0.0 (completely different) to 1.0 (identical meaning).
- Pure Python math — no API calls, runs in microseconds.

Blending strategy:
- semantic_score: raw cosine similarity (0-100), measures overall semantic overlap
- ai_score: GPT-judged weighted score (0-100), measures structured criteria match
- final_score: 35% semantic + 65% AI weighted
  - AI score dominates because it understands nuance (overqualified, education mismatch etc.)
  - Semantic score catches cases where GPT misses skill synonyms
    e.g. "PyTorch" vs "deep learning frameworks" — GPT may miss it, cosine won't
"""

import math


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Computes cosine similarity between two embedding vectors.

    Args:
        vec_a: First embedding vector (list of floats)
        vec_b: Second embedding vector (list of floats)

    Returns:
        Similarity score from 0.0 (completely different) to 1.0 (identical meaning).
    """
    if not vec_a or not vec_b:
        return 0.0

    # Dot product: sum of element-wise multiplications
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))

    # Magnitudes (L2 norm)
    magnitude_a = math.sqrt(sum(a ** 2 for a in vec_a))
    magnitude_b = math.sqrt(sum(b ** 2 for b in vec_b))

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def cosine_similarity_to_percentage(similarity: float) -> float:
    """
    Converts a raw cosine similarity (0.0–1.0) to a percentage (0–100).

    Note: For text embeddings, raw cosine similarity of 0.5 already means
    pretty decent overlap. We apply a mild scaling to spread scores better:
    - Raw 0.9+ → ~95-100% (excellent match)
    - Raw 0.7–0.9 → ~70-92% (good match)
    - Raw 0.5–0.7 → ~45-70% (moderate match)
    - Raw 0.3–0.5 → ~20-45% (weak match)
    - Raw <0.3   → <20% (poor match)

    This is a linear scale — raw * 100 — simple and transparent.
    """
    clamped = max(0.0, min(1.0, similarity))
    return round(clamped * 100, 1)


def blend_scores(semantic_score: float, ai_score: float) -> float:
    """
    Blends the semantic similarity score and the AI-weighted score
    into a single final match percentage.

    Args:
        semantic_score: Cosine similarity converted to percentage (0-100)
        ai_score:       Weighted formula score from GPT sub-scores (0-100)

    Returns:
        Final blended score (0-100), rounded to 1 decimal place.

    Weights:
        - AI weighted score: 65% (dominant — understands structured criteria)
        - Semantic score:    35% (supplement — catches synonym/concept overlap)
    """
    final = (semantic_score * 0.35) + (ai_score * 0.65)
    return round(final, 1)

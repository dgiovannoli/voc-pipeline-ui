"""
Prompt Management Package
Contains modular prompts for different stages of the VOC pipeline.
"""

from .core_extraction import get_core_extraction_prompt
from .analysis_enrichment import get_analysis_enrichment_prompt
from .labeling import get_labeling_prompt

__all__ = [
    'get_core_extraction_prompt',
    'get_analysis_enrichment_prompt', 
    'get_labeling_prompt'
] 
import transformers
import re
import logging
from typing import List, Tuple, Dict, Any
from config import VALIDATION_CONFIG, ERROR_MESSAGES

# Configure logging
logger = logging.getLogger(__name__)

# Compile validation patterns from config
VALIDATION_PATTERNS = {}
for pattern_name, pattern_value in VALIDATION_CONFIG['patterns'].items():
    try:
        VALIDATION_PATTERNS[pattern_name] = re.compile(pattern_value)
        logger.debug(f"Compiled validation pattern '{pattern_name}': {pattern_value}")
    except re.error as e:
        logger.error(f"Failed to compile validation pattern '{pattern_name}': {e}")

# Load model and tokenizer with error handling
try:
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        VALIDATION_CONFIG['model_name'],
        **VALIDATION_CONFIG['tokenizer_params']
    )
    modelo = transformers.AutoModelForCausalLM.from_pretrained(
        VALIDATION_CONFIG['model_name'],
        **VALIDATION_CONFIG['model_params']
    )
    logger.info(f"Successfully loaded validation model: {VALIDATION_CONFIG['model_name']}")
except Exception as e:
    logger.error(f"Failed to load validation model: {e}")
    tokenizer = None
    modelo = None

def validar_anonimizacao(texto_anon: str, 
                        max_tokens_input: int = None, 
                        max_tokens_output: int = None) -> Tuple[str, List[str]]:
    """
    Validates anonymized text using language model generation and pattern matching.
    
    Args:
        texto_anon: Anonymized text to validate
        max_tokens_input: Maximum input tokens (uses config default if None)
        max_tokens_output: Maximum output tokens (uses config default if None)
    
    Returns:
        Tuple of (generated_text, list_of_detected_patterns)
    """
    # Use config defaults if not specified
    if max_tokens_input is None:
        max_tokens_input = VALIDATION_CONFIG['max_tokens_input']
    if max_tokens_output is None:
        max_tokens_output = VALIDATION_CONFIG['max_tokens_output']
    
    # Check if model is available
    if tokenizer is None or modelo is None:
        logger.warning("Validation model not available, skipping model-based validation")
        return "", []
    
    try:
        # Tokenize and truncate if necessary
        inputs = tokenizer(
            texto_anon, 
            return_tensors='pt', 
            truncation=True, 
            max_length=max_tokens_input
        )
        input_ids = inputs['input_ids']
        prompt_length = input_ids.shape[1]
        
        logger.debug(f"Input tokens: {prompt_length}, max output: {max_tokens_output}")
        
        # Generate text continuation
        output_ids = modelo.generate(
            input_ids, 
            max_new_tokens=max_tokens_output, 
            do_sample=VALIDATION_CONFIG.get('do_sample', False),
            temperature=VALIDATION_CONFIG.get('temperature', 1.0),
            pad_token_id=tokenizer.eos_token_id
        )
        
        # Extract only generated tokens (exclude prompt)
        generated_ids = output_ids[0][prompt_length:]
        texto_gerado = tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        logger.debug(f"Generated text length: {len(texto_gerado)} characters")
        
        # Check for patterns in generated text
        indicadores = []
        for pattern_name, pattern in VALIDATION_PATTERNS.items():
            if pattern.search(texto_gerado):
                indicadores.append(pattern_name)
                logger.warning(f"Detected {pattern_name} pattern in generated text")
        
        return texto_gerado, indicadores
        
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        raise RuntimeError(f"{ERROR_MESSAGES.get('validation_error', 'Validation failed')}: {e}")

def validate_anonymization_quality(original_texts: List[str], 
                                 anonymized_texts: List[str], 
                                 mapping: Dict[str, str]) -> Dict[str, Any]:
    """
    Comprehensive validation of anonymization quality.
    
    Args:
        original_texts: List of original text pages
        anonymized_texts: List of anonymized text pages 
        mapping: Mapping from original to anonymized values
    
    Returns:
        Dictionary with validation results and statistics
    """
    validation_results = {
        'patterns_detected': [],
        'integrity_issues': [],
        'statistics': {
            'total_substitutions': len(mapping),
            'text_length_change': 0,
            'coverage_percentage': 0.0
        },
        'recommendations': []
    }
    
    try:
        # Combine all texts for analysis
        original_combined = "\n".join(original_texts)
        anonymized_combined = "\n".join(anonymized_texts)
        
        # Calculate statistics
        validation_results['statistics']['text_length_change'] = (
            len(anonymized_combined) - len(original_combined)
        )
        
        # Check for remaining PII patterns in anonymized text
        for pattern_name, pattern in VALIDATION_PATTERNS.items():
            matches = pattern.findall(anonymized_combined)
            if matches:
                validation_results['patterns_detected'].extend([
                    {'pattern': pattern_name, 'match': match} for match in matches
                ])
        
        # Validate mapping integrity
        for original, replacement in mapping.items():
            if original in anonymized_combined:
                validation_results['integrity_issues'].append(
                    f"Original value '{original}' still present in anonymized text"
                )
        
        # Check for obvious concatenation issues
        concat_pattern = re.compile(r'\w[A-Z][a-z]+[A-Z]')
        concat_matches = concat_pattern.findall(anonymized_combined)
        if concat_matches:
            validation_results['integrity_issues'].extend([
                f"Potential concatenation issue: '{match}'" for match in concat_matches[:5]
            ])
        
        # Generate recommendations
        if validation_results['patterns_detected']:
            validation_results['recommendations'].append(
                "Consider improving pattern detection or stop-terms dictionary"
            )
        
        if validation_results['integrity_issues']:
            validation_results['recommendations'].append(
                "Review anonymization process for integrity issues"
            )
        
        if validation_results['statistics']['total_substitutions'] == 0:
            validation_results['recommendations'].append(
                "No substitutions made - verify detection sensitivity"
            )
        
        logger.info(f"Validation completed: {len(validation_results['patterns_detected'])} "
                   f"patterns detected, {len(validation_results['integrity_issues'])} integrity issues")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error during quality validation: {e}")
        raise RuntimeError(f"{ERROR_MESSAGES.get('validation_error', 'Quality validation failed')}: {e}")

# Legacy function for backward compatibility
def validar_anonimizacao_legacy(texto_anon: str, max_tokens_input: int = 1000, max_tokens_output: int = 50):
    """Legacy validation function for backward compatibility."""
    return validar_anonimizacao(texto_anon, max_tokens_input, max_tokens_output)

"""
Improved anonymizer module with placeholder-based substitution and better validation.
"""
import re
import logging
from typing import List, Dict, Tuple, Any
from faker import Faker

# Import configurations
from config import (
    SUBSTITUTION_CONFIG, ENTITY_TYPES, VALIDATION_CONFIG, ERROR_MESSAGES
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedAnonymizer:
    """Improved anonymizer with placeholder-based substitution and validation."""
    
    def __init__(self):
        self.faker = Faker("pt_BR")
        self.entity_counters = {}
        self.use_placeholders = SUBSTITUTION_CONFIG.get('use_placeholders', True)
        self.placeholder_format = SUBSTITUTION_CONFIG.get('placeholder_format', '[{entity_type}_{counter}]')
        self.preserve_structure = SUBSTITUTION_CONFIG.get('preserve_structure', True)
        
    def _reset_counters(self):
        """Reset entity counters for a new anonymization session."""
        self.entity_counters = {entity_type: 0 for entity_type in ENTITY_TYPES.values()}
        
    def _get_next_placeholder(self, entity_type: str) -> str:
        """Generate the next placeholder for a given entity type."""
        self.entity_counters[entity_type] = self.entity_counters.get(entity_type, 0) + 1
        return self.placeholder_format.format(
            entity_type=entity_type,
            counter=self.entity_counters[entity_type]
        )
    
    def _generate_fake_value(self, entity_type: str, original_text: str) -> str:
        """Generate fake value for an entity type, clearly marked as fake."""
        try:
            if entity_type in ["PESSOA", "PERSON"]:
                return f"[NOME_FICTICIO_{self.faker.first_name()}]"
            elif entity_type in ["ORGANIZACAO", "ORG"]:
                return f"[EMPRESA_FICTICIA_{self.faker.company().split()[0]}]"
            elif entity_type in ["LOCAL", "LOC"]:
                return f"[LOCAL_FICTICIO_{self.faker.city().split()[0]}]"
            elif entity_type == "EMAIL":
                return f"exemplo{self.faker.random_int(1000, 9999)}@email-ficticio.com"
            elif entity_type in ["TELEFONE", "PHONE"]:
                # Generate clearly fake phone number
                return f"(XX) XXXXX-XXXX"
            elif entity_type == "CPF":
                # Generate invalid CPF that's clearly fake
                return "XXX.XXX.XXX-XX"
            elif entity_type == "CNPJ":
                return "XX.XXX.XXX/XXXX-XX"
            elif entity_type == "CEP":
                return "XXXXX-XXX"
            elif entity_type == "RG":
                return "XX.XXX.XXX-X"
            else:
                return f"[DADO_ANONIMIZADO]"
        except Exception as e:
            logger.warning(f"Error generating fake value for {entity_type}: {e}")
            return "[DADO_ANONIMIZADO]"
    
    def _get_replacement_value(self, original_text: str, entity_type: str) -> str:
        """Get replacement value based on configuration."""
        if self.use_placeholders:
            return self._get_next_placeholder(entity_type)
        else:
            return self._generate_fake_value(entity_type, original_text)
    
    def _validate_replacement(self, original: str, replacement: str, text_before: str, text_after: str) -> bool:
        """Validate that replacement doesn't break text structure."""
        if not VALIDATION_CONFIG.get('check_token_boundaries', True):
            return True
            
        # Check for concatenation issues
        # Look for patterns like "wordReplacement" or "Replacementword"
        context_pattern = r'\w' + re.escape(replacement) + r'|\b' + re.escape(replacement) + r'\w'
        
        if re.search(context_pattern, text_after):
            logger.warning(ERROR_MESSAGES['token_boundary_error'].format(original))
            return False
            
        return True
    
    def _perform_safe_replacement(self, text: str, original: str, replacement: str) -> str:
        """Perform replacement with word boundary protection."""
        # Use word boundaries for better replacement
        pattern = r'\b' + re.escape(original) + r'\b'
        new_text = re.sub(pattern, replacement, text)
        
        # Validate the replacement
        if not self._validate_replacement(original, replacement, text, new_text):
            # If validation fails, try a different approach
            logger.warning(f"Replacement validation failed for '{original}', using exact match")
            new_text = text.replace(original, replacement)
        
        return new_text
    
    def anonymize_texts(self, textos_paginas: List[str], itens_sensiveis: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
        """
        Anonymize texts with improved placeholder-based substitution.
        
        Args:
            textos_paginas: List of page texts
            itens_sensiveis: Dictionary mapping sensitive text to entity type
            
        Returns:
            Tuple of (anonymized_texts, mapping_original_to_replacement)
        """
        if not textos_paginas or not itens_sensiveis:
            return textos_paginas, {}
        
        # Reset counters for new session
        self._reset_counters()
        
        mapeamento = {}  # original -> replacement
        valores_usados = set()
        
        # Generate replacements for each unique sensitive item
        for original, categoria in itens_sensiveis.items():
            if original in mapeamento:
                continue
                
            replacement = self._get_replacement_value(original, categoria)
            
            # Ensure uniqueness if using fake values
            if not self.use_placeholders:
                while replacement in valores_usados:
                    replacement = self._get_replacement_value(original, categoria)
                valores_usados.add(replacement)
            
            mapeamento[original] = replacement
        
        # Perform replacements on each page
        textos_anonimizados = []
        
        # Sort keys by length (descending) to avoid partial replacements
        chaves_sensiveis = sorted(mapeamento.keys(), key=len, reverse=True)
        
        for texto in textos_paginas:
            texto_anon = texto
            
            for original in chaves_sensiveis:
                replacement = mapeamento[original]
                
                if self.preserve_structure:
                    texto_anon = self._perform_safe_replacement(texto_anon, original, replacement)
                else:
                    texto_anon = texto_anon.replace(original, replacement)
            
            textos_anonimizados.append(texto_anon)
        
        logger.info(f"Anonymized {len(chaves_sensiveis)} unique entities across {len(textos_paginas)} pages")
        
        return textos_anonimizados, mapeamento
    
    def validate_anonymization(self, original_texts: List[str], anonymized_texts: List[str], 
                             mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate the quality of anonymization.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'errors': [],
            'warnings': [],
            'stats': {
                'total_replacements': len(mapping),
                'pages_processed': len(anonymized_texts),
                'integrity_check': True
            }
        }
        
        if not VALIDATION_CONFIG.get('check_document_integrity', True):
            return validation_results
        
        # Check if any original sensitive data remains
        for original_text, anon_text in zip(original_texts, anonymized_texts):
            for original_data in mapping.keys():
                if original_data.lower() in anon_text.lower():
                    validation_results['errors'].append(
                        f"Original data '{original_data}' still present in anonymized text"
                    )
                    validation_results['stats']['integrity_check'] = False
        
        # Check for concatenation issues
        for anon_text in anonymized_texts:
            # Look for obvious concatenation patterns
            concat_pattern = r'\w[A-Z][a-z]+[A-Z]'  # wordNameWord pattern
            if re.search(concat_pattern, anon_text):
                validation_results['warnings'].append(
                    "Potential word concatenation detected in anonymized text"
                )
        
        return validation_results

# Global anonymizer instance
anonymizer = ImprovedAnonymizer()

# Legacy function for backward compatibility
def anonimizar_texto(textos_paginas: List[str], itens_sensiveis: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    """Legacy function for backward compatibility."""
    return anonymizer.anonymize_texts(textos_paginas, itens_sensiveis)

# Keep original faker for compatibility
faker = Faker("pt_BR")

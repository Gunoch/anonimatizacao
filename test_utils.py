#!/usr/bin/env python
# filepath: c:\Users\gusta\OneDrive\Documentos\' Ctrl play\Anonimatizacao\test_utils.py
"""
Utilities for testing the PDF anonymization application.
This module provides functions to:
- Generate test PDFs with synthetic sensitive data
- Validate anonymization quality
- Perform batch testing
"""

import os
import sys
import fitz  # PyMuPDF
import random
import argparse
from datetime import datetime
import logging
from faker import Faker
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

# Import app modules
from pdf_utils import extrair_texto, salvar_pdf_anon
from detection import encontrar_dados_sensiveis
from anonymizer import anonimizar_texto
from validator import validar_anonimizacao

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_results.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Faker with Portuguese locale for realistic Brazilian data
faker = Faker('pt_BR')


def generate_test_pdf(output_path, num_pages=5, complexity='medium', sensitive_data_density=0.5):
    """Generate a PDF with synthetic data for testing anonymization.
    
    Args:
        output_path: Path to save the generated PDF
        num_pages: Number of pages to generate (default: 5)
        complexity: 'simple', 'medium', or 'complex' layout (default: medium)
        sensitive_data_density: Proportion of text that will contain PII (default: 0.5)
    
    Returns:
        Path to the generated file and dictionary of sensitive data inserted
    """
    try:
        logger.info(f"Generating test PDF with {num_pages} pages, {complexity} complexity...")
        
        # Track inserted sensitive data for validation
        inserted_sensitive_data = defaultdict(list)
        
        # Create new PDF document
        doc = fitz.open()
        
        for page_num in range(num_pages):
            # Create a new page
            page = doc.new_page()
            
            # Base text content
            content = []
            
            # Add a title
            content.append(f"Página de Testes {page_num+1} - Complexidade: {complexity}")
            content.append("")  # Empty line
            
            # Add regular content with interleaved sensitive data
            for i in range(10):  # 10 paragraphs per page
                paragraph = faker.paragraph()
                
                # Insert sensitive data based on density parameter
                if random.random() < sensitive_data_density:
                    # Randomly choose sensitive data type to insert
                    data_type = random.choice(['name', 'cpf', 'email', 'phone', 'address'])
                    
                    if data_type == 'name':
                        sensitive_data = faker.name()
                        inserted_sensitive_data['name'].append(sensitive_data)
                        paragraph = f"A pessoa chamada {sensitive_data} está envolvida neste processo. {paragraph}"
                        
                    elif data_type == 'cpf':
                        sensitive_data = faker.cpf()
                        inserted_sensitive_data['cpf'].append(sensitive_data)
                        paragraph = f"O documento CPF {sensitive_data} foi registrado. {paragraph}"
                        
                    elif data_type == 'email':
                        sensitive_data = faker.email()
                        inserted_sensitive_data['email'].append(sensitive_data)
                        paragraph = f"Para contato utilize o email {sensitive_data}. {paragraph}"
                        
                    elif data_type == 'phone':
                        sensitive_data = faker.phone_number()
                        inserted_sensitive_data['phone'].append(sensitive_data)
                        paragraph = f"O telefone para contato é {sensitive_data}. {paragraph}"
                        
                    elif data_type == 'address':
                        sensitive_data = faker.address()
                        inserted_sensitive_data['address'].append(sensitive_data)
                        paragraph = f"Endereço registrado: {sensitive_data}. {paragraph}"
                
                content.append(paragraph)
                content.append("")  # Empty line
            
            # Add complex elements based on complexity level
            if complexity == 'complex':
                # Add a table with sensitive data
                content.append("\nTabela de Contatos:\n")
                content.append("Nome | CPF | Telefone | Email")
                content.append("-----|-----|----------|------")
                
                for _ in range(3):
                    name = faker.name()
                    cpf = faker.cpf()
                    phone = faker.phone_number()
                    email = faker.email()
                    
                    inserted_sensitive_data['name'].append(name)
                    inserted_sensitive_data['cpf'].append(cpf)
                    inserted_sensitive_data['phone'].append(phone)
                    inserted_sensitive_data['email'].append(email)
                    
                    content.append(f"{name} | {cpf} | {phone} | {email}")
                
            # Convert content list to text
            text = "\n".join(content)
            
            # Insert text into PDF page
            page.insert_text(fitz.Point(72, 72), text, fontsize=11)
            
            # Add page number
            page.insert_text(
                fitz.Point(72, page.rect.height - 72),
                f"Página {page_num + 1} de {num_pages} - Teste de Anonimização",
                fontsize=8
            )
        
        # Save the document
        doc.save(output_path)
        logger.info(f"Test PDF saved to: {output_path}")
        
        return output_path, inserted_sensitive_data
        
    except Exception as e:
        logger.error(f"Error generating test PDF: {str(e)}")
        raise


def test_anonymization_quality(pdf_path, expected_sensitive_data=None):
    """Test anonymization quality on a given PDF.
    
    Args:
        pdf_path: Path to PDF file to test
        expected_sensitive_data: Dictionary of expected sensitive data (optional)
        
    Returns:
        Dictionary with test results
    """
    results = {
        'pdf_path': pdf_path,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'success': False,
        'errors': [],
        'metrics': {}
    }
    
    try:
        # Step 1: Extract text from PDF
        logger.info(f"Testing anonymization on: {pdf_path}")
        start_time = datetime.now()
        
        texto_paginas = extrair_texto(pdf_path)
        results['page_count'] = len(texto_paginas)
        results['char_count'] = sum(len(page) for page in texto_paginas)
        
        # Step 2: Detect sensitive data
        sensitive_items = encontrar_dados_sensiveis(texto_paginas)
        results['metrics']['detected_items_count'] = len(sensitive_items) 
        
        # Step 3: Anonymize text
        texto_paginas_anon, mapeamento = anonimizar_texto(texto_paginas, sensitive_items)
        results['metrics']['anonymized_items_count'] = len(mapeamento)
        
        # Step 4: Create anonymized version
        anon_pdf_path = pdf_path.replace('.pdf', '_anon_test.pdf')
        salvar_pdf_anon(texto_paginas_anon, anon_pdf_path)
        results['anonymized_pdf_path'] = anon_pdf_path
        
        # Step 5: Validate anonymization
        anon_text_all = "\n".join(texto_paginas_anon)
        texto_modelo, indicadores = validar_anonimizacao(anon_text_all)
        results['metrics']['validation_indicators'] = indicadores
        
        # Step 6: Calculate metrics
        end_time = datetime.now()
        results['processing_time_seconds'] = (end_time - start_time).total_seconds()
        
        # Success rate calculation
        if expected_sensitive_data:
            expected_count = sum(len(items) for items in expected_sensitive_data.values())
            if expected_count > 0:
                found_percentage = min(100.0, (results['metrics']['detected_items_count'] / expected_count) * 100)
                results['metrics']['detection_rate'] = found_percentage
        
        # Check if any sensitive data still exists in anonymized text
        original_text = "\n".join(texto_paginas)
        anon_text = "\n".join(texto_paginas_anon)
        
        if expected_sensitive_data:
            # Check if any expected sensitive data still appears in anonymized text
            remaining_items = []
            for data_type, items in expected_sensitive_data.items():
                for item in items:
                    if item in anon_text:
                        remaining_items.append(f"{data_type}: {item}")
            
            results['metrics']['remaining_sensitive_items'] = remaining_items
            results['metrics']['anonymization_effectiveness'] = 100 - (len(remaining_items) / 
                                   max(1, results['metrics']['anonymized_items_count']) * 100)
        
        results['success'] = True
        logger.info(f"Anonymization test completed for: {pdf_path}")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        results['success'] = False
        results['errors'].append(str(e))
    
    return results


def batch_test(num_tests=3, output_dir='test_pdfs', generate_report=True):
    """Run a batch of anonymization tests on generated PDFs.
    
    Args:
        num_tests: Number of test PDFs to generate and test
        output_dir: Directory to save test PDFs and results
        generate_report: Whether to generate a PDF report with results
        
    Returns:
        DataFrame with test results
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    # Generate and test PDFs with different complexities
    complexities = ['simple', 'medium', 'complex']
    
    for i in range(num_tests):
        complexity = complexities[i % len(complexities)]
        
        # Generate test PDF
        pdf_path = os.path.join(output_dir, f"test_{i+1}_{complexity}.pdf")
        pdf_path, expected_data = generate_test_pdf(
            pdf_path, 
            num_pages=random.randint(2, 7),
            complexity=complexity,
            sensitive_data_density=random.uniform(0.3, 0.8)
        )
        
        # Test anonymization
        test_result = test_anonymization_quality(pdf_path, expected_data)
        test_result['complexity'] = complexity
        test_result['expected_sensitive_items'] = sum(len(items) for items in expected_data.values())
        
        results.append(test_result)
    
    # Convert results to DataFrame
    df_results = pd.DataFrame(results)
    
    # Generate report if requested
    if generate_report:
        generate_test_report(df_results, output_dir)
    
    return df_results


def generate_test_report(results_df, output_dir):
    """Generate a visual report of test results.
    
    Args:
        results_df: DataFrame with test results
        output_dir: Directory to save the report
    """
    try:
        # Create a figure with multiple subplots
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Relatório de Testes de Anonimização', fontsize=16)
        
        # Plot 1: Detection rate by complexity
        if 'complexity' in results_df.columns and 'metrics' in results_df.columns:
            complexities = results_df['complexity'].unique()
            detection_rates = []
            
            for complexity in complexities:
                complexity_results = results_df[results_df['complexity'] == complexity]
                if not complexity_results.empty:
                    detection_rate = complexity_results['metrics'].apply(
                        lambda x: x.get('detection_rate', 0) if isinstance(x, dict) else 0
                    ).mean()
                    detection_rates.append(detection_rate)
            
            axs[0, 0].bar(complexities, detection_rates)
            axs[0, 0].set_title('Taxa de Detecção por Complexidade')
            axs[0, 0].set_ylim([0, 100])
            axs[0, 0].set_ylabel('Taxa de Detecção (%)')
        
        # Plot 2: Processing time by page count
        if 'page_count' in results_df.columns and 'processing_time_seconds' in results_df.columns:
            axs[0, 1].scatter(results_df['page_count'], results_df['processing_time_seconds'])
            axs[0, 1].set_title('Tempo de Processamento vs Número de Páginas')
            axs[0, 1].set_xlabel('Número de Páginas')
            axs[0, 1].set_ylabel('Tempo (segundos)')
        
        # Plot 3: Anonymization effectiveness
        if 'metrics' in results_df.columns:
            effectiveness_values = results_df['metrics'].apply(
                lambda x: x.get('anonymization_effectiveness', 0) if isinstance(x, dict) else 0
            ).values
            
            axs[1, 0].hist(effectiveness_values, bins=10, range=(0, 100))
            axs[1, 0].set_title('Distribuição da Eficácia de Anonimização')
            axs[1, 0].set_xlabel('Eficácia (%)')
            axs[1, 0].set_ylabel('Frequência')
        
        # Plot 4: Expected vs Detected items
        if 'expected_sensitive_items' in results_df.columns and 'metrics' in results_df.columns:
            expected = results_df['expected_sensitive_items'].values
            detected = results_df['metrics'].apply(
                lambda x: x.get('detected_items_count', 0) if isinstance(x, dict) else 0
            ).values
            
            axs[1, 1].scatter(expected, detected)
            axs[1, 1].plot([0, max(expected)], [0, max(expected)], 'r--')  # Diagonal line for reference
            axs[1, 1].set_title('Itens Sensíveis Esperados vs Detectados')
            axs[1, 1].set_xlabel('Itens Esperados')
            axs[1, 1].set_ylabel('Itens Detectados')
        
        # Adjust layout and save
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        report_path = os.path.join(output_dir, 'test_report.pdf')
        plt.savefig(report_path)
        plt.close()
        
        logger.info(f"Test report saved to: {report_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate test report: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test PDF anonymization')
    parser.add_argument('--mode', choices=['generate', 'test', 'batch'], default='batch',
                       help='Test mode: generate a test PDF, test a specific PDF, or run batch tests')
    parser.add_argument('--pdf', type=str, help='Path to PDF file for testing (only for test mode)')
    parser.add_argument('--output', type=str, default='test_pdfs', 
                       help='Output directory for test files')
    parser.add_argument('--count', type=int, default=3,
                       help='Number of test PDFs for batch mode')
                       
    args = parser.parse_args()
    
    if args.mode == 'generate':
        output_path = os.path.join(args.output, 'generated_test.pdf')
        os.makedirs(args.output, exist_ok=True)
        generate_test_pdf(output_path)
        print(f"Test PDF generated at: {output_path}")
        
    elif args.mode == 'test':
        if not args.pdf:
            print("Error: PDF path is required for test mode")
            sys.exit(1)
        results = test_anonymization_quality(args.pdf)
        print(f"Test results: {'SUCCESS' if results['success'] else 'FAILED'}")
        print(f"Metrics: {results.get('metrics', {})}")
        
    elif args.mode == 'batch':
        os.makedirs(args.output, exist_ok=True)
        results_df = batch_test(num_tests=args.count, output_dir=args.output)
        success_rate = (results_df['success'].sum() / len(results_df)) * 100
        print(f"Batch test completed with {success_rate:.1f}% success rate")
        print(f"Report saved to: {os.path.join(args.output, 'test_report.pdf')}")

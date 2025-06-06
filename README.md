# PDF Anonymizer (Anonimizador de PDF)

Um aplicativo desktop em Python para anonimização de documentos PDF contendo dados pessoais em português.

## Funcionalidades

- Detecção e anonimização de dados pessoais sensíveis (nomes, CPFs, emails, telefones, etc.)
- Interface gráfica amigável utilizando Tkinter
- Preservação de mapeamentos para possível reversão da anonimização
- Validação da qualidade da anonimização utilizando modelos de linguagem
- Testes automatizados e geração de relatórios de qualidade

## Documentação

- [Instalação detalhada](INSTALLATION.md) - Guia completo para configurar o aplicativo
- [Resolução de problemas](TROUBLESHOOTING.md) - Soluções para problemas comuns
- [Problemas e melhorias](issues_and_improvements.md) - Status do projeto e melhorias planejadas

## Instalação Rápida

```bash
# Instalação de dependências básicas
pip install -r requirements.txt

# Instalação do modelo de idioma português para spaCy
python -m spacy download pt_core_news_sm

# Instalação do PyTorch (necessário para validação)
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

## Executando a Aplicação

```bash
python main.py
```

## Como Usar

1. Clique em "Carregar PDF" para selecionar um documento PDF
2. Clique em "Anonimizar" para iniciar o processo de detecção e anonimização
3. Após a conclusão, o documento anonimizado será salvo automaticamente
4. Use "Validar" para verificar se todos os dados pessoais foram corretamente anonimizados
5. Use "Reverter Sessão" para desfazer a anonimização atual ou "Carregar e Reverter" para desfazer uma anonimização anterior

## Arquitetura da Aplicação

- `main.py`: Ponto de entrada da aplicação
- `app.py`: Interface gráfica principal e lógica da aplicação
- `pdf_utils.py`: Funções para manipulação de PDFs
- `detection.py`: Lógica de detecção de dados sensíveis
- `anonymizer.py`: Lógica de anonimização
- `validator.py`: Validação da qualidade de anonimização
- `mapping_utils.py`: Gerenciamento dos mapeamentos de anonimização

## Testes e Validação

A aplicação inclui ferramentas abrangentes para testes:

```bash
# Executar testes rápidos
python run_tests.py --type quick

# Executar testes completos
python run_tests.py --type thorough

# Executar testes de desempenho
python run_tests.py --type performance
```

Os relatórios de teste são gerados como PDFs com visualizações e análises estatísticas.

## Limitações Atuais

- Suporta apenas texto extraível de PDFs (não realiza OCR em imagens)
- Otimizado para dados pessoais em português do Brasil
- Pode ter dificuldades com formatos complexos ou não-padronizados

## Contribuição

Contribuições são bem-vindas! Por favor, sinta-se à vontade para enviar pull requests ou reportar problemas.
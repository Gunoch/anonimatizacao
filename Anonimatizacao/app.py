import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os # Added for os.path.basename
import json # For json.JSONDecodeError
import fitz # For fitz.fitz.FZ_ERROR_GENERIC
import threading # For asynchronous operations

# Importa funções dos módulos criados
from pdf_utils import extrair_texto, salvar_pdf_anon
from detection import encontrar_dados_sensiveis
from anonymizer import anonimizar_texto
from validator import validar_anonimizacao
from mapping_utils import save_mapping, load_mapping # Added

class PDFAnonymizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Anonimizador de PDF")
        # Adjusted geometry for new log area
        self.root.geometry("600x550") # Increased height for log
        self.root.resizable(False, False)
        
        # Estado da aplicação
        self.caminho_pdf = None
        self.texto_paginas_original = None
        self.texto_paginas_anon = None
        self.mapeamento = None
        self.caminho_pdf_anon_salvo = None # To store path of saved anonymized PDF
        self.caminho_mapeamento_salvo = None # To store path of saved mapping file
        
        # Elementos da interface
        self.label_status = tk.Label(root, text="Selecione um arquivo PDF para começar.", wraplength=580) # Added wraplength
        self.label_status.pack(pady=10)
        
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        self.btn_carregar = tk.Button(btn_frame, text="Carregar PDF", command=self.carregar_pdf)
        self.btn_carregar.grid(row=0, column=0, padx=5)
        self.btn_anon = tk.Button(btn_frame, text="Anonimizar", command=self.anonimizar)
        self.btn_anon.grid(row=0, column=1, padx=5)
        self.btn_validar = tk.Button(btn_frame, text="Validar", command=self.validar)
        self.btn_validar.grid(row=0, column=2, padx=5)
        self.btn_reverter_sessao = tk.Button(btn_frame, text="Reverter Sessão", command=self.reverter_sessao) # Renamed
        self.btn_reverter_sessao.grid(row=0, column=3, padx=5)
        self.btn_carregar_e_reverter = tk.Button(btn_frame, text="Carregar e Reverter", command=self.carregar_e_reverter) # New button
        self.btn_carregar_e_reverter.grid(row=0, column=4, padx=5) # Added to grid
        
        # Desabilita botões que requerem etapas anteriores
        self.btn_anon.config(state="disabled")
        self.btn_validar.config(state="disabled")
        self.btn_reverter_sessao.config(state="disabled")
        # self.btn_carregar_e_reverter can be enabled by default or after first PDF load

        # Lock for thread-safe operations if needed, though root.after is generally safe for UI updates
        self.ui_lock = threading.Lock()
        self.validation_thread = None
        
        # Barra de progresso
        self.progress = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate") # Increased length
        self.progress.pack(pady=10)
        self.progress["value"] = 0

        # Text areas for original and anonymized text (optional preview)
        text_preview_frame = tk.Frame(root)
        text_preview_frame.pack(pady=5, fill="x", expand=False)

        self.label_original_preview = tk.Label(text_preview_frame, text="Original (primeiros 500 chars):")
        self.label_original_preview.pack(anchor="w")
        self.text_original_preview = tk.Text(text_preview_frame, height=4, width=70, state="disabled", wrap="word")
        self.text_original_preview.pack(fill="x", expand=True)

        self.label_anon_preview = tk.Label(text_preview_frame, text="Anonimizado (primeiros 500 chars):")
        self.label_anon_preview.pack(anchor="w")
        self.text_anon_preview = tk.Text(text_preview_frame, height=4, width=70, state="disabled", wrap="word")
        self.text_anon_preview.pack(fill="x", expand=True)

        # Anonymization Log Area
        log_frame = tk.Frame(root)
        log_frame.pack(pady=10, fill="both", expand=True)

        self.label_log = tk.Label(log_frame, text="Log de Anonimização (Original -> Substituto):")
        self.label_log.pack(anchor="w")
        
        self.log_text_area = tk.Text(log_frame, height=10, width=70, state="disabled", wrap="word")
        self.log_scroll = tk.Scrollbar(log_frame, command=self.log_text_area.yview)
        self.log_text_area.config(yscrollcommand=self.log_scroll.set)
        
        self.log_text_area.pack(side="left", fill="both", expand=True)
        self.log_scroll.pack(side="right", fill="y")

    def _update_preview(self, text_area, content):
        text_area.config(state="normal")
        text_area.delete("1.0", tk.END)
        text_area.insert("1.0", content[:500]) # Show first 500 chars
        text_area.config(state="disabled")

    def _update_log_area(self, mapping_data):
        self.log_text_area.config(state="normal")
        self.log_text_area.delete("1.0", tk.END)
        if mapping_data:
            log_entries = []
            for original, fake in mapping_data.items():
                log_entries.append(f'\"{original}\" -> \"{fake}\"')
            self.log_text_area.insert("1.0", "\\n".join(log_entries))
        else:
            self.log_text_area.insert("1.0", "Nenhuma substituição realizada ou mapeamento não disponível.")
        self.log_text_area.config(state="disabled")

    def carregar_pdf(self):
        """Abre um diálogo para selecionar um PDF e carrega seu caminho."""
        file_path = filedialog.askopenfilename(title="Selecione o PDF", filetypes=[("Arquivos PDF", "*.pdf")])
        if file_path:
            try:
                self.caminho_pdf = file_path
                self.btn_anon.config(state="normal")
                self.label_status.config(text=f"PDF selecionado: {os.path.basename(file_path)}. Pronto para anonimizar.")
                # Reset states from previous operations
                self.texto_paginas_original = None
                self.texto_paginas_anon = None
                self.mapeamento = None
                self.caminho_pdf_anon_salvo = None
                self.caminho_mapeamento_salvo = None
                self.btn_validar.config(state="disabled")
                self.btn_reverter_sessao.config(state="disabled")
                self._update_preview(self.text_original_preview, "")
                self._update_preview(self.text_anon_preview, "")
                self._update_log_area(None) # Clear log on new PDF load
                # Optionally, extract and show preview of original text here
                try:
                    temp_original_text_pages = extrair_texto(self.caminho_pdf)
                    self._update_preview(self.text_original_preview, "\\n".join(temp_original_text_pages))
                except fitz.fitz.FZ_ERROR_GENERIC as e:
                    messagebox.showerror("Erro de PDF", f"Não foi possível ler o arquivo PDF (pode estar corrompido ou não ser um PDF válido):\\n{e}")
                    self._update_preview(self.text_original_preview, f"Erro ao pré-visualizar: PDF inválido ou corrompido.")
                    self.caminho_pdf = None # Reset path
                    self.btn_anon.config(state="disabled")
                    self.label_status.config(text="Falha ao carregar PDF. Selecione um arquivo válido.")
                    return
                except FileNotFoundError:
                    messagebox.showerror("Erro de Arquivo", f"Arquivo PDF não encontrado: {self.caminho_pdf}")
                    self._update_preview(self.text_original_preview, "Erro ao pré-visualizar: Arquivo não encontrado.")
                    self.caminho_pdf = None # Reset path
                    self.btn_anon.config(state="disabled")
                    self.label_status.config(text="Falha ao carregar PDF. Arquivo não encontrado.")
                    return
                except Exception as e:
                    messagebox.showerror("Erro Inesperado", f"Ocorreu um erro inesperado ao carregar o PDF:\\n{e}")
                    self._update_preview(self.text_original_preview, f"Erro ao pré-visualizar: {e}")
                    self.caminho_pdf = None # Reset path
                    self.btn_anon.config(state="disabled")
                    self.label_status.config(text="Falha ao carregar PDF.")
                    return
            except Exception as e:
                messagebox.showerror("Erro Inesperado", f"Ocorreu um erro inesperado ao carregar o PDF:\\n{e}")
                self.label_status.config(text="Falha ao carregar PDF.")
                return
        else:
            # Se nenhum arquivo foi selecionado, não faz nada
            return
    
    def anonimizar(self):
        """Executa a anonimização do PDF selecionado."""
        if not self.caminho_pdf:
            messagebox.showerror("Erro de Operação", "Nenhum PDF selecionado para anonimizar.")
            return
        
        # For now, anonymization is synchronous. If it becomes too slow, it can also be threaded.
        # self._set_ui_busy(True)
        # self.label_status.config(text="Anonimizando... Por favor, aguarde.")
        # self.root.update_idletasks()

        try:
            # 1. Extração do texto
            self.progress["value"] = 0
            self.label_status.config(text="Extraindo texto do PDF...")
            self.root.update_idletasks() # Use update_idletasks
            
            self.texto_paginas_original = extrair_texto(self.caminho_pdf)
            self._update_preview(self.text_original_preview, "\n".join(self.texto_paginas_original))
            self.progress["value"] = 20
            self.label_status.config(text="Texto extraído. Detectando dados sensíveis...")
            self.root.update_idletasks()
            
            # 2. Detecção de dados sensíveis
            itens_sensiveis = encontrar_dados_sensiveis(self.texto_paginas_original)
            total_encontrados = len(itens_sensiveis)
            self.progress["value"] = 40
            self.label_status.config(text=f"{total_encontrados} dado(s) sensível(is) identificado(s). Anonimizando...")
            self.root.update_idletasks()
            
            # 3. Anonimização do texto
            self.texto_paginas_anon, self.mapeamento = anonimizar_texto(self.texto_paginas_original, itens_sensiveis)
            self._update_preview(self.text_anon_preview, "\n".join(self.texto_paginas_anon))
            self.progress["value"] = 60
            self.label_status.config(text="Texto anonimizado. Salvando arquivos...")
            self.root.update_idletasks()
            
            self._update_log_area(self.mapeamento) # Update log after anonymization

            # 4. Salvar PDF anonimizado
            self.caminho_pdf_anon_salvo = salvar_pdf_anon(self.texto_paginas_anon, self.caminho_pdf)
            self.progress["value"] = 80
            
            # 5. Salvar Mapeamento
            if self.mapeamento:
                self.caminho_mapeamento_salvo = save_mapping(self.mapeamento, self.caminho_pdf)
            status_msg = f"PDF anonimizado: {os.path.basename(self.caminho_pdf_anon_salvo)}\nMapeamento: {os.path.basename(self.caminho_mapeamento_salvo)}"
            
            self.label_status.config(text=status_msg)
            self.root.update_idletasks()
            
            # Finaliza progresso
            self.progress["value"] = 100
            # Habilita os botões de validar e reverter pós-anonimização
            self.btn_validar.config(state="normal")
            self.btn_reverter_sessao.config(state="normal")
            messagebox.showinfo("Concluído", f"Anonimização concluída.\\n{status_msg}")

        except FileNotFoundError: # Should ideally be caught by carregar_pdf, but as a safeguard
            messagebox.showerror("Erro de Arquivo", f"Arquivo PDF não encontrado: {self.caminho_pdf}")
            self.label_status.config(text="Falha na anonimização: PDF não encontrado.")
            self._update_log_area(None)
        except fitz.fitz.FZ_ERROR_GENERIC as e: # From extrair_texto or salvar_pdf_anon
            messagebox.showerror("Erro de PDF", f"Erro ao processar o arquivo PDF (pode estar corrompido ou ser um formato não suportado):\\n{e}")
            self.label_status.config(text="Falha na anonimização: Erro no PDF.")
            self._update_log_area(None)
        except IOError as e: # From save_mapping
            messagebox.showerror("Erro de Arquivo", f"Erro ao salvar o arquivo de mapeamento:\\n{e}")
            self.label_status.config(text="Falha ao salvar mapeamento.")
            # Log might still be relevant if anonymization itself was ok
        except Exception as e:
            messagebox.showerror("Erro de Anonimização", f"Ocorreu uma falha inesperada durante a anonimização:\\n{e}")
            self.label_status.config(text="Falha na anonimização.")
            self._update_log_area(None)
    
    def _set_ui_busy(self, busy_status: bool):
        """Helper to enable/disable UI elements during long operations."""
        state = "disabled" if busy_status else "normal"
        self.btn_carregar.config(state=state)
        # Only enable anon if a PDF is loaded and not busy
        self.btn_anon.config(state=state if self.caminho_pdf else "disabled")
        # Only enable validate if anonymized text exists and not busy
        self.btn_validar.config(state=state if self.texto_paginas_anon else "disabled")
        # Only enable revert session if mapping exists and not busy
        self.btn_reverter_sessao.config(state=state if self.mapeamento else "disabled")
        self.btn_carregar_e_reverter.config(state=state)
        
        if busy_status:
            self.progress.start(10) # Indeterminate progress for background tasks
        else:
            self.progress.stop()
            self.progress['value'] = 0 # Reset determinate progress

    def _perform_validation(self):
        try:
            texto_anon_completo = "\\n".join(self.texto_paginas_anon)
            # This call can take time (model loading)
            texto_modelo, indicadores = validar_anonimizacao(texto_anon_completo)
            
            # Schedule UI update back on the main thread
            self.root.after(0, self._update_validation_ui, texto_modelo, indicadores, None)
        except Exception as e:
            # Schedule error display back on the main thread
            self.root.after(0, self._update_validation_ui, None, None, e)

    def _update_validation_ui(self, texto_modelo, indicadores, error):
        self._set_ui_busy(False) # Re-enable UI
        if error:
            messagebox.showerror("Erro de Validação", f"Falha ao validar anonimização:\\n{error}")
            self.label_status.config(text="Falha na validação.")
        else:
            if not indicadores:
                messagebox.showinfo("Validação", "Nenhum dado pessoal aparente foi detectado no texto anonimizado.")
            else:
                msg = "Possível dado pessoal detectado na validação: " + ", ".join(indicadores)
                msg += "\n(O modelo gerou o seguinte trecho de texto continuando o PDF: ... \"{}\")".format(texto_modelo[:100] + "..." if len(texto_modelo)>100 else texto_modelo)
                messagebox.showwarning("Validação", msg)
            self.label_status.config(text="Validação concluída.")
        self.validation_thread = None # Clear the thread reference

    def validar(self):
        """Valida o texto anonimizado em busca de possíveis dados pessoais remanescentes."""
        if not self.texto_paginas_anon:
            messagebox.showerror("Erro de Operação", "Nenhum texto anonimizado disponível para validar.")
            return
        
        if self.validation_thread and self.validation_thread.is_alive():
            messagebox.showinfo("Validação", "A validação já está em progresso.")
            return

        self._set_ui_busy(True)
        self.label_status.config(text="Validando anonimização (carregando modelo e processando)... Por favor, aguarde.")
        self.root.update_idletasks()

        # Create and start the validation thread
        self.validation_thread = threading.Thread(target=self._perform_validation, daemon=True)
        self.validation_thread.start()
    
    def reverter_sessao(self): # Renamed from reverter
        """Reverte a anonimização da sessão atual, usando o mapeamento em memória."""
        if not self.texto_paginas_anon or not self.mapeamento:
            messagebox.showerror("Erro de Reversão", "Nenhuma anonimização na sessão atual para reverter.")
            return
        
        # Constrói o texto deanonimizado usando o mapeamento (substituindo falsos -> originais)
        texto_paginas_restaurado = []
        mapeamento_inverso = {falso: orig for orig, falso in self.mapeamento.items()}
        chaves_falsas = sorted(mapeamento_inverso.keys(), key=len, reverse=True)

        for texto_anon_pagina in self.texto_paginas_anon: # Iterate through pages
            texto_restaurado_pagina = texto_anon_pagina
            for falso in chaves_falsas:
                original = mapeamento_inverso[falso]
                texto_restaurado_pagina = texto_restaurado_pagina.replace(falso, original)
            texto_paginas_restaurado.append(texto_restaurado_pagina)
        
        self._update_preview(self.text_original_preview, "\n".join(self.texto_paginas_original or []))
        self._update_preview(self.text_anon_preview, "\n".join(texto_paginas_restaurado)) # Show reverted in anon preview

        texto_original_completo = "\n".join(self.texto_paginas_original) if self.texto_paginas_original else ""
        texto_restaurado_completo = "\n".join(texto_paginas_restaurado)

        if self.texto_paginas_original and texto_restaurado_completo == texto_original_completo:
            messagebox.showinfo("Reversão da Sessão", "Reversão bem-sucedida! O texto original foi restaurado integralmente na visualização.")
        else:
            messagebox.showinfo(
                "Reversão da Sessão", 
                "Reversão concluída para visualização. O texto foi restaurado com base no mapeamento da sessão."
            )
        self.label_status.config(text="Reversão da sessão realizada.")
        # Optionally, update log to indicate reversion if desired, or clear it
        # self._update_log_area(None) 

    def carregar_e_reverter(self):
        """Carrega um PDF anonimizado e seu arquivo de mapeamento para reverter."""
        self.label_status.config(text="Selecione o PDF anonimizado...")
        self.root.update_idletasks()
        caminho_pdf_anon = filedialog.askopenfilename(
            title="Selecione o PDF Anonimizado", 
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if not caminho_pdf_anon:
            self.label_status.config(text="Reversão cancelada.")
            self._update_log_area(None) # Clear log
            return

        self.label_status.config(text="Selecione o arquivo de mapeamento (.json)...")
        self.root.update_idletasks()
        caminho_mapeamento = filedialog.askopenfilename(
            title="Selecione o Arquivo de Mapeamento (.json)", 
            filetypes=[("Arquivos JSON", "*.json")]
        )
        if not caminho_mapeamento:
            self.label_status.config(text="Reversão cancelada.")
            self._update_log_area(None) # Clear log
            return

        try:
            self.label_status.config(text="Carregando e revertendo...")
            self.root.update_idletasks()

            texto_paginas_anon_carregado = extrair_texto(caminho_pdf_anon)
            mapeamento_carregado = load_mapping(caminho_mapeamento)

            if not texto_paginas_anon_carregado: # extrair_texto might return empty list or raise error
                # This case is if extrair_texto returns empty without error, actual error caught below
                messagebox.showerror("Erro de Carga", f"Não foi possível extrair texto de: {os.path.basename(caminho_pdf_anon)}. O arquivo pode estar vazio ou ilegível.")
                self.label_status.config(text="Erro ao carregar PDF anonimizado.")
                self._update_log_area(None)
                return
            if not mapeamento_carregado: # load_mapping returns None on error
                # Error message for this is handled by the specific exceptions below if they occurred,
                # or a general one if it just returned None for other reasons.
                messagebox.showerror("Erro de Carga", f"Não foi possível carregar o mapeamento de: {os.path.basename(caminho_mapeamento)}. Verifique o console para detalhes.")
                self.label_status.config(text="Erro ao carregar mapeamento.")
                self._update_log_area(None)
                return
            # Reversão
            texto_paginas_restaurado = []
            mapeamento_inverso = {falso: orig for orig, falso in mapeamento_carregado.items()}
            chaves_falsas = sorted(mapeamento_inverso.keys(), key=len, reverse=True)

            for texto_anon_pagina in texto_paginas_anon_carregado:
                texto_restaurado_pagina = texto_anon_pagina
                for falso in chaves_falsas:
                    original = mapeamento_inverso[falso]
                    texto_restaurado_pagina = texto_restaurado_pagina.replace(falso, original)
                texto_paginas_restaurado.append(texto_restaurado_pagina)
            
            # Display reverted text in the "anonymized" preview area for simplicity
            self._update_preview(self.text_original_preview, "\n".join(texto_paginas_anon_carregado)) # Show loaded anon text
            self._update_preview(self.text_anon_preview, "\n".join(texto_paginas_restaurado)) # Show reverted text
            self._update_log_area(mapeamento_carregado) # Show the loaded mapping

            self.label_status.config(text="Reversão a partir de arquivos concluída.")
            
            # Offer to save the reverted text
            if messagebox.askyesno("Salvar Reversão", "Deseja salvar o texto revertido em um novo arquivo?"):
                caminho_salvar_revertido = filedialog.asksaveasfilename(
                    title="Salvar PDF Revertido",
                    defaultextension=".pdf",
                    filetypes=[("Arquivos PDF", "*.pdf"), ("Arquivos de Texto", "*.txt")]
                )
                if caminho_salvar_revertido:
                    if caminho_salvar_revertido.lower().endswith(".pdf"):
                        salvar_pdf_anon(texto_paginas_restaurado, caminho_salvar_revertido) # Re-using salvar_pdf_anon
                        messagebox.showinfo("Sucesso", f"PDF revertido salvo em: {os.path.basename(caminho_salvar_revertido)}")
                    else: # Save as .txt
                        with open(caminho_salvar_revertido, "w", encoding="utf-8") as f:
                            f.write("\n".join(texto_paginas_restaurado))
                        messagebox.showinfo("Sucesso", f"Texto revertido salvo em: {os.path.basename(caminho_salvar_revertido)}")
                    self.label_status.config(text=f"Texto revertido salvo em: {os.path.basename(caminho_salvar_revertido)}")
                else:
                    self.label_status.config(text="Salvamento do texto revertido cancelado.")
            else:
                messagebox.showinfo("Reversão", "Texto revertido carregado para visualização.")

        except FileNotFoundError as e:
            messagebox.showerror("Erro de Arquivo", f"Arquivo não encontrado durante a reversão:\\n{e}")
            self.label_status.config(text="Erro na reversão: Arquivo não encontrado.")
            self._update_log_area(None)
        except fitz.fitz.FZ_ERROR_GENERIC as e: # From extrair_texto
            messagebox.showerror("Erro de PDF", f"Erro ao ler o arquivo PDF anonimizado (pode estar corrompido):\\n{e}")
            self.label_status.config(text="Erro na reversão: Falha ao ler PDF.")
            self._update_log_area(None)
        except json.JSONDecodeError as e: # From load_mapping
            messagebox.showerror("Erro de Mapeamento", f"Erro ao decodificar o arquivo de mapeamento (JSON inválido):\\n{e}")
            self.label_status.config(text="Erro na reversão: JSON de mapeamento inválido.")
            self._update_log_area(None)
        except IOError as e: # From load_mapping or salvar_pdf_anon (if saving reverted)
            messagebox.showerror("Erro de Arquivo", f"Erro de I/O durante a reversão (leitura/escrita):\\n{e}")
            self.label_status.config(text="Erro na reversão: Falha de I/O.")
            self._update_log_area(None) # Clear log as state is uncertain
        except Exception as e:
            messagebox.showerror("Erro na Reversão", f"Ocorreu uma falha inesperada durante a reversão a partir de arquivos:\\n{e}")
            self.label_status.config(text="Erro na reversão.")
            self._update_log_area(None)

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFAnonymizerApp(root)
    root.mainloop()
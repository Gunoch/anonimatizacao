import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import json
import threading

# Importa funções dos módulos criados
from pdf_utils import extrair_texto, salvar_pdf_anon
from detection import encontrar_dados_sensiveis
from anonymizer import anonimizar_texto
from validator import validar_anonimizacao
from mapping_utils import save_mapping, load_mapping

class PDFAnonymizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Anonimizador de PDF")
        self.root.geometry("600x550")
        self.root.resizable(False, False)
        
        # Estado da aplicação
        self.caminho_pdf = None
        self.texto_paginas_original = None
        self.texto_paginas_anon = None
        self.mapeamento = None
        self.caminho_pdf_anon_salvo = None
        self.caminho_mapeamento_salvo = None
        
        # Threading
        self.validation_thread = None
        
        # Elementos da interface
        self.label_status = tk.Label(root, text="Selecione um arquivo PDF para começar.", wraplength=580)
        self.label_status.pack(pady=10)
        
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        self.btn_carregar = tk.Button(btn_frame, text="Carregar PDF", command=self.carregar_pdf)
        self.btn_carregar.grid(row=0, column=0, padx=5)
        self.btn_anon = tk.Button(btn_frame, text="Anonimizar", command=self.anonimizar)
        self.btn_anon.grid(row=0, column=1, padx=5)
        self.btn_validar = tk.Button(btn_frame, text="Validar", command=self.validar)
        self.btn_validar.grid(row=0, column=2, padx=5)
        self.btn_reverter_sessao = tk.Button(btn_frame, text="Reverter Sessão", command=self.reverter_sessao)
        self.btn_reverter_sessao.grid(row=0, column=3, padx=5)
        self.btn_carregar_e_reverter = tk.Button(btn_frame, text="Carregar e Reverter", command=self.carregar_e_reverter)
        self.btn_carregar_e_reverter.grid(row=0, column=4, padx=5)
        
        # Desabilita botões que requerem etapas anteriores
        self.btn_anon.config(state="disabled")
        self.btn_validar.config(state="disabled")
        self.btn_reverter_sessao.config(state="disabled")
        
        # Barra de progresso
        self.progress = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(pady=10)
        self.progress["value"] = 0

        # Text areas for original and anonymized text preview
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
        """Atualiza área de preview com conteúdo."""
        text_area.config(state="normal")
        text_area.delete("1.0", tk.END)
        text_area.insert("1.0", content[:500])  # Show first 500 chars
        text_area.config(state="disabled")

    def _update_log_area(self, mapping_data):
        """Atualiza área de log com dados de mapeamento."""
        self.log_text_area.config(state="normal")
        self.log_text_area.delete("1.0", tk.END)
        if mapping_data:
            log_entries = []
            for original, fake in mapping_data.items():
                log_entries.append(f'"{original}" -> "{fake}"')
            self.log_text_area.insert("1.0", "\n".join(log_entries))
        else:
            self.log_text_area.insert("1.0", "Nenhuma substituição realizada ou mapeamento não disponível.")
        self.log_text_area.config(state="disabled")

    def carregar_pdf(self):
        """Carrega um arquivo PDF e extrai seu texto."""
        caminho = filedialog.askopenfilename(
            title="Selecione um arquivo PDF",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        
        if caminho:
            try:
                self.label_status.config(text="Carregando PDF...")
                self.root.update_idletasks()
                
                self.caminho_pdf = caminho
                self.texto_paginas_original = extrair_texto(caminho)
                
                if not self.texto_paginas_original:
                    messagebox.showerror("Erro", "Não foi possível extrair texto do PDF. O arquivo pode estar vazio ou protegido.")
                    self.label_status.config(text="Falha ao carregar PDF.")
                    return
                
                # Update preview
                self._update_preview(self.text_original_preview, "\n".join(self.texto_paginas_original))
                
                # Habilita anonimização
                self.btn_anon.config(state="normal")
                self.label_status.config(text=f"PDF carregado: {os.path.basename(caminho)}")
                
                # Reset previous anonymization state
                self.texto_paginas_anon = None
                self.mapeamento = None
                self.btn_validar.config(state="disabled")
                self.btn_reverter_sessao.config(state="disabled")
                self._update_preview(self.text_anon_preview, "")
                self._update_log_area(None)
                
            except Exception as e:
                messagebox.showerror("Erro Inesperado", f"Ocorreu um erro inesperado ao carregar o PDF:\n{e}")
                self.label_status.config(text="Falha ao carregar PDF.")

    def _set_ui_busy(self, busy_status: bool):
        """Helper to enable/disable UI elements during long operations."""
        state = "disabled" if busy_status else "normal"
        self.btn_carregar.config(state=state)
        # Only enable anon if a PDF is loaded and not busy
        self.btn_anon.config(state=state if self.caminho_pdf and not busy_status else "disabled")
        # Only enable validate if anonymized text exists and not busy
        self.btn_validar.config(state=state if self.texto_paginas_anon and not busy_status else "disabled")
        # Only enable revert session if mapping exists and not busy
        self.btn_reverter_sessao.config(state=state if self.mapeamento and not busy_status else "disabled")
        self.btn_carregar_e_reverter.config(state=state)
        
        if busy_status:
            self.progress.start(10)  # Indeterminate progress for background tasks
        else:
            self.progress.stop()
            self.progress['value'] = 0  # Reset determinate progress

    def _anonimizar_thread(self):
        """Função executada em thread separada para processar a anonimização."""
        try:
            # 1. Extração do texto
            self.root.after(0, lambda: self.progress.config(value=0))
            self.root.after(0, lambda: self.label_status.config(text="Extraindo texto do PDF..."))
            
            self.texto_paginas_original = extrair_texto(self.caminho_pdf)
            self.root.after(0, lambda: self._update_preview(self.text_original_preview, "\n".join(self.texto_paginas_original)))
            self.root.after(0, lambda: self.progress.config(value=20))
            self.root.after(0, lambda: self.label_status.config(text="Texto extraído. Detectando dados sensíveis..."))
            
            # 2. Detecção de dados sensíveis
            itens_sensiveis = encontrar_dados_sensiveis(self.texto_paginas_original)
            total_encontrados = len(itens_sensiveis)
            self.root.after(0, lambda: self.progress.config(value=40))
            self.root.after(0, lambda: self.label_status.config(text=f"{total_encontrados} dado(s) sensível(is) identificado(s). Anonimizando..."))
            
            # 3. Anonimização do texto
            self.texto_paginas_anon, self.mapeamento = anonimizar_texto(self.texto_paginas_original, itens_sensiveis)
            self.root.after(0, lambda: self._update_preview(self.text_anon_preview, "\n".join(self.texto_paginas_anon)))
            self.root.after(0, lambda: self.progress.config(value=60))
            self.root.after(0, lambda: self.label_status.config(text="Texto anonimizado. Salvando arquivos..."))
            self.root.after(0, lambda: self._update_log_area(self.mapeamento))

            # 4. Salvar PDF anonimizado
            self.caminho_pdf_anon_salvo = salvar_pdf_anon(self.texto_paginas_anon, self.caminho_pdf)
            
            # Atualização final na thread principal
            self.root.after(0, self._finalizar_anonimizacao)
            
        except Exception as e:
            self.root.after(0, lambda: self._handle_error(str(e), "Erro na Anonimização"))

    def _finalizar_anonimizacao(self):
        """Finaliza o processo de anonimização na thread principal."""
        try:
            self.progress["value"] = 80
            self.label_status.config(text="PDF anonimizado salvo. Salvando mapeamento...")
            
            # 5. Salvar mapeamento
            self.caminho_mapeamento_salvo = save_mapping(self.mapeamento, self.caminho_pdf)
            self.progress["value"] = 100
            
            # 6. Habilitar validação e reversão
            self.btn_validar.config(state="normal")
            self.btn_reverter_sessao.config(state="normal")
            
            self.label_status.config(text=f"Anonimização concluída! Arquivo salvo em: {os.path.basename(self.caminho_pdf_anon_salvo)}")
            
            messagebox.showinfo("Concluído", f"Arquivo anonimizado salvo em:\n{self.caminho_pdf_anon_salvo}\n\nMapeamento salvo em:\n{self.caminho_mapeamento_salvo}")
            
        except Exception as e:
            self._handle_error(str(e), "Erro ao Finalizar")
        finally:
            self._set_ui_busy(False)

    def _handle_error(self, error_msg, title="Erro"):
        """Centraliza tratamento de erros na UI."""
        messagebox.showerror(title, error_msg)
        self.label_status.config(text=f"Ocorreu um erro: {error_msg[:50]}...")
        self.progress["value"] = 0
        self._set_ui_busy(False)

    def anonimizar(self):
        """Executa a anonimização do PDF selecionado em uma thread separada."""
        if not self.caminho_pdf:
            messagebox.showerror("Erro de Operação", "Nenhum PDF selecionado para anonimizar.")
            return
        
        # Configura UI para indicar processamento
        self._set_ui_busy(True)
        self.label_status.config(text="Iniciando anonimização... Por favor, aguarde.")
        
        # Inicia processo em thread separada
        threading.Thread(target=self._anonimizar_thread, daemon=True).start()

    def _perform_validation(self):
        """Executa validação em thread separada."""
        try:
            texto_anon_completo = "\n".join(self.texto_paginas_anon)
            # This call can take time (model loading)
            texto_modelo, indicadores = validar_anonimizacao(texto_anon_completo)
            
            # Schedule UI update back on the main thread
            self.root.after(0, self._update_validation_ui, texto_modelo, indicadores, None)
        except Exception as e:
            # Schedule error display back on the main thread
            self.root.after(0, self._update_validation_ui, None, None, e)

    def _update_validation_ui(self, texto_modelo, indicadores, error):
        """Atualiza UI após validação."""
        self._set_ui_busy(False)  # Re-enable UI
        if error:
            messagebox.showerror("Erro de Validação", f"Falha ao validar anonimização:\n{error}")
            self.label_status.config(text="Falha na validação.")
        else:
            if not indicadores:
                messagebox.showinfo("Validação", "Nenhum dado pessoal aparente foi detectado no texto anonimizado.")
            else:
                msg = "Possível dado pessoal detectado na validação: " + ", ".join(indicadores)
                msg += f"\n(O modelo gerou o seguinte trecho de texto continuando o PDF: ... \"{texto_modelo[:100] + '...' if len(texto_modelo)>100 else texto_modelo}\")"
                messagebox.showwarning("Validação", msg)
            self.label_status.config(text="Validação concluída.")
        self.validation_thread = None  # Clear the thread reference

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

    def reverter_sessao(self):
        """Reverte a anonimização da sessão atual, usando o mapeamento em memória."""
        if not self.texto_paginas_anon or not self.mapeamento:
            messagebox.showerror("Erro de Reversão", "Nenhuma anonimização na sessão atual para reverter.")
            return
        
        # Constrói o texto deanonimizado usando o mapeamento (substituindo falsos -> originais)
        texto_paginas_restaurado = []
        mapeamento_inverso = {falso: orig for orig, falso in self.mapeamento.items()}
        chaves_falsas = sorted(mapeamento_inverso.keys(), key=len, reverse=True)

        for texto_anon_pagina in self.texto_paginas_anon:  # Iterate through pages
            texto_restaurado_pagina = texto_anon_pagina
            for falso in chaves_falsas:
                original = mapeamento_inverso[falso]
                texto_restaurado_pagina = texto_restaurado_pagina.replace(falso, original)
            texto_paginas_restaurado.append(texto_restaurado_pagina)
        
        self._update_preview(self.text_original_preview, "\n".join(self.texto_paginas_original or []))
        self._update_preview(self.text_anon_preview, "\n".join(texto_paginas_restaurado))  # Show reverted in anon preview

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

    def _finalizar_reversao(self, texto_paginas_anon_carregado, texto_paginas_restaurado, mapeamento_carregado, error_msg):
        """Finaliza o processo de reversão na thread principal."""
        self._set_ui_busy(False)
        
        if error_msg:
            messagebox.showerror("Erro de Reversão", error_msg)
            self.label_status.config(text="Erro na reversão.")
            self._update_log_area(None)
            return
            
        # Atualiza a interface com os textos
        self._update_preview(self.text_original_preview, "\n".join(texto_paginas_anon_carregado))
        self._update_preview(self.text_anon_preview, "\n".join(texto_paginas_restaurado))
        self._update_log_area(mapeamento_carregado)
        
        self.label_status.config(text="Reversão a partir de arquivos concluída.")
        
        # Pergunta se deseja salvar
        if messagebox.askyesno("Salvar Reversão", "Deseja salvar o texto revertido em um novo arquivo?"):
            self._salvar_texto_revertido(texto_paginas_restaurado)
        else:
            messagebox.showinfo("Reversão", "Texto revertido carregado para visualização.")

    def _salvar_texto_revertido(self, texto_paginas_restaurado):
        """Salva o texto revertido em um arquivo PDF ou TXT."""
        caminho_salvar_revertido = filedialog.asksaveasfilename(
            title="Salvar PDF Revertido",
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Arquivos de Texto", "*.txt")]
        )
        if caminho_salvar_revertido:
            try:
                if caminho_salvar_revertido.lower().endswith(".pdf"):
                    salvar_pdf_anon(texto_paginas_restaurado, caminho_salvar_revertido)
                    messagebox.showinfo("Sucesso", f"PDF revertido salvo em: {os.path.basename(caminho_salvar_revertido)}")
                else:
                    with open(caminho_salvar_revertido, "w", encoding="utf-8") as f:
                        f.write("\n".join(texto_paginas_restaurado))
                    messagebox.showinfo("Sucesso", f"Texto revertido salvo em: {os.path.basename(caminho_salvar_revertido)}")
                self.label_status.config(text=f"Texto revertido salvo em: {os.path.basename(caminho_salvar_revertido)}")
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Erro ao salvar o arquivo: {str(e)}")
                self.label_status.config(text="Erro ao salvar arquivo revertido.")
        else:
            self.label_status.config(text="Salvamento do texto revertido cancelado.")

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
            self._update_log_area(None)
            return

        self.label_status.config(text="Selecione o arquivo de mapeamento (.json)...")
        self.root.update_idletasks()
        caminho_mapeamento = filedialog.askopenfilename(
            title="Selecione o Arquivo de Mapeamento (.json)", 
            filetypes=[("Arquivos JSON", "*.json")]
        )
        if not caminho_mapeamento:
            self.label_status.config(text="Reversão cancelada.")
            self._update_log_area(None)
            return
            
        # Configura a interface para processamento
        self._set_ui_busy(True)
        self.label_status.config(text="Carregando e revertendo... Por favor, aguarde.")
        self.root.update_idletasks()
        
        # Inicia processamento em thread separada
        threading.Thread(target=self._processar_reversao_thread, 
                         args=(caminho_pdf_anon, caminho_mapeamento), 
                         daemon=True).start()

    def _processar_reversao_thread(self, caminho_pdf_anon, caminho_mapeamento):
        """Função de thread para processar a reversão."""
        try:
            # Carregar texto e mapeamento
            texto_paginas_anon_carregado = extrair_texto(caminho_pdf_anon)
            mapeamento_carregado = load_mapping(caminho_mapeamento)
            
            if not texto_paginas_anon_carregado or not mapeamento_carregado:
                self.root.after(0, lambda: self._finalizar_reversao(None, None, None,
                                "Erro ao carregar o PDF ou mapeamento. Verifique se os arquivos são válidos."))
                return
                
            # Processar a reversão
            texto_paginas_restaurado = []
            mapeamento_inverso = {falso: orig for orig, falso in mapeamento_carregado.items()}
            chaves_falsas = sorted(mapeamento_inverso.keys(), key=len, reverse=True)

            for texto_anon_pagina in texto_paginas_anon_carregado:
                texto_restaurado_pagina = texto_anon_pagina
                for falso in chaves_falsas:
                    original = mapeamento_inverso[falso]
                    texto_restaurado_pagina = texto_restaurado_pagina.replace(falso, original)
                texto_paginas_restaurado.append(texto_restaurado_pagina)
                
            self.root.after(0, lambda: self._finalizar_reversao(texto_paginas_anon_carregado, 
                                                               texto_paginas_restaurado, 
                                                               mapeamento_carregado, None))
        except Exception as e:
            self.root.after(0, lambda: self._finalizar_reversao(None, None, None, str(e)))


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFAnonymizerApp(root)
    root.mainloop()

import flet as ft
import subprocess
import threading
import sys
import os
import signal
import time
import requests
import json
from flask import Flask, request as flask_request
# from waitress import serve as waitress_serve


# Arquivo de configurações
CONFIG_FILE = "printer_config.json"

def load_config():
    """Carrega configurações salvas"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"selected_printer": None}

def save_config(config):
    """Salva configurações"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False


class ImageGenerator:
    def __init__(self, IMAGE_SIZE):
        self.image = None
        self.image_path = None
        self.IMAGE_SIZE = IMAGE_SIZE
        self.FONT_SIZE = 20
        self.CODE_FONT_SIZE = 32

    def create_image(self, created_date, code, services, header, footer):
        from datetime import datetime
        from PIL import Image, ImageDraw, ImageFont

        self.image = Image.new("RGB", self.IMAGE_SIZE, color=(255, 255, 255))
        draw = ImageDraw.Draw(self.image)
        
        # Cache de fontes para melhor performance
        if not hasattr(self, '_font_cache'):
            try:
                self._font_cache = {
                    'font': ImageFont.truetype("arial.ttf", size=self.FONT_SIZE),
                    'code_font': ImageFont.truetype("arial.ttf", size=self.CODE_FONT_SIZE)
                }
            except:
                self._font_cache = {
                    'font': ImageFont.load_default(),
                    'code_font': ImageFont.load_default()
                }
        
        font = self._font_cache['font']
        code_font = self._font_cache['code_font']

        header_block = header
        code_block = f"Código: {code}"
        services_block = f"Serviços: {services}"
        date_block = f"Data: {created_date}"
        footer_block = footer

        y_positions = [
            10,
            self.CODE_FONT_SIZE + 30,
            self.FONT_SIZE * 2 + 90,
            self.FONT_SIZE * 3 + 120,
            self.FONT_SIZE * 3 + 170,
        ]

        for block, y in zip([header_block, code_block, services_block, date_block, footer_block], y_positions):
            bbox = draw.textbbox((0, 0), block, font=code_font if "Código:" in block else font)
            w = bbox[2] - bbox[0]
            x = (self.IMAGE_SIZE[0] - w) // 2
            draw.text((x, y), block, font=code_font if "Código:" in block else font, fill=(0, 0, 0))

        date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        if not os.path.exists('ticket'):
            os.makedirs('ticket')
        self.image_path = os.path.join(os.getcwd(), "ticket", f"{date}.png")

        self.image.save(self.image_path)
        return self.image_path

    def create_qrcode(self, code):
        import qrcode
        from datetime import datetime

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=4, border=4)
        qr.add_data(code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        if not os.path.exists('ticket'):
            os.makedirs('ticket')
        self.qr_path = os.path.join(os.getcwd(), "ticket", f"{date}QR.png")
        img.save(self.qr_path)
        return self.qr_path

    def combine(self):
        from PIL import Image

        img = Image.open(self.image_path)
        img2 = Image.open(self.qr_path)
        img2 = img2.resize((100, 100))
        img_width, img_height = img.size
        spacer = Image.new('RGB', (img_width, 5), color='white')
        img_with_spacer = Image.new('RGB', (img_width, img_height + 100), color='white')
        img_with_spacer.paste(spacer, (0, img_height))
        img_with_spacer.paste(img, (0, 0))
        img_with_spacer.paste(img2, (100, img_height - 50))
        img_with_spacer.save(self.image_path)
        return self.image_path


def main(page: ft.Page):
    page.title = "Cliente de Impressão - Monitor"
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_width = 980
    page.window_height = 720
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Configuração para minimizar para bandeja
    page.window_prevent_close = True
    page.window_always_on_top = False

    # Carrega configurações salvas
    config = load_config()
    
    log_view = ft.ListView(expand=True, spacing=4, auto_scroll=True)
    advanced_log_view = ft.ListView(expand=True, spacing=4, auto_scroll=True)
    
    # Toggle para logs simples/avançados
    show_advanced_logs = ft.Ref[ft.Switch]()
    current_log_view = ft.Ref[ft.Container]()
    
    status_badge = ft.Container(
        content=ft.Text("Parado", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=14),
        bgcolor=ft.Colors.RED_600,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        border_radius=16,
    )
    
    # Variável global para impressora selecionada
    selected_printer = {"name": config.get("selected_printer", None)}
    
    # Diálogo de configurações
    settings_dialog = ft.Ref[ft.AlertDialog]()
    printer_dropdown = ft.Ref[ft.Dropdown]()
    printer_status_text = ft.Ref[ft.Text]()
    
    # Controle de estado da janela
    window_state = {"minimized_to_tray": False, "really_close": False}

    def append_simple_log(message, status="info"):
        """Adiciona log simplificado para o usuário"""
        icon_map = {
            "success": ft.Icons.CHECK_CIRCLE,
            "error": ft.Icons.ERROR,
            "warning": ft.Icons.WARNING,
            "info": ft.Icons.INFO
        }
        color_map = {
            "success": ft.Colors.GREEN_600,
            "error": ft.Colors.RED_600,
            "warning": ft.Colors.ORANGE_600,
            "info": ft.Colors.BLUE_600
        }
        
        icon = icon_map.get(status, ft.Icons.INFO)
        color = color_map.get(status, ft.Colors.BLUE_600)
        
        log_view.controls.append(
            ft.Row(
                [
                    ft.Icon(icon, color=color, size=20),
                    ft.Text(message, size=14, weight=ft.FontWeight.W_500),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()

    def append_advanced_log(line, level="INFO"):
        """Adiciona log técnico detalhado"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {line.rstrip()}")
        
        color = ft.Colors.BLUE_800 if level == "INFO" else ft.Colors.RED_700
        advanced_log_view.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(level, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        padding=ft.padding.symmetric(3, 2),
                        bgcolor=color,
                        border_radius=4,
                    ),
                    ft.Text(line.rstrip(), selectable=True, size=12),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()

    def append_log(line, level="INFO"):
        """Função principal que decide qual tipo de log usar"""
        # Sempre adiciona ao log avançado
        append_advanced_log(line, level)

        # Normaliza para facilitar o matching
        l = line.lower()

        # Eventos vindos da plataforma / endpoints
        if "nova impressão recebida" in l or "nova impressão com qr recebida" in l:
            append_simple_log("📩 Nova solicitação de impressão recebida", "info")
            return
        if "código:" in l and "|" in l:
            # Log de detalhes (código e serviços)
            return  # Não mostra nos logs simples, muito detalhado
        if "ticket gerado:" in l or "ticket com qr gerado:" in l:
            append_simple_log("🖼️ Ticket de senha gerado", "info")
            return
        if "impressora configurada:" in l:
            append_simple_log("🖨️ Impressora configurada", "info")
            return
        if "impressão enviada com sucesso" in l or "impressão qr enviada com sucesso" in l:
            append_simple_log("✅ Senha impressa com sucesso", "success")
            return
        if "erro ao enviar para impressão" in l:
            append_simple_log("❌ Falha ao imprimir", "error")
            return
        if "erro geral no endpoint" in l:
            append_simple_log("⚠️ Erro interno", "error")
            return
        if "falha ao chamar" in l or "httpconnectionpool" in l:
            append_simple_log("⚠️ Falha de comunicação", "error")
            return
        if "printing server stopped" in l:
            append_simple_log("⏹️ Servidor parado", "error")
            return
        if "servidor flask iniciado" in l:
            append_simple_log("🚀 Servidor iniciado", "success")
            status_badge.content = ft.Text("Executando", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=14)
            status_badge.bgcolor = ft.Colors.GREEN_600
            page.update()
            return
        if "fila da impressora" in l and "limpa" in l:
            append_simple_log("🧹 Fila de impressão limpa", "info")
            return
        if "impressora detectada" in l:
            append_simple_log("✅ Impressora encontrada", "success")
            return
        if "impressora não encontrada" in l:
            append_simple_log("❌ Impressora não detectada", "warning")
            return

        # Fallback: erros genéricos
        if level == "ERROR" or "traceback" in l:
            append_simple_log("⚠️ Erro no sistema", "error")

    # ========== FUNÇÕES DE CONFIGURAÇÃO ==========
    
    def load_available_printers():
        """Carrega lista de impressoras disponíveis"""
        try:
            # Configurações para ocultar janela do console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run([
                "powershell", "-Command", 
                "Get-Printer | Select-Object -ExpandProperty Name"
            ], capture_output=True, text=True, timeout=10,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            if result.returncode == 0:
                printers = [p.strip() for p in result.stdout.splitlines() if p.strip()]
                return printers
            return []
        except:
            return []
    
    def open_settings(e):
        """Abre diálogo de configurações"""
        printers = load_available_printers()
        
        if not printers:
            printer_dropdown.current.options = [
                ft.dropdown.Option("Nenhuma impressora encontrada")
            ]
            printer_dropdown.current.disabled = True
        else:
            printer_dropdown.current.options = [
                ft.dropdown.Option(p) for p in printers
            ]
            printer_dropdown.current.disabled = False
            
            # Seleciona a impressora atual se existir
            if selected_printer["name"] in printers:
                printer_dropdown.current.value = selected_printer["name"]
        
        # Atualiza status
        if selected_printer["name"]:
            printer_status_text.current.value = f"✓ Impressora atual: {selected_printer['name']}"
            printer_status_text.current.color = ft.Colors.GREEN_700
        else:
            printer_status_text.current.value = "⚠ Nenhuma impressora configurada"
            printer_status_text.current.color = ft.Colors.ORANGE_700
        
        settings_dialog.current.open = True
        page.update()
    
    def save_printer_config(e):
        """Salva configuração da impressora"""
        if not printer_dropdown.current.value or printer_dropdown.current.value == "Nenhuma impressora encontrada":
            printer_status_text.current.value = "❌ Selecione uma impressora válida"
            printer_status_text.current.color = ft.Colors.RED_700
            page.update()
            return
        
        # Verifica se a impressora está disponível
        printer_name = printer_dropdown.current.value
        if not verificar_impressora_online(printer_name):
            # Mensagem compacta no status
            printer_status_text.current.value = (
                "⚠️ Impressora não disponível\n\n"
                "Verifique:\n"
                "1. Se a impressora está conectada corretamente\n"
                "   na sua máquina (cabo USB/Rede)\n"
                "2. Se a impressora está ligada\n"
                "3. Se os drivers estão instalados corretamente\n"
                "4. Nas configurações do Windows:\n"
                "   Dispositivos > Impressoras e scanners"
            )
            printer_status_text.current.color = ft.Colors.ORANGE_700
            append_simple_log(f"⚠️ Impressora '{printer_name}' não disponível", "warning")
            append_log(f"Impressora '{printer_name}' não encontrada ou está offline", "WARNING")
            append_log("╔═══════════════════════════════════════════════════╗", "WARNING")
            append_log("║  Verifique:                                       ║", "WARNING")
            append_log("║  1. Se a impressora está conectada corretamente  ║", "WARNING")
            append_log("║     na sua máquina (cabo USB/Rede)               ║", "WARNING")
            append_log("║  2. Se a impressora está ligada                  ║", "WARNING")
            append_log("║  3. Se os drivers estão instalados corretamente ║", "WARNING")
            append_log("║  4. Nas configurações do Windows:                ║", "WARNING")
            append_log("║     Dispositivos > Impressoras e scanners        ║", "WARNING")
            append_log("╚═══════════════════════════════════════════════════╝", "WARNING")
            page.update()
            return
        
        # Salva localmente
        selected_printer["name"] = printer_name
        
        # Salva no arquivo
        config = load_config()
        config["selected_printer"] = selected_printer["name"]
        
        if save_config(config):
            append_simple_log(f"🖨️ Impressora configurada: {selected_printer['name']}", "success")
            append_log(f"Impressora '{selected_printer['name']}' salva com sucesso", "INFO")
            
            # Limpa cache das funções de impressão
            if hasattr(imprimir, '_cached_printer'):
                delattr(imprimir, '_cached_printer')
            if hasattr(imprimir_qrcode, '_cached_printer'):
                delattr(imprimir_qrcode, '_cached_printer')
            
            # Fecha o diálogo automaticamente
            settings_dialog.current.open = False
            page.update()
        else:
            printer_status_text.current.value = "❌ Erro ao salvar configuração"
            printer_status_text.current.color = ft.Colors.RED_700
            page.update()
    
    def close_settings(e):
        """Fecha diálogo de configurações"""
        settings_dialog.current.open = False
        page.update()

    # ========== FIM FUNÇÕES DE CONFIGURAÇÃO ==========

    stop_flag = threading.Event()

    # Funções auxiliares para gerenciar fila e status da impressora
    def limpar_fila_impressora(impressora):
        """Limpa a fila da impressora de forma tolerante a erros"""
        try:
            # Configurações para ocultar janela do console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Tenta primeiro com PowerShell
            result = subprocess.run([
                "powershell", "-Command", 
                f"Get-PrintJob -PrinterName '{impressora}' | Remove-PrintJob"
            ], capture_output=True, text=True, timeout=10,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            if result.returncode == 0:
                append_log(f"Fila da impressora '{impressora}' limpa com sucesso", "INFO")
                return True
            else:
                append_log(f"Nota: Não foi possível limpar fila da '{impressora}' (pode estar vazia)", "INFO")
                return True
                
        except subprocess.TimeoutExpired:
            append_log(f"Timeout ao tentar limpar fila da '{impressora}'", "WARNING")
            return True
        except Exception as e:
            append_log(f"Nota: Falha ao limpar fila da '{impressora}': {e}", "WARNING")
            return True  # Continua mesmo com falha na limpeza

    def _normalize_printer_key(name: str) -> str:
        """Normaliza nome da impressora para comparação"""
        if not name:
            return ""
        # Remove espaços, hífens, underlines e torna minúsculo
        return ''.join(ch for ch in name.lower() if ch.isalnum())

    def find_installed_printers():
        """Lista todas as impressoras instaladas no sistema"""
        try:
            # Configurações para ocultar janela do console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run([
                "powershell", "-Command", 
                "Get-Printer | Select-Object -ExpandProperty Name"
            ], capture_output=True, text=True, timeout=10,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            if result.returncode == 0:
                printers = [p.strip() for p in result.stdout.splitlines() if p.strip()]
                append_log(f"Impressoras encontradas: {printers}", "INFO")
                return printers
            else:
                append_log("Nenhuma impressora encontrada via PowerShell", "WARNING")
                return []
                
        except Exception as e:
            append_log(f"Erro ao listar impressoras: {e}", "ERROR")
            return []

    def find_printer_matching(preferred_name: str):
        """Usa impressora configurada ou busca por 'Ticket-Printer'"""
        try:
            # PRIORIDADE 1: Usa impressora configurada nas configurações
            if selected_printer["name"]:
                append_log(f"Usando impressora configurada: '{selected_printer['name']}'", "INFO")
                return selected_printer["name"]
            
            # PRIORIDADE 2: Busca por 'Ticket-Printer' ou 'ticket-printer'
            if not preferred_name:
                preferred_name = "ticket-printer"
                
            preferred_key = _normalize_printer_key(preferred_name)
            installed = find_installed_printers()
            
            append_log(f"Procurando impressora: '{preferred_name}'", "INFO")
            
            # 1. PRIORIDADE MÁXIMA: Busca exata por "ticket-printer" ou "Ticket-Printer" (case insensitive)
            for p in installed:
                if p.lower() == "ticket-printer":
                    append_log(f"✓ Impressora encontrada: '{p}'", "INFO")
                    return p
            
            # 2. Busca por chave normalizada "ticketprinter"
            for p in installed:
                if _normalize_printer_key(p) == "ticketprinter":
                    append_log(f"✓ Impressora encontrada (normalizada): '{p}'", "INFO")
                    return p
            
            # 3. Busca parcial contendo "ticket" E "printer" no nome
            for p in installed:
                p_lower = p.lower()
                if "ticket" in p_lower and "printer" in p_lower:
                    append_log(f"✓ Impressora encontrada (parcial): '{p}'", "INFO")
                    return p
            
            # 4. ERRO: Impressora não encontrada
            append_log(f"❌ ERRO: Impressora 'Ticket-Printer' não encontrada!", "ERROR")
            append_log(f"   Configure uma impressora compartilhada como 'Ticket-Printer'", "ERROR")
            append_log(f"   Impressoras disponíveis: {', '.join(installed)}", "ERROR")
            
            # Retorna o nome esperado para forçar erro ao tentar usar
            return "Ticket-Printer"
            
        except Exception as e:
            append_log(f"Erro ao buscar impressora: {e}", "ERROR")
            return preferred_name or "ticket-printer"

    def verificar_impressora_online(impressora):
        """Verifica se a impressora está disponível e online"""
        try:
            # Primeiro verifica se está instalada
            installed = find_installed_printers()
            
            impressora_encontrada = None
            for p in installed:
                if p.lower() == impressora.lower() or _normalize_printer_key(p) == _normalize_printer_key(impressora):
                    impressora_encontrada = p
                    break
            
            if not impressora_encontrada:
                append_log(f"Impressora '{impressora}' não encontrada nas impressoras instaladas", "WARNING")
                return False
            
            # Configurações para ocultar janela do console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Agora verifica o STATUS da impressora (se está online/offline)
            result = subprocess.run([
                "powershell", "-Command",
                f"Get-Printer -Name '{impressora_encontrada}' | Select-Object -ExpandProperty PrinterStatus"
            ], capture_output=True, text=True, timeout=5,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            if result.returncode == 0:
                status = result.stdout.strip().lower()
                append_log(f"Status da impressora '{impressora}': {status}", "INFO")
                
                # Verifica se o status indica que está offline/erro
                if "offline" in status or "error" in status or "paused" in status:
                    append_log(f"Impressora '{impressora}' está {status} (desconectada ou com erro)", "WARNING")
                    return False
                
                append_log(f"Impressora '{impressora}' detectada e online", "INFO")
                return True
            else:
                # Se não conseguiu obter status, assume que está online (para não bloquear)
                append_log(f"Não foi possível verificar status da impressora '{impressora}'", "WARNING")
                append_log(f"Impressora detectada no sistema", "INFO")
                return True
            
        except Exception as e:
            append_log(f"Erro na verificação da impressora: {e}", "ERROR")
            # Em caso de erro, assume que está online para não bloquear a impressão
            return True

    # --- Flask integrado para endpoints de impressão ---
    printing_app = Flask("printing_app")

    @printing_app.route('/imprimir')
    def imprimir():
        try:
            # Coleta parâmetros
            created_date = flask_request.args.get('created_date', '')
            code = flask_request.args.get('code', '')
            services = flask_request.args.get('services', '')
            header = flask_request.args.get('header', '')
            footer = flask_request.args.get('footer', '')
            
            # Log de recebimento da requisição externa
            append_log(f"📩 Nova impressão recebida", "INFO")
            append_log(f"   Código: {code} | Serviços: {services}", "INFO")

            # Gera imagem do ticket
            image_generator = ImageGenerator(IMAGE_SIZE=(300, 300))
            image_path = image_generator.create_image(
                created_date=created_date, 
                code=code, 
                services=services, 
                header=header, 
                footer=footer
            )
            
            append_log(f"🖼️ Ticket gerado: {code}", "INFO")

            # Encontra impressora (usa cache para ser mais rápido)
            if not hasattr(imprimir, '_cached_printer'):
                imprimir._cached_printer = find_printer_matching('ticket-printer')
                append_log(f"🖨️ Impressora: {imprimir._cached_printer}", "INFO")
                    
            impressora = imprimir._cached_printer
            
            # Valida se há impressora configurada
            if not impressora or impressora == "Ticket-Printer":
                # Se não encontrou, verifica se tem nas configurações
                if not selected_printer["name"]:
                    append_log(f"❌ Nenhuma impressora configurada!", "ERROR")
                    return "Erro: Configure uma impressora nas Configurações", 500
                impressora = selected_printer["name"]
            
            # Limpa a fila da impressora antes de imprimir
            limpar_fila_impressora(impressora)
            
            # Prepara comando de impressão ultra-rápido
            command = ['mspaint', '/pt', image_path, impressora]
            
            # Inicia processo completamente assíncrono (fire and forget)
            # CREATE_NO_WINDOW evita janela de console piscando
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                subprocess.Popen(
                    command, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                    startupinfo=startupinfo if os.name == 'nt' else None
                )
                
                # Retorna IMEDIATAMENTE sem esperar nada
                append_log(f"✅ Impressão enviada com sucesso - {code}", "INFO")
                return "Impressão realizada com sucesso", 200
                
            except Exception as e:
                append_log(f"Erro ao enviar para impressão: {e}", "ERROR")
                return f"Erro ao imprimir: {e}", 500
                    
            except subprocess.TimeoutExpired:
                append_log("Timeout na impressão - processo demorou muito", "ERROR")
                return "Timeout na impressão", 500
            except Exception as e:
                append_log(f"Erro ao executar comando de impressão: {e}", "ERROR")
                return f"Erro ao imprimir: {e}", 500

        except Exception as e:
            append_log(f"Erro geral no endpoint /imprimir: {e}", "ERROR")
            return f"Erro ao imprimir: {e}", 500

    @printing_app.route('/imprimir/qrcode')
    def imprimir_qrcode():
        try:
            # Coleta parâmetros
            created_date = flask_request.args.get('created_date', '')
            code = flask_request.args.get('code', '')
            services = flask_request.args.get('services', '')
            header = flask_request.args.get('header', '')
            footer = flask_request.args.get('footer', '')
            qrcode_val = flask_request.args.get('qrcode', '')
            
            # Log de recebimento da requisição externa
            append_log(f"📩 Nova impressão com QR recebida", "INFO")
            append_log(f"   Código: {code} | QR: {qrcode_val[:30]}...", "INFO")

            # Gera imagem com QR Code
            image_generator = ImageGenerator(IMAGE_SIZE=(300, 300))
            image_generator.create_image(
                created_date=created_date, 
                code=code, 
                services=services, 
                header=header, 
                footer=footer
            )
            image_generator.create_qrcode(qrcode_val)
            image_path = image_generator.combine()
            
            append_log(f"🖼️ Ticket com QR gerado: {code}", "INFO")

            # Encontra impressora (usa cache para ser mais rápido)
            if not hasattr(imprimir_qrcode, '_cached_printer'):
                imprimir_qrcode._cached_printer = find_printer_matching('ticket-printer')
                append_log(f"🖨️ Impressora: {imprimir_qrcode._cached_printer}", "INFO")
                    
            impressora = imprimir_qrcode._cached_printer
            
            # Valida se há impressora configurada
            if not impressora or impressora == "Ticket-Printer":
                # Se não encontrou, verifica se tem nas configurações
                if not selected_printer["name"]:
                    append_log(f"❌ Nenhuma impressora configurada!", "ERROR")
                    return "Erro: Configure uma impressora nas Configurações", 500
                impressora = selected_printer["name"]
            
            # Limpa a fila da impressora antes de imprimir
            limpar_fila_impressora(impressora)
            
            # Prepara comando de impressão ultra-rápido
            command = ['mspaint', '/pt', image_path, impressora]
            
            # Inicia processo completamente assíncrono (fire and forget)
            # CREATE_NO_WINDOW evita janela de console piscando
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                subprocess.Popen(
                    command, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                    startupinfo=startupinfo if os.name == 'nt' else None
                )
                
                # Retorna IMEDIATAMENTE sem esperar nada
                append_log(f"✅ Impressão QR enviada com sucesso - {code}", "INFO")
                return "Impressão com QRCode realizada com sucesso", 200
                
            except Exception as e:
                append_log(f"Erro ao enviar para impressão QR: {e}", "ERROR")
                return f"Erro ao imprimir QR: {e}", 500

        except Exception as e:
            append_log(f"Erro geral no endpoint /imprimir/qrcode: {e}", "ERROR")
            return f"Erro ao imprimir QR: {e}", 500

    @printing_app.route('/status')
    def status():
        """Endpoint para verificar status do servidor"""
        return "Servidor de impressão online", 200

    def run_printing_server():
        """Executa o servidor Flask em background"""
        try:
            append_log("Iniciando servidor de impressão na porta 5000...", "INFO")
            if not os.path.exists('ticket'):
                os.makedirs('ticket')
                append_log("Diretório 'ticket' criado", "INFO")
                
            append_log("Servidor Flask iniciado em http://127.0.0.1:5000", "INFO")
            printing_app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
            
        except Exception as e:
            append_log(f"Erro no servidor de impressão: {e}", "ERROR")

    # Inicia servidor em thread separada
    server_thread = threading.Thread(target=run_printing_server, daemon=True)
    server_thread.start()

    def toggle_logs(e):
        """Alterna entre logs simples e avançados"""
        if show_advanced_logs.current.value:
            current_log_view.current.content = advanced_log_view
            current_log_view.current.bgcolor = ft.Colors.GREY_100
            append_simple_log("🔍 Modo de logs avançados ativado", "info")
        else:
            current_log_view.current.content = log_view
            current_log_view.current.bgcolor = ft.Colors.WHITE
            append_simple_log("📋 Modo de logs simples ativado", "info")
        page.update()

    def call_endpoint(path, params=None):
        """Função para testar endpoints"""
        url = f"http://localhost:5000{path}"
        append_log(f"Testando endpoint: {url}", "INFO")
        if params:
            append_log(f"Parâmetros: {params}", "INFO")
        
        try:
            response = requests.get(url, params=params or {}, timeout=10)
            append_log(f"Resposta: {response.status_code} - {response.text}", "INFO")
            
            if response.status_code == 200:
                append_simple_log(f"✅ Teste {path} executado com sucesso", "success")
            else:
                append_simple_log(f"❌ Teste {path} falhou: {response.text}", "error")
                
        except Exception as ex:
            append_log(f"Falha ao testar {url}: {ex}", "ERROR")
            append_simple_log(f"❌ Falha no teste {path}", "error")

    # Interface de teste
    header = ft.TextField(label="Cabeçalho", value="Bem-vindo")
    footer = ft.TextField(label="Rodapé", value="Obrigado")
    code = ft.TextField(label="Código", value="A123")
    services = ft.TextField(label="Serviços", value="Atendimento Geral")
    created_date = ft.TextField(label="Data", value="2025-01-01")
    qrcode_value = ft.TextField(label="QR Code", value="https://exemplo.com/senha/A123")

    def handle_test_print(e):
        params = {
            "created_date": created_date.value,
            "code": code.value,
            "services": services.value,
            "header": header.value,
            "footer": footer.value,
        }
        call_endpoint("/imprimir", params)

    def handle_test_qr(e):
        params = {
            "created_date": created_date.value,
            "code": code.value,
            "services": services.value,
            "header": header.value,
            "footer": footer.value,
            "qrcode": qrcode_value.value,
        }
        call_endpoint("/imprimir/qrcode", params)

    def handle_test_status(e):
        call_endpoint("/status")

    # Funções de controle de janela
    window_state = {"minimized_to_tray": False, "really_close": False}
    
    def show_window(e):
        """Mostra a janela novamente"""
        page.window_visible = True
        window_state["minimized_to_tray"] = False
        page.update()
        append_log("Janela restaurada da bandeja", "INFO")
    
    def quit_app(e):
        """Encerra o aplicativo completamente"""
        append_log("Encerrando aplicação...", "INFO")
        window_state["really_close"] = True
        stop_flag.set()
        # Aguarda um momento para exibir os logs
        page.update()
        threading.Timer(0.5, lambda: os._exit(0)).start()

    def on_window_event(e):
        """Gerencia eventos da janela"""
        if e.data == "close":
            # Sempre minimiza para bandeja (usuário deve usar botão Sair para fechar)
            page.window_visible = False
            window_state["minimized_to_tray"] = True
            append_log("Aplicação minimizada para bandeja do sistema", "INFO")
            append_simple_log("🔽 Minimizado para bandeja - Use o botão Sair para fechar", "info")
            page.update()

    # Toggle de logs
    log_toggle = ft.Row(
        [
            ft.Text("Logs Simples", size=12, weight=ft.FontWeight.W_500),
            ft.Switch(
                ref=show_advanced_logs,
                on_change=toggle_logs,
                value=False,
                active_color=ft.Colors.BLUE_600,
            ),
            ft.Text("Logs Avançados", size=12, weight=ft.FontWeight.W_500),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    # Diálogo de configurações
    settings_dialog_content = ft.AlertDialog(
        ref=settings_dialog,
        modal=True,
        title=ft.Text("⚙️ Configurações de Impressora", size=20, weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("Selecione a impressora para utilizar:", size=14),
                    ft.Dropdown(
                        ref=printer_dropdown,
                        label="Impressora",
                        hint_text="Escolha uma impressora",
                        width=400,
                    ),
                    ft.Divider(),
                    ft.Text(
                        ref=printer_status_text,
                        value="",
                        size=13,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                spacing=15,
                tight=True,
            ),
            padding=20,
        ),
        actions=[
            ft.TextButton("Fechar", on_click=close_settings),
            ft.FilledButton("Salvar", icon=ft.Icons.SAVE, on_click=save_printer_config),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # Logo e título
    logo_and_title = ft.Row(
        [
            # Logo (se existir o arquivo)
            ft.Image(
                src="assets/logo.png",
                width=40,
                height=40,
                fit=ft.ImageFit.CONTAIN,
                visible=os.path.exists("assets/logo.png"),
            ) if os.path.exists("assets/logo.png") else ft.Icon(
                ft.Icons.PRINT_ROUNDED,
                size=40,
                color=ft.Colors.BLUE_700,
            ),
            ft.Column(
                [
                    ft.Text("Sistema de Impressão de Senhas", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("Meu Atendimento Virtual", size=12, color=ft.Colors.GREY_600),
                ],
                spacing=0,
            ),
        ],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    controls_bar = ft.Row(
        [
            logo_and_title,
            status_badge,
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.SETTINGS,
                tooltip="Configurações",
                on_click=open_settings,
                icon_color=ft.Colors.BLUE_700,
            ),
            ft.FilledTonalButton("Testar Status", icon=ft.Icons.SEARCH, on_click=handle_test_status),
            ft.FilledTonalButton("Testar Impressão", icon=ft.Icons.PRINT, on_click=handle_test_print),
            ft.FilledTonalButton("Testar QRCode", icon=ft.Icons.QR_CODE_2, on_click=handle_test_qr),
            ft.FilledButton(
                "Sair",
                icon=ft.Icons.EXIT_TO_APP,
                on_click=quit_app,
                bgcolor=ft.Colors.RED_700,
                tooltip="Fechar completamente o aplicativo",
            ),
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    form = ft.ResponsiveRow(
        [
            ft.Container(header, col=6),
            ft.Container(footer, col=6),
            ft.Container(code, col=4),
            ft.Container(services, col=4),
            ft.Container(created_date, col=4),
            ft.Container(qrcode_value, col=12),
        ],
        run_spacing=10,
        alignment=ft.MainAxisAlignment.START,
    )

    # Container de logs com toggle
    log_container = ft.Container(
        content=log_view,
        ref=current_log_view,
        padding=12,
        expand=True,
        bgcolor=ft.Colors.WHITE,
    )

    page.add(
        settings_dialog_content,  # Adiciona o diálogo primeiro
        ft.Column(
            [
                controls_bar,
                ft.Card(ft.Container(content=form, padding=12)),
                ft.Card(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text("📋 Logs do Sistema", size=16, weight=ft.FontWeight.BOLD),
                                    ft.Container(expand=True),
                                    log_toggle,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Divider(height=1),
                            log_container,
                        ],
                        expand=True,
                        spacing=0,
                    ),
                    expand=True,
                ),
            ],
            expand=True,
            spacing=10,
        )
    )
    
    # Log inicial
    append_log("=== Cliente de Impressão de Senhas Iniciado ===", "INFO")
    append_log("Interface Flet carregada com sucesso", "INFO")
    
    # Mostra impressora configurada no log inicial
    if selected_printer["name"]:
        append_log(f"Impressora configurada: {selected_printer['name']}", "INFO")
        append_simple_log(f"🖨️ Usando: {selected_printer['name']}", "info")
    else:
        append_log("Nenhuma impressora configurada - use as Configurações", "WARNING")
        append_simple_log("⚠️ Configure a impressora", "warning")
    
    append_log("Servidor de impressão inicializando...", "INFO")
    append_simple_log("💡 Fechar a janela minimiza para bandeja", "info")
    
    # Testa se o servidor está respondendo após um breve delay
    def check_server_status():
        time.sleep(2)
        try:
            response = requests.get("http://localhost:5000/status", timeout=5)
            if response.status_code == 200:
                append_simple_log("✅ Servidor de impressão online", "success")
            else:
                append_simple_log("⚠️ Servidor respondendo com erro", "warning")
        except:
            append_simple_log("⏳ Aguardando servidor inicializar...", "info")

    threading.Thread(target=check_server_status, daemon=True).start()

    # Configura o evento de janela
    page.on_window_event = on_window_event
    
    # Configuração do ícone da bandeja
    page.window_title_bar_hidden = False
    page.window_title_bar_buttons_hidden = False
    
    # Adiciona ícone de bandeja (system tray)
    if hasattr(page, 'system_overlay_style'):
        page.system_overlay_style = ft.SystemOverlayStyle.DARK


if __name__ == "__main__":
    ft.app(target=main)
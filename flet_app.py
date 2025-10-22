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
import pystray
from PIL import Image
import webbrowser
import atexit
import logging
import queue

# Arquivo de configurações
CONFIG_FILE = "printer_config.json"

# Variáveis globais para comunicação entre threads
app_instance = None
server_running = False
backend_thread = None

def load_config():
    """Carrega configurações salvas"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"📋 Configuração carregada: {config}")
                return config
        except Exception as e:
            print(f"⚠️ Erro ao carregar configuração: {e}")
    else:
        print(f"📄 Arquivo de configuração não existe, criando padrão")
    
    default_config = {"selected_printer": None}
    save_config(default_config)
    return default_config

def save_config(config):
    """Salva configurações"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ Configuração salva: {config}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar configuração: {e}")
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


class PrintingBackend:
    """Classe responsável pelo backend de impressão"""
    def __init__(self, log_queue=None):
        self.app = None
        self.running = False
        self.thread = None
        self.log_queue = log_queue  # Fila para enviar logs para a UI
        
    def create_flask_app(self):
        """Cria a aplicação Flask"""
        app = Flask("printing_app")
        
        # Função auxiliar para enviar logs para a UI
        def send_log(message, level="INFO", simple_message=None, simple_status="info"):
            """Envia log para a UI através da fila"""
            if self.log_queue:
                self.log_queue.put({
                    "type": "log",
                    "message": message,
                    "level": level,
                    "simple_message": simple_message,
                    "simple_status": simple_status
                })
            # Também imprime no console
            print(f"[{level}] {message}")
        
        @app.route('/imprimir')
        def imprimir():
            try:
                # Coleta parâmetros
                created_date = flask_request.args.get('created_date', '')
                code = flask_request.args.get('code', '')
                services = flask_request.args.get('services', '')
                header = flask_request.args.get('header', '')
                footer = flask_request.args.get('footer', '')
                
                send_log(
                    f"Nova impressão recebida - Código: {code}", 
                    "INFO",
                    "📩 Nova solicitação de impressão recebida",
                    "info"
                )

                # Gera imagem do ticket
                image_generator = ImageGenerator(IMAGE_SIZE=(300, 300))
                image_path = image_generator.create_image(
                    created_date=created_date, 
                    code=code, 
                    services=services, 
                    header=header, 
                    footer=footer
                )
                
                send_log(
                    f"Ticket gerado: {code}",
                    "INFO",
                    "🖼️ Ticket de senha gerado",
                    "info"
                )

                # Carrega configuração da impressora
                config = load_config()
                impressora = config.get("selected_printer")
                
                send_log(f"Configuração carregada no Flask: {config}", "INFO")
                send_log(
                    f"Impressora selecionada: '{impressora}'",
                    "INFO",
                    f"🖨️ Impressora: {impressora}",
                    "info"
                )
                
                if not impressora or impressora == "null" or (isinstance(impressora, str) and impressora.strip() == ""):
                    send_log(
                        f"Nenhuma impressora configurada! Valor: {repr(impressora)}",
                        "ERROR",
                        "❌ Impressora não configurada",
                        "error"
                    )
                    return "Erro: Configure uma impressora nas Configurações", 500
                
                # Prepara comando de impressão
                command = ['mspaint', '/pt', image_path, impressora]
                
                # Inicia processo assíncrono
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
                    
                    send_log(
                        f"Impressão enviada com sucesso - {code}",
                        "INFO",
                        "✅ Senha impressa com sucesso",
                        "success"
                    )
                    return "Impressão realizada com sucesso", 200
                    
                except Exception as e:
                    send_log(
                        f"Erro ao enviar para impressão: {e}",
                        "ERROR",
                        "❌ Falha ao imprimir",
                        "error"
                    )
                    return f"Erro ao imprimir: {e}", 500

            except Exception as e:
                send_log(
                    f"Erro geral no endpoint /imprimir: {e}",
                    "ERROR",
                    "⚠️ Erro interno",
                    "error"
                )
                return f"Erro ao imprimir: {e}", 500

        @app.route('/imprimir/qrcode')
        def imprimir_qrcode():
            try:
                # Coleta parâmetros
                created_date = flask_request.args.get('created_date', '')
                code = flask_request.args.get('code', '')
                services = flask_request.args.get('services', '')
                header = flask_request.args.get('header', '')
                footer = flask_request.args.get('footer', '')
                qrcode_val = flask_request.args.get('qrcode', '')
                
                send_log(
                    f"Nova impressão com QR recebida - Código: {code}",
                    "INFO",
                    "📩 Nova solicitação de impressão (QR Code)",
                    "info"
                )

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
                
                send_log(
                    f"Ticket com QR gerado: {code}",
                    "INFO",
                    "🖼️ Ticket com QR Code gerado",
                    "info"
                )

                # Carrega configuração da impressora
                config = load_config()
                impressora = config.get("selected_printer")
                
                send_log(f"Configuração carregada no Flask QR: {config}", "INFO")
                send_log(
                    f"Impressora selecionada QR: '{impressora}'",
                    "INFO",
                    f"🖨️ Impressora: {impressora}",
                    "info"
                )
                
                if not impressora or impressora == "null" or (isinstance(impressora, str) and impressora.strip() == ""):
                    send_log(
                        f"Nenhuma impressora configurada! Valor QR: {repr(impressora)}",
                        "ERROR",
                        "❌ Impressora não configurada",
                        "error"
                    )
                    return "Erro: Configure uma impressora nas Configurações", 500
                
                # Prepara comando de impressão
                command = ['mspaint', '/pt', image_path, impressora]
                
                # Inicia processo assíncrono
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
                    
                    send_log(
                        f"Impressão QR enviada com sucesso - {code}",
                        "INFO",
                        "✅ Senha com QR Code impressa",
                        "success"
                    )
                    return "Impressão com QRCode realizada com sucesso", 200
                    
                except Exception as e:
                    send_log(
                        f"Erro ao enviar para impressão QR: {e}",
                        "ERROR",
                        "❌ Falha ao imprimir QR Code",
                        "error"
                    )
                    return f"Erro ao imprimir QR: {e}", 500

            except Exception as e:
                send_log(
                    f"Erro geral no endpoint /imprimir/qrcode: {e}",
                    "ERROR",
                    "⚠️ Erro interno (QR Code)",
                    "error"
                )
                return f"Erro ao imprimir QR: {e}", 500

        @app.route('/status')
        def status():
            """Endpoint para verificar status do servidor"""
            return "Servidor de impressão online", 200

        @app.route('/shutdown', methods=['POST'])
        def shutdown():
            """Endpoint para desligar o servidor"""
            self.running = False
            # Usa threading para encerrar o servidor de forma segura
            def shutdown_server():
                time.sleep(0.1)  # Pequeno delay para enviar resposta
                os._exit(0)
            
            threading.Thread(target=shutdown_server, daemon=True).start()
            return 'Server shutting down...', 200
            
        return app
    
    def start(self):
        """Inicia o servidor backend"""
        if self.running:
            return
            
        self.app = self.create_flask_app()
        self.running = True
        
        def run_server():
            try:
                print("🚀 Iniciando servidor de impressão na porta 5000...")
                if not os.path.exists('ticket'):
                    os.makedirs('ticket')
                    
                # Configura logging para ser mais silencioso
                log = logging.getLogger('werkzeug')
                log.setLevel(logging.ERROR)
                    
                self.app.run(host='127.0.0.1', port=5000, debug=False, threaded=True, use_reloader=False)
                
            except Exception as e:
                print(f"Erro no servidor de impressão: {e}")
            finally:
                self.running = False
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        print("✅ Servidor backend iniciado em thread separada")
    
    def stop(self):
        """Para o servidor backend"""
        if not self.running:
            return
            
        try:
            print("🔴 Parando servidor backend...")
            self.running = False
            
            # Tenta parar graciosamente primeiro
            try:
                requests.post("http://localhost:5000/shutdown", timeout=1)
                print("✅ Servidor backend parado graciosamente")
            except:
                # Se não conseguir parar graciosamente, força o encerramento
                print("⚠️ Forçando encerramento do servidor backend")
                
        except Exception as e:
            print(f"⚠️ Erro ao parar servidor: {e}")
        
        self.running = False


class DesktopApp:
    """Classe principal que gerencia o aplicativo desktop"""
    def __init__(self):
        self.message_queue = queue.Queue()
        self.backend = PrintingBackend(log_queue=self.message_queue)
        self.tray_app = None
        self.flet_process = None
        self.gui_visible = False
        self.should_quit = False
        
    def start_backend(self):
        """Inicia o backend"""
        self.backend.start()
        
    def stop_backend(self):
        """Para o backend"""
        self.backend.stop()
        
    def create_gui(self):
        """Cria e exibe a interface gráfica"""
        if self.gui_visible:
            return
            
        print("🎨 Iniciando interface gráfica...")
        self.gui_visible = True
        
        # Executa Flet na thread principal
        try:
            ft.app(target=self.create_flet_app, port=0)
        except Exception as e:
            print(f"Erro na interface: {e}")
        finally:
            self.gui_visible = False
        
    def create_flet_app(self, page: ft.Page):
        """Cria a aplicação Flet"""
        # Chama a função main_gui passando a referência para este desktop_app
        main_gui(page, self)
        
    def process_messages(self):
        """Processa mensagens da queue de comunicação"""
        try:
            # Processa até 10 mensagens por vez para evitar loop infinito
            for _ in range(10):
                try:
                    message = self.message_queue.get_nowait()
                    
                    if message == "OPEN_GUI":
                        if not self.gui_visible:
                            print("🎨 Abrindo interface pela solicitação do tray...")
                            try:
                                self.create_gui()
                            except Exception as e:
                                print(f"❌ Erro ao abrir GUI: {e}")
                        else:
                            print("Interface já está visível")
                            
                    elif message == "QUIT_APP":
                        print("🔴 Processando solicitação de encerramento...")
                        self.quit_application()
                        return  # Sai imediatamente após quit
                        
                except queue.Empty:
                    break  # Não há mais mensagens
                    
        except Exception as e:
            print(f"Erro ao processar mensagens: {e}")
    
    def quit_application(self):
        """Encerra completamente o aplicativo"""
        print("🔴 Encerrando aplicação...")
        
        # Marca para encerrar
        self.should_quit = True
        
        try:
            # Para o tray primeiro
            if self.tray_app and self.tray_app.tray_icon:
                try:
                    print("🔴 Parando ícone da bandeja...")
                    self.tray_app.tray_icon.stop()
                except Exception as e:
                    print(f"⚠️ Erro ao parar tray: {e}")
            
            # Para o backend
            print("🔴 Parando backend...")
            self.stop_backend()
            
            # Pequeno delay para permitir cleanup
            time.sleep(0.5)
            
        except Exception as e:
            print(f"⚠️ Erro durante encerramento: {e}")
        finally:
            # Força o encerramento
            print("🔴 Encerramento forçado")
            os._exit(0)


class TrayApp:
    def __init__(self, desktop_app):
        self.desktop_app = desktop_app
        self.tray_icon = None
        self.create_tray_icon()
        
    def create_tray_icon(self):
        """Cria o ícone da bandeja do sistema"""
        try:
            # Usa o logo PNG para o ícone da bandeja
            if os.path.exists("assets/logo.png"):
                try:
                    image = Image.open("assets/logo.png")
                    # Converte para RGB se necessário e redimensiona para 64x64
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    image = image.resize((64, 64), Image.Resampling.LANCZOS)
                    print("✅ Ícone da bandeja carregado de assets/logo.png")
                except Exception as png_error:
                    print(f"⚠️ Erro ao carregar assets/logo.png: {png_error}")
                    # Fallback para imagem simples
                    image = Image.new('RGB', (64, 64), color='blue')
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(image)
                    draw.rectangle([16, 16, 48, 48], fill='white')
            else:
                print("⚠️ Arquivo assets/logo.png não encontrado, usando ícone padrão")
                # Cria uma imagem simples para o ícone
                image = Image.new('RGB', (64, 64), color='blue')
                from PIL import ImageDraw
                draw = ImageDraw.Draw(image)
                draw.rectangle([16, 16, 48, 48], fill='white')
            
            # Define o menu
            menu = pystray.Menu(
                pystray.MenuItem("Abrir Interface", self.show_window),
                pystray.MenuItem("Status do Servidor", self.check_status),
                pystray.MenuItem("Sair", self.quit_app)
            )
            
            self.tray_icon = pystray.Icon("printing_app", image, "Serviço de Impressão", menu)
            print("Ícone da bandeja criado com sucesso")
            
        except Exception as e:
            print(f"Erro ao criar ícone da bandeja: {e}")
            self.tray_icon = None
    
    def run_tray(self):
        """Executa o ícone da bandeja em thread separada"""
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                if self.tray_icon:
                    print(f"Iniciando ícone da bandeja (tentativa {retry_count + 1})")
                    self.tray_icon.run_detached()
                    print("Ícone da bandeja iniciado com sucesso")
                    break
                else:
                    print("Ícone da bandeja não foi criado")
                    break
                    
            except Exception as e:
                retry_count += 1
                print(f"Erro ao executar tray (tentativa {retry_count}): {e}")
                if retry_count < max_retries:
                    time.sleep(1)
                    try:
                        # Recria o ícone se houve erro
                        self.create_tray_icon()
                    except:
                        pass
    
    def show_window(self, icon=None, item=None):
        """Solicita abertura da interface gráfica via message queue"""
        try:
            print("📱 Solicitando abertura da interface...")
            if not self.desktop_app.gui_visible:
                # Envia mensagem para a thread principal abrir a GUI
                self.desktop_app.message_queue.put("OPEN_GUI")
                print("✅ Solicitação de abertura enviada")
            else:
                print("Interface já está aberta")
        except Exception as e:
            print(f"Erro ao solicitar janela: {e}")
    
    def check_status(self, icon=None, item=None):
        """Verifica status do servidor"""
        try:
            response = requests.get("http://localhost:5000/status", timeout=5)
            if response.status_code == 200:
                self.show_notification("Servidor Online", "Serviço de impressão está rodando normalmente")
            else:
                self.show_notification("Servidor com Problemas", f"Status: {response.status_code}")
        except Exception as e:
            self.show_notification("Erro de Conexão", f"Não foi possível conectar ao servidor: {e}")
    
    def show_notification(self, title, message):
        """Mostra notificação do sistema"""
        if self.tray_icon:
            self.tray_icon.notify(message, title)
    
    def quit_app(self, icon=None, item=None):
        """Solicita encerramento do aplicativo via message queue"""
        try:
            print("🔴 Solicitando encerramento do aplicativo...")
            self.desktop_app.should_quit = True
            
            # Tenta enviar mensagem pela queue primeiro
            try:
                self.desktop_app.message_queue.put_nowait("QUIT_APP")
            except:
                # Se a queue falhar, chama diretamente
                self.desktop_app.quit_application()
                
        except Exception as e:
            print(f"Erro ao solicitar encerramento: {e}")
            # Força encerramento em caso de erro
            time.sleep(0.2)
            os._exit(0)


def main_gui(page: ft.Page, desktop_app):
    page.title = "Cliente de Impressão - Monitor"
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_width = 980
    page.window_height = 720
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Configuração do ícone da janela (aparece na barra de tarefas)
    if os.path.exists("assets/logo.png"):
        page.window_icon = "assets/logo.png"
        print("✅ Ícone da janela configurado: assets/logo.png")
    else:
        print("⚠️ Arquivo assets/logo.png não encontrado para ícone da janela")
    
    # Configuração para comportamento igual ao Spotify
    page.window_minimizable = True
    page.window_maximizable = True
    page.window_always_on_top = False
    
    # Variável para controlar se é um fechamento real ou apenas minimizar
    page.real_close = False

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
    
    # Referência para o desktop app (para poder fechar a interface)
    page.desktop_app = desktop_app
    
    # O tray é gerenciado pela classe DesktopApp, não aqui

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
        if ("servidor flask iniciado" in l or "servidor de impressão na porta 5000" in l or 
            "servidor backend iniciado" in l or "serving flask app" in l or 
            "running on http://127.0.0.1:5000" in l):
            append_simple_log("🚀 Servidor iniciado", "success")
            update_server_status(True)
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
    
    # Função para processar logs vindos do Flask (através da fila)
    def process_log_queue(e):
        """Processa logs da fila de mensagens do Flask"""
        try:
            while not desktop_app.message_queue.empty():
                log_msg = desktop_app.message_queue.get_nowait()
                
                if log_msg.get("type") == "log":
                    # Adiciona ao log avançado
                    append_advanced_log(log_msg["message"], log_msg["level"])
                    
                    # Se tem mensagem simples, adiciona ao log simples
                    if log_msg.get("simple_message"):
                        append_simple_log(log_msg["simple_message"], log_msg.get("simple_status", "info"))
        except queue.Empty:
            pass
        except Exception as error:
            print(f"Erro ao processar fila de logs: {error}")
    
    # Timer para processar logs da fila a cada 500ms
    log_timer = ft.Ref[ft.Container]()
    def start_log_timer():
        import asyncio
        async def timer_loop():
            while True:
                process_log_queue(None)
                await asyncio.sleep(0.5)
        
        # Inicia o loop em uma task
        page.run_task(timer_loop)

    # ========== FUNÇÕES DE CONFIGURAÇÃO ==========
    
    # Cache de impressoras para melhorar performance
    printers_cache = {"list": None, "timestamp": 0}
    CACHE_DURATION = 30  # Cache válido por 30 segundos
    
    def test_print_config(printer_name):
        """Testa a impressora fazendo uma impressão real de teste"""
        try:
            from datetime import datetime
            from PIL import Image, ImageDraw, ImageFont
            
            # Cria uma imagem pequena de teste
            img = Image.new("RGB", (280, 150), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            try:
                font_title = ImageFont.truetype("arial.ttf", size=16)
                font_text = ImageFont.truetype("arial.ttf", size=12)
            except:
                font_title = ImageFont.load_default()
                font_text = ImageFont.load_default()
            
            # Desenha o texto de teste
            draw.text((10, 10), "TESTE DE CONFIGURACAO", font=font_title, fill=(0, 0, 0))
            draw.text((10, 40), f"Impressora: {printer_name}", font=font_text, fill=(0, 0, 0))
            draw.text((10, 60), f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", font=font_text, fill=(0, 0, 0))
            draw.text((10, 80), "Status: Configurada com sucesso!", font=font_text, fill=(0, 128, 0))
            draw.line([(10, 100), (270, 100)], fill=(0, 0, 0), width=1)
            draw.text((10, 110), "Sistema de Impressao de Senhas", font=font_text, fill=(100, 100, 100))
            
            # Salva a imagem temporária
            test_image_path = os.path.join('ticket', 'test_config.png')
            if not os.path.exists('ticket'):
                os.makedirs('ticket')
            img.save(test_image_path)
            
            # Configurações para ocultar janela do console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Tenta imprimir
            command = ['mspaint', '/pt', test_image_path, printer_name]
            result = subprocess.run(
                command,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                timeout=10,
                capture_output=True
            )
            
            # Aguarda um pouco para o comando processar
            import time
            time.sleep(1)
            
            # Remove o arquivo temporário
            try:
                if os.path.exists(test_image_path):
                    os.remove(test_image_path)
            except:
                pass
            
            if result.returncode == 0:
                append_log(f"✅ Teste de impressão enviado para '{printer_name}'", "INFO")
                return True
            else:
                append_log(f"❌ Falha no teste de impressão: {result.stderr.decode() if result.stderr else 'Erro desconhecido'}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            append_log(f"⚠️ Timeout ao enviar teste de impressão", "WARNING")
            return False
        except Exception as e:
            append_log(f"❌ Erro ao testar impressão: {e}", "ERROR")
            return False
    
    def load_available_printers():
        """Carrega lista de impressoras disponíveis de forma otimizada"""
        # Verifica se tem cache válido
        current_time = time.time()
        if (printers_cache["list"] is not None and 
            current_time - printers_cache["timestamp"] < CACHE_DURATION):
            print("✅ Usando cache de impressoras")
            return printers_cache["list"]
        
        print("🔄 Carregando impressoras do sistema...")
        try:
            # Configurações para ocultar janela do console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Comando PowerShell otimizado com timeout reduzido
            result = subprocess.run([
                "powershell", "-NoProfile", "-NonInteractive", "-Command", 
                "Get-Printer | Select-Object -ExpandProperty Name"
            ], capture_output=True, text=True, timeout=5,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            if result.returncode == 0:
                printers = [p.strip() for p in result.stdout.splitlines() if p.strip()]
                # Atualiza cache
                printers_cache["list"] = printers
                printers_cache["timestamp"] = time.time()
                print(f"✅ {len(printers)} impressora(s) carregada(s)")
                return printers
            
            printers_cache["list"] = []
            printers_cache["timestamp"] = time.time()
            return []
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout ao carregar impressoras")
            printers_cache["list"] = []
            printers_cache["timestamp"] = time.time()
            return []
        except Exception as e:
            print(f"⚠️ Erro ao carregar impressoras: {e}")
            printers_cache["list"] = []
            printers_cache["timestamp"] = time.time()
            return []
    
    def open_settings(e):
        """Abre diálogo de configurações"""
        # Mostra diálogo imediatamente com estado de carregamento
        printer_dropdown.current.options = [
            ft.dropdown.Option("🔄 Carregando impressoras...")
        ]
        printer_dropdown.current.value = "🔄 Carregando impressoras..."
        printer_dropdown.current.disabled = True
        
        # Atualiza status
        if selected_printer["name"]:
            printer_status_text.current.value = f"✓ Impressora atual: {selected_printer['name']}"
            printer_status_text.current.color = ft.Colors.GREEN_700
        else:
            printer_status_text.current.value = "⚠ Nenhuma impressora configurada"
            printer_status_text.current.color = ft.Colors.ORANGE_700
        
        # Abre o diálogo imediatamente
        settings_dialog.current.open = True
        page.update()
        
        # Carrega impressoras em thread separada
        def load_printers_async():
            printers = load_available_printers()
            
            # Função para atualizar UI na thread principal
            def update_ui():
                if not printers:
                    printer_dropdown.current.options = [
                        ft.dropdown.Option("Nenhuma impressora encontrada")
                    ]
                    printer_dropdown.current.value = "Nenhuma impressora encontrada"
                    printer_dropdown.current.disabled = True
                else:
                    printer_dropdown.current.options = [
                        ft.dropdown.Option(p) for p in printers
                    ]
                    printer_dropdown.current.disabled = False
                    
                    # Seleciona a impressora atual se existir
                    if selected_printer["name"] in printers:
                        printer_dropdown.current.value = selected_printer["name"]
                    else:
                        printer_dropdown.current.value = None
                
                page.update()
            
            # Atualiza UI na thread principal usando page.run_task
            try:
                page.run_task(update_ui)
            except:
                # Fallback: atualiza diretamente (funciona em algumas versões do Flet)
                update_ui()
        
        # Executa carregamento em thread separada
        threading.Thread(target=load_printers_async, daemon=True).start()
    
    def save_printer_config(e):
        """Salva configuração da impressora"""
        if not printer_dropdown.current.value or printer_dropdown.current.value == "Nenhuma impressora encontrada":
            printer_status_text.current.value = "❌ Selecione uma impressora válida"
            printer_status_text.current.color = ft.Colors.RED_700
            page.update()
            return
        
        printer_name = printer_dropdown.current.value
        
        # Mostra loading
        printer_status_text.current.value = "🔄 Verificando impressora..."
        printer_status_text.current.color = ft.Colors.BLUE_700
        printer_dropdown.current.disabled = True
        page.update()
        
        # Executa verificação e salvamento em thread separada
        def save_async():
            # Mostra mensagem de teste
            def update_testing_message():
                printer_status_text.current.value = "🖨️ Enviando impressão de teste..."
                printer_status_text.current.color = ft.Colors.BLUE_700
                page.update()
            
            try:
                page.run_task(update_testing_message)
            except:
                update_testing_message()
            
            # Testa a impressão real
            test_result = test_print_config(printer_name)
            
            def update_result():
                # Reabilita dropdown
                printer_dropdown.current.disabled = False
                
                if not test_result:
                    # Mensagem de erro no teste
                    printer_status_text.current.value = (
                        "❌ Falha no teste de impressão!\n\n"
                        "A impressora pode estar:\n"
                        "1. Desligada (sem energia)\n"
                        "2. Desconectada do cabo USB/Rede\n"
                        "3. Com a tampa aberta\n"
                        "4. Sem papel\n"
                        "5. Com erro de driver\n\n"
                        "Verifique a impressora e tente novamente."
                    )
                    printer_status_text.current.color = ft.Colors.RED_700
                    append_simple_log(f"❌ Teste de impressão falhou em '{printer_name}'", "error")
                    append_log(f"Impressora '{printer_name}' não respondeu ao teste de impressão", "ERROR")
                    append_log("╔═══════════════════════════════════════════════════╗", "ERROR")
                    append_log("║  A impressora pode estar:                        ║", "ERROR")
                    append_log("║  1. Desligada (sem energia)                      ║", "ERROR")
                    append_log("║  2. Desconectada do cabo USB/Rede                ║", "ERROR")
                    append_log("║  3. Com a tampa aberta                           ║", "ERROR")
                    append_log("║  4. Sem papel                                    ║", "ERROR")
                    append_log("║  5. Com erro de driver                           ║", "ERROR")
                    append_log("╚═══════════════════════════════════════════════════╝", "ERROR")
                    page.update()
                    return
                
                # Salva localmente
                selected_printer["name"] = printer_name
                
                # Salva no arquivo
                config = load_config()
                config["selected_printer"] = selected_printer["name"]
                
                if save_config(config):
                    # Mensagem de sucesso
                    printer_status_text.current.value = (
                        f"✅ Impressora '{printer_name}' configurada!\n\n"
                        "✅ Teste de impressão enviado com sucesso!\n"
                        "Verifique se o ticket de teste foi impresso."
                    )
                    printer_status_text.current.color = ft.Colors.GREEN_700
                    
                    append_simple_log(f"🖨️ Impressora configurada: {selected_printer['name']}", "success")
                    append_log(f"Impressora '{selected_printer['name']}' configurada e testada com sucesso", "INFO")
                    
                    # Cache de impressora será limpo automaticamente no backend
                    
                    # Aguarda 2 segundos para mostrar a mensagem antes de fechar
                    import time
                    time.sleep(2)
                    
                    # Fecha o diálogo automaticamente
                    settings_dialog.current.open = False
                    page.update()
                else:
                    printer_status_text.current.value = "❌ Erro ao salvar configuração"
                    printer_status_text.current.color = ft.Colors.RED_700
                    page.update()
            
            # Atualiza UI na thread principal
            try:
                page.run_task(update_result)
            except:
                update_result()
        
        # Executa salvamento em thread separada
        threading.Thread(target=save_async, daemon=True).start()
    
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
            
            # Verifica múltiplos aspectos da impressora usando PowerShell
            result = subprocess.run([
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                f"$p = Get-Printer -Name '{impressora_encontrada}'; "
                f"Write-Output \"Status:$($p.PrinterStatus)\"; "
                f"Write-Output \"JobCount:$($p.JobCount)\"; "
                f"$jobs = Get-PrintJob -PrinterName '{impressora_encontrada}' -ErrorAction SilentlyContinue; "
                f"if ($jobs) {{ $errorJobs = ($jobs | Where-Object {{ $_.JobStatus -like '*Error*' -or $_.JobStatus -like '*Offline*' }}); "
                f"Write-Output \"ErrorJobs:$($errorJobs.Count)\" }} else {{ Write-Output 'ErrorJobs:0' }}"
            ], capture_output=True, text=True, timeout=8,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            if result.returncode == 0:
                output = result.stdout.strip().lower()
                append_log(f"Verificação detalhada da impressora '{impressora}': {output}", "INFO")
                
                # Verifica se há erros explícitos
                if "offline" in output or "error" in output or "paused" in output:
                    append_log(f"Impressora '{impressora}' reportou erro ou está offline", "WARNING")
                    return False
                
                # Verifica se há trabalhos com erro
                if "errorjobs:" in output:
                    try:
                        error_count = int(output.split("errorjobs:")[1].split()[0])
                        if error_count > 0:
                            append_log(f"Impressora '{impressora}' tem {error_count} trabalho(s) com erro na fila", "WARNING")
                            # Não bloqueia por trabalhos com erro, mas avisa
                    except:
                        pass
                
                append_log(f"Impressora '{impressora}' passou na verificação", "INFO")
                return True
            else:
                # Se não conseguiu obter informações detalhadas, faz verificação básica
                append_log(f"Verificação detalhada falhou, tentando verificação básica...", "WARNING")
                result_basic = subprocess.run([
                    "powershell", "-NoProfile", "-Command",
                    f"Get-Printer -Name '{impressora_encontrada}' | Select-Object -ExpandProperty PrinterStatus"
                ], capture_output=True, text=True, timeout=5,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                if result_basic.returncode == 0:
                    status = result_basic.stdout.strip().lower()
                    append_log(f"Status básico da impressora '{impressora}': {status}", "INFO")
                    
                    if "offline" in status or "error" in status or "paused" in status:
                        append_log(f"Impressora '{impressora}' está {status}", "WARNING")
                        return False
                
                # Se chegou aqui, assume que está disponível
                append_log(f"Impressora '{impressora}' detectada no sistema", "INFO")
                return True
            
        except Exception as e:
            append_log(f"Erro na verificação da impressora: {e}", "ERROR")
            # Em caso de erro, assume que está online para não bloquear a impressão
            return True

    # O servidor Flask agora é gerenciado pela classe PrintingBackend

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

    # ========== FUNÇÕES DE GERENCIAMENTO DA INTERFACE ==========
    
    def minimize_to_tray(e=None):
        """Minimiza a janela para a bandeja do sistema"""
        try:
            append_log("Minimizando aplicação para bandeja do sistema...", "INFO")
            append_simple_log("🔽 Aplicação minimizada para bandeja", "info")
            
            # Oculta a janela
            page.window_visible = False
            
            # Mostra notificação
            if desktop_app.tray_app:
                desktop_app.tray_app.show_notification(
                    "Serviço de Impressão", 
                    "Aplicação minimizada para bandeja. Continua rodando em segundo plano.\n\n"
                    "Clique com o botão direito no ícone da bandeja para abrir ou sair."
                )
            
            page.update()
            
        except Exception as ex:
            append_log(f"Erro ao minimizar para bandeja: {ex}", "ERROR")
    
    def restore_from_tray():
        """Restaura a janela da bandeja"""
        try:
            page.window_visible = True
            page.window_minimized = False
            page.window_to_front()
            page.update()
            append_log("Janela restaurada da bandeja", "INFO")
        except Exception as ex:
            append_log(f"Erro ao restaurar janela: {ex}", "ERROR")
    
    def on_window_event(e):
        """Gerencia eventos da janela - Interface permanece ativa em segundo plano"""
        print(f"Evento de janela: {e.data}")
        
        if e.data == "close":
            # Interface continua rodando em segundo plano: X apenas oculta a janela
            print("X clicado - minimizando interface para bandeja do sistema")
            
            # Marca como não visível
            desktop_app.gui_visible = False
            
            # Mostra notificação
            if desktop_app.tray_app:
                desktop_app.tray_app.show_notification(
                    "Serviço de Impressão", 
                    "Interface fechada. Aplicativo continua na bandeja.\n\n"
                    "Clique com o botão direito no ícone da bandeja para reabrir."
                )
            
            # Permite que o Flet feche a janela normalmente
            # O loop principal vai manter o aplicativo vivo
            return
        
        elif e.data == "minimize":
            # Minimizar normal - deixa o sistema gerenciar
            print("Minimizando janela...")
            # Não fazemos nada especial aqui
        
    def quit_app(e=None):
        """Encerra o aplicativo completamente - apenas quando usuário escolhe Sair"""
        try:
            append_log("Encerrando aplicação por solicitação do usuário...", "INFO")
            
            # Chama o método de encerramento da classe DesktopApp
            desktop_app.quit_application()
            
        except Exception as ex:
            print(f"Erro ao sair: {ex}")
            os._exit(0)

    # ========== FIM DAS FUNÇÕES DE GERENCIAMENTO ==========

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
            # Logo usando o arquivo PNG
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

    # Botão de minimizar adicionado
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
    append_simple_log("💡 Clique no X para minimizar para bandeja do sistema", "info")
    
    # Configura o evento de janela - Interface permanece em segundo plano
    page.on_window_event = on_window_event
    print("✅ Sistema configurado - Interface minimiza para bandeja ao fechar")
    
    # Função para verificar e atualizar o status do servidor
    def check_server_status():
        time.sleep(2)
        try:
            response = requests.get("http://localhost:5000/status", timeout=5)
            if response.status_code == 200:
                append_simple_log("✅ Servidor de impressão online", "success")
                # Atualiza o status badge para EXECUTANDO
                status_badge.content = ft.Text("Executando", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=14)
                status_badge.bgcolor = ft.Colors.GREEN_600
                page.update()
                
                if desktop_app.tray_app:
                    desktop_app.tray_app.show_notification("Serviço Iniciado", "Servidor de impressão está online e pronto para uso")
            else:
                append_simple_log("⚠️ Servidor respondendo com erro", "warning")
        except:
            append_simple_log("⏳ Aguardando servidor inicializar...", "info")
    
    # Função para atualizar status do servidor
    def update_server_status(online=True):
        """Atualiza o status badge do servidor"""
        if online:
            status_badge.content = ft.Text("Executando", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=14)
            status_badge.bgcolor = ft.Colors.GREEN_600
        else:
            status_badge.content = ft.Text("Parado", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=14)
            status_badge.bgcolor = ft.Colors.RED_600
        page.update()
    
    # Função para verificação inicial imediata (caso o servidor já esteja rodando)
    def check_initial_status():
        try:
            response = requests.get("http://localhost:5000/status", timeout=2)
            if response.status_code == 200:
                append_simple_log("✅ Servidor já estava online", "success")
                update_server_status(True)
                return True
            else:
                # Agenda a verificação normal com delay
                threading.Thread(target=check_server_status, daemon=True).start()
                return False
        except:
            # Servidor ainda não está pronto, agenda a verificação normal
            threading.Thread(target=check_server_status, daemon=True).start()
            return False
    
    # Função para verificação contínua do status
    def monitor_server_status():
        """Monitora o status do servidor continuamente"""
        attempts = 0
        max_attempts = 10
        
        while attempts < max_attempts:
            try:
                response = requests.get("http://localhost:5000/status", timeout=3)
                if response.status_code == 200:
                    append_simple_log("✅ Servidor de impressão online", "success")
                    update_server_status(True)
                    
                    if desktop_app.tray_app:
                        desktop_app.tray_app.show_notification("Serviço Iniciado", "Servidor de impressão está online e pronto para uso")
                    
                    return True
                else:
                    append_simple_log("⚠️ Servidor respondendo com erro", "warning")
                    
            except Exception as e:
                append_simple_log(f"⏳ Tentativa {attempts + 1}/{max_attempts} - Aguardando servidor...", "info")
                
            attempts += 1
            time.sleep(1)  # Espera 1 segundo entre tentativas
        
        # Se chegou aqui, o servidor não respondeu após todas as tentativas
        append_simple_log("❌ Servidor não respondeu após múltiplas tentativas", "error")
        return False
    
    # Inicia o timer para processar logs do Flask
    start_log_timer()
    
    # Executa verificação inicial e depois monitora
    if not check_initial_status():
        # Se a verificação inicial falhou, inicia monitoramento
        threading.Thread(target=monitor_server_status, daemon=True).start()


def main():
    """Função principal que inicializa o aplicativo desktop"""
    print("🚀 Iniciando Sistema de Impressão de Senhas...")
    
    # Cria a instância principal do aplicativo
    desktop_app = DesktopApp()
    
    # Inicializa o backend (servidor Flask)
    desktop_app.start_backend()
    
    # Aguarda um pouco para o backend inicializar
    time.sleep(1)
    
    # Cria o tray app
    desktop_app.tray_app = TrayApp(desktop_app)
    
    # Inicia o tray em thread separada
    try:
        if desktop_app.tray_app.tray_icon:
            tray_thread = threading.Thread(target=desktop_app.tray_app.run_tray, daemon=True)
            tray_thread.start()
            print("✅ Ícone da bandeja iniciado")
        else:
            print("⚠️ Falha ao criar ícone da bandeja")
    except Exception as e:
        print(f"❌ Erro ao iniciar ícone da bandeja: {e}")
    
    # Aguarda mais um pouco para tudo inicializar
    time.sleep(0.5)
    
    print("✅ Backend e tray inicializados com sucesso!")
    print("🔄 Backend rodando em background")
    print("📍 Ícone disponível na bandeja do sistema")
    
    # Inicia a interface gráfica na thread principal
    print("🎨 Iniciando interface gráfica...")
    try:
        desktop_app.create_gui()
    except KeyboardInterrupt:
        print("🔴 Interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro na interface: {e}")
    
    # Interface fechada - mas o aplicativo continua rodando via tray
    print("📱 Interface fechada - aplicativo continua na bandeja")
    print("🔍 Monitorando mensagens do tray...")
    
    # Loop principal que mantém o aplicativo vivo e processa mensagens
    try:
        while desktop_app.tray_app and desktop_app.tray_app.tray_icon and not desktop_app.should_quit:
            try:
                # Processa mensagens da queue
                desktop_app.process_messages()
                
                # Pequena pausa para não consumir muito CPU
                time.sleep(0.1)
            except Exception as e:
                print(f"⚠️ Erro no loop principal: {e}")
                time.sleep(1)  # Pausa maior em caso de erro
                
    except KeyboardInterrupt:
        print("🔴 Interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        print(f"❌ Erro crítico no loop principal: {e}")
    finally:
        # Garante que o aplicativo seja encerrado
        try:
            desktop_app.quit_application()
        except:
            print("🔴 Encerramento de emergência")
            os._exit(0)
    
    print("🏁 Loop principal encerrado")


if __name__ == "__main__":
    main()
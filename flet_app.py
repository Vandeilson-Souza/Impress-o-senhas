import flet as ft
import subprocess
import threading
import sys
import os
import signal
import time
import requests
from flask import Flask, request as flask_request
from waitress import serve as waitress_serve


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
        font = ImageFont.truetype("arial.ttf", size=self.FONT_SIZE)
        code_font = ImageFont.truetype("arial.ttf", size=self.CODE_FONT_SIZE)

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

    # Integração: o Flask de impressão roda no mesmo processo em background
    script_path = os.path.join(os.getcwd(), "printer_app.py")

    log_view = ft.ListView(expand=True, spacing=4, auto_scroll=True)
    advanced_log_view = ft.ListView(expand=True, spacing=4, auto_scroll=True)
    
    # Toggle para logs simples/avançados
    show_advanced_logs = ft.Ref[ft.Switch]()
    current_log_view = ft.Ref[ft.Container]()
    
    status_badge = ft.Chip(label=ft.Text("Parado"), color=ft.Colors.RED_400)

    def append_simple_log(message, status="success"):
        """Adiciona log simplificado para o usuário"""
        icon = ft.Icons.CHECK_CIRCLE if status == "success" else ft.Icons.ERROR if status == "error" else ft.Icons.INFO
        color = ft.Colors.GREEN_600 if status == "success" else ft.Colors.RED_600 if status == "error" else ft.Colors.BLUE_600
        
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
        
        # Adiciona ao log simples apenas se for relevante para o usuário
        if "Servidor Flask iniciado com sucesso" in line:
            append_simple_log("✅ Servidor iniciado com sucesso", "success")
        elif "Servidor Flask parado" in line:
            append_simple_log("⏹️ Servidor parado", "info")
        elif "Resposta: 200 Imprimindo" in line:
            append_simple_log("✅ Senha impressa com sucesso na impressora", "success")
        elif "Resposta: 200" in line and "Imprimindo" in line:
            append_simple_log("✅ Senha enviada para impressora com sucesso", "success")
        elif "Executando comando" in line:
            # Exibe uma mensagem simples quando um comando de impressão é executado
            append_simple_log("🖨️ Imprimindo senha...", "info")
        elif "Impressão realizada com código" in line:
            append_simple_log("✅ Senha impressa com sucesso na impressora", "success")
        elif "Impressão com QRCode realizada" in line:
            append_simple_log("✅ Senha com QRCode impressa com sucesso", "success")
        elif "Erro ao imprimir" in line or "Falha ao chamar" in line:
            append_simple_log("❌ Falha ao enviar senha para impressora", "error")
        elif "HTTPConnectionPool" in line or "Failed to establish" in line:
            append_simple_log("❌ Servidor não está respondendo", "error")
        elif "ERROR" in line or "Traceback" in line:
            append_simple_log("⚠️ Erro no sistema", "error")

    stop_flag = threading.Event()

    # --- Flask integrado para endpoints de impressão (porta 5000) ---
    printing_app = Flask("printing_app")

    @printing_app.route('/imprimir')
    def imprimir():
        try:
            image_generator = ImageGenerator(IMAGE_SIZE=(300, 300))
            created_date = flask_request.args.get('created_date')
            code = flask_request.args.get('code')
            services = flask_request.args.get('services')
            header = flask_request.args.get('header')
            footer = flask_request.args.get('footer')
            append_log(f"/imprimir recebido: code={code}", level="INFO")

            data = image_generator.create_image(created_date=created_date, code=code, services=services, header=header, footer=footer)
            append_log(f"Imagem criada: {data}", level="INFO")

            # comando de impressão (Windows mspaint)
            import subprocess
            impressora = 'ticket-printer'
            largura_pagina = '1000'
            altura_pagina = '1200'
            fator_zoom = '200'
            command = ['mspaint', '/pt', data, impressora, '1', largura_pagina, altura_pagina, '/z', fator_zoom]
            append_log(f"Executando comando: {command}", level="INFO")
            try:
                subprocess.check_call(command)
                append_log(f"Impressão realizada com código {code}", level="INFO")
            except Exception as e:
                append_log(f"Erro ao executar comando de impressão: {e}", level="ERROR")
                return f"Erro ao imprimir: {e}", 500
        except Exception as e:
            append_log(f"Erro geral no endpoint /imprimir: {e}", level="ERROR")
            return f"Erro ao imprimir: {e}", 500
        return "Imprimindo"

    @printing_app.route('/imprimir/qrcode')
    def imprimir_qrcode():
        try:
            image_generator = ImageGenerator(IMAGE_SIZE=(300, 300))
            created_date = flask_request.args.get('created_date')
            code = flask_request.args.get('code')
            services = flask_request.args.get('services')
            header = flask_request.args.get('header')
            footer = flask_request.args.get('footer')
            qrcode_val = flask_request.args.get('qrcode')

            append_log(f"/imprimir/qrcode recebido: code={code}, qrcode={qrcode_val}", level="INFO")
            image_generator.create_image(created_date=created_date, code=code, services=services, header=header, footer=footer)
            image_generator.create_qrcode(qrcode_val)
            image = image_generator.combine()

            import subprocess
            impressora = 'ticket-printer'
            largura_pagina = '1000'
            altura_pagina = '1200'
            fator_zoom = '200'
            try:
                subprocess.run(['mspaint', '/pt', image, impressora, '1', largura_pagina, altura_pagina, '/z', fator_zoom], shell=True)
                append_log(f"Impressão com QRCode realizada com código {code or qrcode_val}", level="INFO")
            except Exception as e:
                append_log(f"Erro ao executar comando de impressão QR: {e}", level="ERROR")
                return f"Erro ao imprimir: {e}", 500
        except Exception as e:
            append_log(f"Erro geral no endpoint /imprimir/qrcode: {e}", level="ERROR")
            return f"Erro ao imprimir: {e}", 500
        return "Imprimindo"

    def run_printing_server():
        try:
            if not os.path.exists('ticket'):
                os.makedirs('ticket')
            waitress_serve(printing_app, host='127.0.0.1', port=5000)
        except Exception as e:
            append_log(f"Printing server stopped: {e}", level="ERROR")

    threading.Thread(target=run_printing_server, daemon=True).start()

    def toggle_logs(e):
        """Alterna entre logs simples e avançados"""
        if show_advanced_logs.current.value:
            # Mostrar logs avançados
            current_log_view.current.content = advanced_log_view
            current_log_view.current.bgcolor = ft.Colors.GREY_100
        else:
            # Mostrar logs simples
            current_log_view.current.content = log_view
            current_log_view.current.bgcolor = ft.Colors.WHITE
        page.update()

    def call_endpoint(path, params=None):
        url = f"http://localhost:5000{path}"
        append_log(f"Chamando endpoint: {url}", level="INFO")
        if params:
            append_log(f"Parâmetros: {params}", level="INFO")
        
        # Log específico para impressão
        if "/imprimir" in path:
            if "/qrcode" in path:
                append_simple_log("📤 Enviando senha com QR Code para impressora...", "info")
            else:
                append_simple_log("📤 Enviando senha para impressora...", "info")
        
        try:
            r = requests.get(url, params=params or {}, timeout=10)
            append_log(f"Resposta: {r.status_code} {r.text}")
        except Exception as ex:
            append_log(f"Falha ao chamar {url}: {ex}", level="ERROR")

    header = ft.TextField(label="Cabeçalho", value="Bem-vindo")
    footer = ft.TextField(label="Rodapé", value="Obrigado")
    code = ft.TextField(label="Código", value="A123")
    services = ft.TextField(label="Serviços", value="Atendimento")
    created_date = ft.TextField(label="Data", value="2025-01-01")
    qrcode_value = ft.TextField(label="QR Code (conteúdo)", value="https://exemplo.com")

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

    # Toggle de logs
    log_toggle = ft.Row(
        [
            ft.Text("Logs Simples", size=12),
            ft.Switch(
                ref=show_advanced_logs,
                on_change=toggle_logs,
                value=False,
                active_color=ft.Colors.BLUE_600,
            ),
            ft.Text("Logs Avançados", size=12),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    controls_bar = ft.Row(
        [
            ft.Text("🖥️ Servidor Flask", size=16, weight=ft.FontWeight.BOLD),
            status_badge,
            ft.Container(expand=True),
            ft.FilledTonalButton("Testar impressão", icon=ft.Icons.PRINT, on_click=handle_test_print),
            ft.FilledTonalButton("Testar QRCode", icon=ft.Icons.QR_CODE_2, on_click=handle_test_qr),
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
    
    # Log inicial e início automático do servidor
    append_log("=== Cliente de Impressão de Senhas ===", level="INFO")
    append_log("Interface Flet carregada. Iniciando servidor automaticamente...", level="INFO")
    
    # O servidor de impressão já foi iniciado em background quando a UI carregou

    def on_close(e):
        stop_flag.set()
        # O server de impressão roda em thread daemon; apenas fecha a janela
        page.window_destroy()

    page.on_window_event = lambda e: on_close(e) if e.data == "close" else None


if __name__ == "__main__":
    ft.app(target=main)



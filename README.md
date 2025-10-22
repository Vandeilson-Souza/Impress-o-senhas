# 🖨️ Sistema de Impressão de Senhas - Desktop Professional

Um aplicativo desktop profissional para impressão automática de senhas/tickets, desenvolvido para funcionar como aplicativos nativos do Windows.

## 🚀 Quick Start

### 1. Clone o Repositório
```bash
git clone https://github.com/Vandeilson-Souza/Impress-o-senhas.git
cd Impress-o-senhas
```

### 2. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 3. Execute o Sistema
```bash
python flet_app.py
```

## 📋 Comandos Essenciais

### Configuração Inicial
```bash
# Clone do projeto
git clone https://github.com/Vandeilson-Souza/Impress-o-senhas.git

# Entre na pasta
cd Impress-o-senhas

# Crie um ambiente virtual (recomendado)
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

### Executar o Sistema
```bash
# Modo desenvolvimento (com logs detalhados)
python flet_app.py

# Ou execute o arquivo batch (apenas Windows)
build_exe.bat
```

### Compilar Executável
```bash
# Execute o script de build
build_exe.bat

# Ou manualmente:
pyinstaller --onefile --noconsole --name "Sistema_Impressao_Senhas" --icon="assets\icon.ico" --add-data "assets;assets" flet_app.py
```

## 🎯 Funcionalidades

### ✨ **Aplicativo Desktop Profissional**
- 🔄 **Backend independente**: Servidor roda separado da interface
- 📱 **Interface opcional**: Pode ser fechada sem afetar o serviço
- 🔔 **System Tray**: Ícone na bandeja com menu funcional
- 🚪 **Comportamento nativo**: X minimiza (não encerra), como Spotify/Discord

### 🖨️ **Sistema de Impressão**
- 📄 **Tickets simples**: Impressão básica de senhas
- 📱 **QR Code**: Tickets com código QR integrado
- ⚙️ **Configuração**: Interface para selecionar impressora
- 🔄 **API REST**: Endpoints para integração externa

### 🛠️ **Recursos Técnicos**
- 🎨 **Interface moderna**: Flet (Flutter para Python)
- 🌐 **API Backend**: Flask com endpoints RESTful
- 🖼️ **Geração de imagens**: PIL/Pillow para tickets
- 📊 **Logs inteligentes**: Modo simples e avançado
- 🔒 **Execução segura**: Processos isolados e threads gerenciadas

## 📡 API Endpoints

### Impressão Simples
```http
GET http://localhost:5000/imprimir?created_date=2025-01-01&code=A123&services=Atendimento&header=Bem-vindo&footer=Obrigado
```

### Impressão com QR Code
```http
GET http://localhost:5000/imprimir/qrcode?created_date=2025-01-01&code=A123&services=Atendimento&header=Bem-vindo&footer=Obrigado&qrcode=https://exemplo.com
```

### Status do Servidor
```http
GET http://localhost:5000/status
```

## 🔧 Integração via Python

```python
import requests

# Enviar impressão
response = requests.get('http://localhost:5000/imprimir', params={
    'created_date': '2025-01-01',
    'code': 'A123',
    'services': 'Atendimento Geral',
    'header': 'Bem-vindo',
    'footer': 'Obrigado'
})

print(response.text)  # "Impressão realizada com sucesso"
```

## 📁 Estrutura do Projeto

```
Impress-o-senhas/
├── flet_app.py                 # 🎯 Arquivo principal
├── requirements.txt            # 📦 Dependências Python
├── build_exe.bat              # 🔨 Script para gerar executável
├── SistemaImpressaoSenhas.spec # ⚙️ Configuração PyInstaller
├── printer_config.json        # 🖨️ Configurações da impressora
├── assets/                     # 🎨 Recursos (ícones, logos)
│   ├── icon.ico               # 🖼️ Ícone do aplicativo
│   └── logo.png               # 🏷️ Logo da empresa
└── ticket/                     # 📄 Tickets gerados (auto-criado)
```

## 🛠️ Dependências

| Biblioteca | Versão | Função |
|------------|--------|--------|
| **flet** | ≥0.28.3 | Interface gráfica moderna |
| **flask** | ≥3.1.0 | Servidor web backend |
| **pystray** | ≥0.19.5 | Ícone da bandeja do sistema |
| **pillow** | ≥12.0.0 | Processamento de imagens |
| **qrcode** | ≥8.0 | Geração de códigos QR |
| **requests** | ≥2.32.0 | Cliente HTTP |

## 💻 Compatibilidade

- ✅ **Windows 10/11** (Testado)
- ✅ **Python 3.8+**
- ✅ **PyInstaller** (executável único)
- ⚙️ **PowerShell** (gerenciamento de impressoras)

## 🎛️ Como Usar

### Primeira Execução
1. **Execute** `python flet_app.py`
2. **Configure** uma impressora no ícone ⚙️
3. **Teste** a impressão usando os botões
4. **Minimize** clicando no X (app continua rodando)

### Comportamento do Sistema
- **Interface**: Abre automaticamente ao iniciar
- **Fechar (X)**: Apenas oculta interface, servidor continua
- **System Tray**: Ícone sempre visível na bandeja
- **Sair**: Menu da bandeja → "Sair" (encerra completamente)

## 🐛 Troubleshooting

### Problemas Comuns

**❌ "Impressora não encontrada"**
```bash
# Verificar impressoras instaladas
Get-Printer | Select-Object Name

# Nas configurações do app, selecionar impressora correta
```

**❌ "Erro de porta 5000"**
```bash
# Verificar se porta está em uso
netstat -ano | findstr :5000

# Encerrar processo se necessário
taskkill /PID <número_do_pid> /F
```

**❌ "Módulo não encontrado"**
```bash
# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

## 🔄 Development Workflow

### Desenvolvendo Localmente
```bash
# 1. Clone e configure
git clone https://github.com/Vandeilson-Souza/Impress-o-senhas.git
cd Impress-o-senhas
python -m venv venv
venv\Scripts\activate

# 2. Instale dependências
pip install -r requirements.txt

# 3. Execute em modo desenvolvimento
python flet_app.py

# 4. Teste as funcionalidades
# - Configure impressora
# - Teste impressão simples
# - Teste impressão com QR
# - Verifique logs
```

### Build para Produção
```bash
# 1. Execute o build script
build_exe.bat

# 2. Teste o executável gerado
Sistema_Impressao_Senhas.exe

# 3. Distribuição
# O arquivo .exe é standalone, não precisa instalação
```

## 🚀 Deploy e Distribuição

### Opção 1: Executável Standalone
```bash
# Gerar executável
build_exe.bat

# Distribuir apenas o arquivo .exe
# Não precisa Python instalado na máquina alvo
```

### Opção 2: Script Python
```bash
# Na máquina alvo, instalar Python 3.8+
# Copiar pasta do projeto
# Instalar dependências: pip install -r requirements.txt
# Executar: python flet_app.py
```

## 📞 Suporte

- **Desenvolvedor**: Vandeilson Souza
- **Repositório**: [GitHub](https://github.com/Vandeilson-Souza/Impress-o-senhas)
- **Issues**: Use a aba Issues do GitHub para reportar problemas
- **Funcionalidades**: Sugestões são bem-vindas via Issues

## 📄 Licença

Este projeto é de código aberto. Consulte o arquivo LICENSE para mais detalhes.

---

### 🎯 **Resumo para Desenvolvedores**

Este é um sistema desktop profissional que combina:
- **Backend Flask** (API REST para impressão)
- **Frontend Flet** (Interface moderna e responsiva)  
- **System Tray** (Comportamento nativo de apps Windows)
- **Geração de imagens** (Tickets com texto e QR code)
- **Integração Windows** (PowerShell para gerenciar impressoras)

**Arquitetura separada** permite que o backend funcione independentemente da interface, ideal para ambientes empresariais onde o serviço precisa rodar 24/7.

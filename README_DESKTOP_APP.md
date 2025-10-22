# Sistema de Impressão de Senhas - Aplicativo Desktop Profissional

## 🎯 Sobre
Este é um aplicativo desktop profissional para impressão de senhas/tickets, desenvolvido para funcionar como aplicativos nativos do Windows (similar ao Spotify, Discord, etc.).

## ✨ Características Profissionais

### 🔄 Arquitetura Separada
- **Backend independente**: Servidor Flask roda em background separado da interface
- **Frontend opcional**: Interface Flet pode ser fechada sem afetar o serviço
- **System Tray**: Ícone na bandeja do sistema com menu funcional

### 📱 Comportamento de App Nativo
- ✅ Interface abre automaticamente ao iniciar
- ✅ Botão X apenas oculta a interface (não encerra o app)
- ✅ Backend continua funcionando mesmo com interface fechada
- ✅ Menu da bandeja: "Abrir Interface" e "Sair"
- ✅ Notificações do sistema
- ✅ Um único arquivo executável (.exe)

## 🚀 Como Usar

### Opção 1: Executar o Código Python
1. Instale as dependências: `pip install -r requirements.txt`
2. Execute: `python flet_app.py`

### Opção 2: Compilar para Executável
1. Execute: `build_exe.bat`
2. Aguarde a compilação (pode demorar alguns minutos)
3. Execute o arquivo gerado: `Sistema_Impressao_Senhas.exe`

## 📋 Instruções de Uso do Aplicativo

### Primeira Execução
1. **Execute o aplicativo** (flet_app.py ou Sistema_Impressao_Senhas.exe)
2. **A interface abrirá automaticamente**
3. **Configure uma impressora** clicando no ícone de configurações ⚙️
4. **Teste a impressão** usando os botões de teste

### Comportamento Normal
- **Servidor ativo**: Backend roda automaticamente na porta 5000
- **Interface opcional**: Pode ser fechada e reaberta quando necessário
- **System Tray**: Ícone sempre visível na bandeja do sistema

### Fechar vs Sair
- **Fechar (X)**: Apenas oculta a interface, backend continua rodando
- **Sair**: Encerra completamente o aplicativo (via menu da bandeja ou botão Sair)

## 🔧 API Endpoints

O servidor backend oferece os seguintes endpoints:

### Impressão Simples
```
GET /imprimir?created_date=2025-01-01&code=A123&services=Atendimento&header=Bem-vindo&footer=Obrigado
```

### Impressão com QR Code  
```
GET /imprimir/qrcode?created_date=2025-01-01&code=A123&services=Atendimento&header=Bem-vindo&footer=Obrigado&qrcode=https://exemplo.com
```

### Status do Servidor
```
GET /status
```

## 📁 Estrutura do Projeto
```
├── flet_app.py                 # Código principal
├── requirements.txt            # Dependências Python
├── build_exe.bat              # Script para compilar executável
├── SistemaImpressaoSenhas.spec # Configuração PyInstaller
├── printer_config.json        # Configurações da impressora
├── assets/                     # Recursos (ícones, logos)
└── ticket/                     # Imagens de tickets geradas
```

## 🏗️ Arquitetura Técnica

### Classes Principais
- **`DesktopApp`**: Gerencia o aplicativo principal
- **`PrintingBackend`**: Servidor Flask independente
- **`TrayApp`**: Ícone e menu da bandeja do sistema
- **`ImageGenerator`**: Geração de tickets/QR codes

### Threads Separadas
- **Thread Principal**: Interface Flet
- **Thread Backend**: Servidor Flask
- **Thread Tray**: Ícone da bandeja do sistema

### Comunicação
- Backend e frontend funcionam independentemente
- Comunicação via HTTP (localhost:5000)
- Configurações salvas em arquivo JSON

## 💻 Compatibilidade PyInstaller

O código foi otimizado para funcionar perfeitamente com PyInstaller:
- ✅ `--onefile`: Um único arquivo executável
- ✅ `--noconsole`: Sem janela de console
- ✅ Recursos incorporados (ícones, assets)
- ✅ Todas as dependências incluídas
- ✅ Threads funcionam corretamente no executável

## 🛠️ Dependências
- **flet**: Interface gráfica moderna
- **flask**: Servidor web backend
- **pystray**: Ícone da bandeja do sistema  
- **PIL/Pillow**: Processamento de imagens
- **qrcode**: Geração de QR codes
- **requests**: Cliente HTTP

## 📖 Exemplo de Integração

```python
import requests

# Enviar impressão para o aplicativo
response = requests.get('http://localhost:5000/imprimir', params={
    'created_date': '2025-01-01',
    'code': 'A123', 
    'services': 'Atendimento Geral',
    'header': 'Bem-vindo',
    'footer': 'Obrigado'
})

print(response.text)  # "Impressão realizada com sucesso"
```

## 🎛️ Configuração de Impressora

O aplicativo permite configurar qualquer impressora instalada no Windows:
1. Abra as Configurações (ícone ⚙️)
2. Selecione a impressora desejada
3. Clique em "Salvar"
4. A configuração é persistida automaticamente

## 🔍 Logs e Monitoramento

- **Logs Simples**: Interface amigável para usuários
- **Logs Avançados**: Detalhes técnicos para desenvolvedores
- **Toggle**: Alternar entre os modos de log
- **Status Badge**: Indicador visual do status do servidor

---

## 📞 Suporte

Este aplicativo foi desenvolvido para ser um sistema profissional de impressão de senhas, com todas as características de um aplicativo nativo do Windows.

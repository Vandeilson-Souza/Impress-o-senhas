# 📁 Assets / Recursos

Esta pasta contém os recursos visuais do aplicativo.

## 🖼️ Arquivos Necessários

### 1. **logo.png** (Recomendado)
- **Uso**: Logo exibido na interface principal do aplicativo
- **Dimensões recomendadas**: 200x200 pixels ou superior
- **Formato**: PNG com fundo transparente
- **Localização na interface**: Canto superior esquerdo, ao lado do título

### 2. **icon.ico** (Recomendado)
- **Uso**: Ícone do executável (.exe) no Windows
- **Dimensões**: Múltiplos tamanhos (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
- **Formato**: .ICO (ícone do Windows)
- **Como criar**: 
  - Use um conversor online: https://convertio.co/png-ico/
  - Ou use software como GIMP, Photoshop, IcoFX

## 📝 Como Adicionar os Arquivos

1. **Coloque seus arquivos nesta pasta** (`assets/`)
   ```
   assets/
   ├── logo.png    ← Sua logo aqui
   ├── icon.ico    ← Seu ícone aqui
   └── README.md
   ```

2. **Execute o aplicativo** para ver o logo na interface:
   ```powershell
   python flet_app.py
   ```

3. **Gere o executável** com o ícone personalizado:
   ```powershell
   pyinstaller build_exe.spec --clean --noconfirm
   ```

## 🎨 Dicas de Design

### Logo (logo.png)
- ✅ Fundo transparente
- ✅ Cores que contrastam bem com fundo branco
- ✅ Formato quadrado ou ligeiramente retangular
- ✅ Alta resolução (mínimo 200x200px)

### Ícone (icon.ico)
- ✅ Design simples e reconhecível em tamanhos pequenos
- ✅ Usar as mesmas cores da logo para consistência
- ✅ Testar em tamanhos 16x16 e 32x32 (mais usados)
- ✅ Incluir múltiplas resoluções no arquivo .ico

## 🔄 Comportamento Padrão

Se os arquivos não forem encontrados:
- **Sem logo.png**: Exibe um ícone de impressora padrão
- **Sem icon.ico**: PyInstaller usa ícone genérico do Python

## 📦 Ao Distribuir o Executável

Os arquivos desta pasta são **incluídos automaticamente** no executável gerado pelo PyInstaller. Não é necessário distribuí-los separadamente.

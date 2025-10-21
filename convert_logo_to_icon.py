"""
Converte logo.png para icon.ico
Certifique-se de que logo.png está na pasta assets/
"""

from PIL import Image
import os

def convert_logo_to_icon():
    """Converte logo.png para icon.ico com múltiplas resoluções"""
    
    logo_path = 'assets/logo.png'
    icon_path = 'assets/icon.ico'
    
    if not os.path.exists(logo_path):
        print('❌ Arquivo assets/logo.png não encontrado!')
        print('💡 Salve a logo primeiro na pasta assets/')
        return
    
    try:
        # Abre a logo
        img = Image.open(logo_path)
        
        # Remove fundo se necessário e converte para RGBA
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Tamanhos para o ícone .ico
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # Cria versões redimensionadas
        images = []
        for size in sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            images.append(resized)
        
        # Salva como .ico com múltiplas resoluções
        images[0].save(
            icon_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in images],
            append_images=images[1:]
        )
        
        print(f'✅ Ícone criado com sucesso: {icon_path}')
        print(f'📦 Tamanhos incluídos: {sizes}')
        
    except Exception as e:
        print(f'❌ Erro ao converter: {e}')


if __name__ == '__main__':
    print('🎨 Convertendo logo.png para icon.ico...\n')
    convert_logo_to_icon()

# 🔧 Comandos Git - Sistema de Impressão de Senhas

## 📋 Configuração Inicial do Git

### Primeira configuração (apenas uma vez)
```bash
# Configurar seu nome e email
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@exemplo.com"

# Verificar configuração
git config --list
```

## 🚀 Comandos Essenciais

### Clonar o Repositório
```bash
# Clone via HTTPS
git clone https://github.com/Vandeilson-Souza/Impress-o-senhas.git

# Clone via SSH (se configurado)
git clone git@github.com:Vandeilson-Souza/Impress-o-senhas.git

# Entre na pasta
cd Impress-o-senhas
```

### Workflow Básico
```bash
# 1. Verificar status
git status

# 2. Adicionar arquivos modificados
git add .                    # Todos os arquivos
git add flet_app.py         # Arquivo específico
git add *.py                # Todos arquivos Python

# 3. Fazer commit
git commit -m "Descrição das alterações"

# 4. Enviar para GitHub
git push origin main
```

## 📝 Comandos para Desenvolvimento

### Verificar Alterações
```bash
# Ver status dos arquivos
git status

# Ver diferenças dos arquivos modificados
git diff

# Ver diferenças de um arquivo específico
git diff flet_app.py

# Ver histórico de commits
git log --oneline
```

### Gerenciar Branches
```bash
# Ver todas as branches
git branch -a

# Criar nova branch
git checkout -b nova-feature

# Mudar de branch
git checkout main
git checkout nova-feature

# Merge de branch
git checkout main
git merge nova-feature

# Deletar branch local
git branch -d nova-feature
```

### Atualizar Repositório Local
```bash
# Baixar últimas alterações
git pull origin main

# Ou forçar atualização (cuidado!)
git fetch origin
git reset --hard origin/main
```

## 🔄 Comandos Específicos do Projeto

### Commit de Novas Funcionalidades
```bash
# Adicionar nova funcionalidade
git add .
git commit -m "feat: adicionar sistema de QR code automático"
git push origin main
```

### Commit de Correções
```bash
# Corrigir bug
git add .
git commit -m "fix: resolver problema de impressora não detectada"
git push origin main
```

### Commit de Documentação
```bash
# Atualizar documentação
git add README.md
git commit -m "docs: atualizar instruções de instalação"
git push origin main
```

### Commit de Configurações
```bash
# Atualizar configurações
git add requirements.txt build_exe.bat
git commit -m "config: atualizar dependências e script de build"
git push origin main
```

## 🛠️ Comandos Avançados

### Desfazer Alterações
```bash
# Desfazer alterações não commitadas
git checkout -- flet_app.py

# Desfazer último commit (mantém alterações)
git reset --soft HEAD~1

# Desfazer último commit (perde alterações)
git reset --hard HEAD~1
```

### Stash (Guardar alterações temporariamente)
```bash
# Guardar alterações atuais
git stash

# Ver lista de stashes
git stash list

# Aplicar último stash
git stash apply

# Aplicar e remover último stash
git stash pop
```

### Tags de Versão
```bash
# Criar tag de versão
git tag v1.0.0
git push origin v1.0.0

# Ver todas as tags
git tag -l

# Criar release no GitHub
git tag -a v1.0.0 -m "Versão 1.0.0 - Sistema completo"
git push origin v1.0.0
```

## 🔍 Comandos para Diagnóstico

### Verificar Configuração
```bash
# Ver configuração atual
git config --list

# Ver configuração específica
git config user.name
git config user.email

# Ver remote origin
git remote -v
```

### Verificar Histórico
```bash
# Histórico detalhado
git log

# Histórico resumido
git log --oneline

# Histórico de um arquivo
git log --follow flet_app.py

# Ver alterações de um commit
git show <hash_do_commit>
```

## 🚨 Comandos de Emergência

### Resolver Conflitos
```bash
# Quando há conflito no merge/pull
# 1. Editar arquivos conflitantes manualmente
# 2. Adicionar arquivos resolvidos
git add .
# 3. Finalizar merge
git commit -m "resolve: conflitos de merge resolvidos"
```

### Sincronizar Fork
```bash
# Adicionar repositório original como upstream
git remote add upstream https://github.com/original/repo.git

# Buscar alterações do upstream
git fetch upstream

# Merge com main local
git checkout main
git merge upstream/main
git push origin main
```

### Reset Completo (CUIDADO!)
```bash
# Resetar para último commit do GitHub
git fetch origin
git reset --hard origin/main

# ATENÇÃO: Isso apaga TODAS as alterações locais!
```

## 📋 Workflow Recomendado para Este Projeto

### Para Desenvolvimento Diário:
```bash
# 1. Sempre começar atualizando
git pull origin main

# 2. Fazer alterações nos arquivos

# 3. Testar o sistema
python flet_app.py

# 4. Adicionar e commitar
git add .
git commit -m "feat: melhorar detecção de status do servidor"

# 5. Enviar para GitHub
git push origin main
```

### Para Releases:
```bash
# 1. Testar compilação
build_exe.bat

# 2. Criar tag de versão
git tag v1.1.0 -m "Versão 1.1 - Melhorias na interface"

# 3. Push com tag
git push origin main --tags

# 4. Criar Release no GitHub via interface web
```

## 📂 Arquivos que DEVEM ser commitados:
- ✅ `flet_app.py` - Código principal
- ✅ `requirements.txt` - Dependências
- ✅ `build_exe.bat` - Script de build
- ✅ `README.md` - Documentação
- ✅ `assets/` - Recursos (ícones, logos)
- ✅ `.gitignore` - Configuração Git

## 🚫 Arquivos que NÃO devem ser commitados:
- ❌ `printer_config.json` - Configuração local
- ❌ `ticket/` - Imagens geradas
- ❌ `build/` - Arquivos temporários
- ❌ `dist/` - Arquivos de distribuição
- ❌ `venv/` - Ambiente virtual
- ❌ `__pycache__/` - Cache Python

## 💡 Dicas Importantes:

1. **Sempre** fazer `git pull` antes de começar a trabalhar
2. **Sempre** testar o código antes de fazer commit
3. **Usar** mensagens de commit descritivas
4. **Não** commitar arquivos de configuração local
5. **Fazer** backup antes de comandos destrutivos
6. **Usar** branches para features grandes
7. **Documentar** mudanças importantes no README

---

### 🎯 Links Úteis:
- **Repositório**: https://github.com/Vandeilson-Souza/Impress-o-senhas
- **Issues**: https://github.com/Vandeilson-Souza/Impress-o-senhas/issues
- **Releases**: https://github.com/Vandeilson-Souza/Impress-o-senhas/releases

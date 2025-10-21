# 📦 Instruções para Publicar no GitHub

## ✅ Preparação Concluída!

O repositório local está pronto com:
- ✓ Commits organizados
- ✓ Arquivos limpos
- ✓ .gitignore configurado
- ✓ Licença MIT
- ✓ README.md completo
- ✓ Documentação em português

---

## 🚀 Próximos Passos para Publicar

### 1. Criar Repositório no GitHub

1. Acesse https://github.com/new
2. Defina um nome: `ticket-printer-flet`
3. Descrição: `Sistema de impressão de senhas/tickets com interface gráfica Flet`
4. Deixe **VAZIO** (não inicialize com README, .gitignore ou licença)
5. Clique em "Create repository"

### 2. Conectar Repositório Local ao GitHub

Após criar no GitHub, execute os comandos:

```powershell
# Adicione o repositório remoto (substitua SEU_USUARIO)
git remote add origin https://github.com/SEU_USUARIO/ticket-printer-flet.git

# Verifique a conexão
git remote -v

# Envie os commits para o GitHub
git push -u origin main
```

### 3. Configurar Descrição e Topics (Opcional)

No GitHub, adicione:

**Descrição:**
```
🎫 Sistema completo para impressão de senhas/tickets com interface gráfica Flet e API REST Flask
```

**Topics (tags):**
- `flet`
- `flask`
- `python`
- `printer`
- `ticket-system`
- `qrcode`
- `pyinstaller`
- `windows`

---

## 📋 Comandos Úteis Git

```powershell
# Ver status
git status

# Ver histórico
git log --oneline

# Criar nova branch
git checkout -b feature/nova-funcionalidade

# Fazer commit
git add .
git commit -m "feat: Nova funcionalidade"

# Enviar para GitHub
git push origin main

# Atualizar do GitHub
git pull origin main
```

---

## 🔄 Para Futuras Atualizações

Depois de fazer mudanças no código:

```powershell
# 1. Adicionar arquivos modificados
git add .

# 2. Fazer commit com mensagem descritiva
git commit -m "feat: Descrição da mudança"

# 3. Enviar para o GitHub
git push origin main
```

---

## 📝 Padrões de Commit (Conventional Commits)

Use estes prefixos nas mensagens de commit:

- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `style:` - Formatação de código
- `refactor:` - Refatoração de código
- `perf:` - Melhoria de performance
- `test:` - Testes
- `chore:` - Tarefas de manutenção

**Exemplos:**
```
feat: Adiciona suporte para múltiplas impressoras
fix: Corrige erro na geração de QR Code
docs: Atualiza README com exemplos de API
perf: Otimiza cache de fontes
```

---

## 🎯 Repositório Está Pronto!

Tudo preparado para publicação. Basta seguir os passos acima! 🚀

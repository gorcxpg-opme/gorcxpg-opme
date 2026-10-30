# Como publicar o perfil

O GitHub mostra no topo do perfil o README de um repositório **público** com o mesmo nome da conta. Para a conta `gorcxpg-opme`, o repositório precisa se chamar exatamente `gorcxpg-opme`.

## 1. Criar o repositório (GitHub Desktop)

1. File → New repository. Nome: `gorcxpg-opme`. Local: `C:\Projetos`. Deixe "Initialize this repository with a README" **desmarcado**.
2. Copie para `C:\Projetos\gorcxpg-opme` tudo o que veio no zip (inclusive a pasta `.github`, que no Windows pode ficar oculta).
3. Commit to main → Publish repository. **Desmarque** "Keep this code private". O perfil só aparece se o repositório for público.

## 2. Ligar a atualização automática

1. No site do GitHub, abra o repositório → aba **Actions**. Se pedir, clique em "I understand my workflows, go ahead and enable them".
2. Clique em **Atualizar perfil** → **Run workflow**. Em um ou dois minutos ele cria a cobrinha e refaz as imagens.
3. Daqui em diante roda sozinho todo dia às 03:17 e sempre que você mudar algo em `dados/` ou no README.

Se a execução falhar com erro de permissão no `git push`: Settings → Actions → General → Workflow permissions → "Read and write permissions" → Save, e rode de novo.

## 3. Ajustar a lateral do perfil (github.com/gorcxpg-opme → Edit profile)

- **Name:** Gabriel Cunha (hoje aparece "gorc-supply").
- **Bio** (até 160 caracteres): `Supply Chain & Operations · dados aplicados a estoque e compras · construindo o Supply OPME`
- **Location:** Olinda, PE
- **Social accounts:** https://www.linkedin.com/in/gabriel-cunha-xp/
- **Foto:** a mesma do LinkedIn, para quem chegar por lá reconhecer na hora.
- No gráfico de contribuições, **Contribution settings → Private contributions** precisa estar marcado. É isso que faz os commits do `supply-opme` contarem para quem visita (e para a cobrinha) sem abrir o código.

## 4. Manter atualizado

| Quero mudar | Onde |
|---|---|
| Frases do terminal, cidade, status | `dados/perfil.json` → `frases`, `local`, `status` |
| Números do sistema e status dos módulos | `dados/perfil.json` → `projeto` |
| Fases do roadmap e data de lançamento | `dados/perfil.json` → `roadmap` |
| Ferramentas | `dados/perfil.json` → `stack` (4 grupos, até 6 itens cada) |
| Certificados | `dados/certificados.csv` (uma linha por curso) |
| Textos "Sobre mim" e "Supply OPME" | `README.md` |

Dá para editar direto no site do GitHub (ícone de lápis no arquivo → Commit changes). A ação roda sozinha logo depois.

### Colunas de `certificados.csv`

`instituicao, formacao, curso, area, horas, conclusao, link`

- `formacao`: deixe vazio para curso avulso; se o curso fizer parte de mais de uma formação, separe com `;`.
- `area`: se ficar vazia, o script adivinha pelo nome do curso. As áreas que já existem: BI & visualização, Engenharia de dados, Bancos de dados & SQL, Estatística & forecast, Python & data science, Excel & VBA, Gestão & agilidade, Supply chain & operações.
- `conclusao`: `dd/mm/aaaa`, `mm/aaaa` ou só o ano.
- `link`: link do certificado, se houver.
- Curso repetido em duas formações conta uma vez só nas horas e no total de cursos.

## 5. Testar no computador antes de enviar (opcional)

```
python scripts/gerar_perfil.py
```

Precisa de Python 3.9 ou mais novo, sem instalar nada. Abra os `.svg` de `assets/` no navegador para ver as animações.

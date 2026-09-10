# João Vitor Bomfim de Souza

Desenvolvedor full stack em Salvador, BA. Construo e opero os sistemas internos de uma
operação de delivery: a automação que fecha os relatórios de turno e o financeiro em workers
Celery separados por tipo, o BI que lê esse resultado, e o painel que monitora a
infraestrutura onde tudo roda — dois nós de aplicação atrás de um load balancer nginx e uma
VM de estado com PostgreSQL, Redis e MinIO. Escrevo o deploy e sou eu quem atende quando ele
quebra.

### Projetos

**[dock_keeper](https://github.com/jvS0uzx/dock_keeper)** — Painel que monitora VPS,
containers Docker e validade de certificado TLS, com log de container em streaming por SSE.
São 19.909 linhas de Go, 9.060 delas em teste (46%), 292 funções de teste sobre 10 pacotes
internos; o CI sobe um PostgreSQL 15 como serviço e roda `go test -race`, porque metade da
suíte depende de banco e teste que se pula sozinho é o que deixa uma regressão de permissão
passar. Oito ADRs registram o que só aparece em sistema que roda — por que a API responde 404
em vez de 403, por que a chave primária é o SHA-256 do token e nunca o token. Um passo do CI
injeta um valor-canário em `VITE_API_TOKEN` e falha se ele aparecer no build: o token de
administrador global já foi embutido no bundle de produção e viajou para todo navegador que
abriu o painel.

**[dockkeeper_collector](https://github.com/jvS0uzx/dockkeeper_collector)** — Agente que
inventaria a rede local de cada unidade e faz push para o painel central, porque pacote de
descoberta não atravessa a internet: painel na matriz é cego para a LAN da filial. São 1.378
linhas de Go, 543 em teste (39%), zero dependência fora da biblioteca padrão. No primeiro
boot ele troca um convite de uso único por credencial própria de dispositivo e queima o
convite; o painel guarda só o SHA-256 do segredo, então credencial perdida se resolve com
convite novo, não com releitura. Varre por TCP connect para rodar sem root, recusa faixa não
privada ou maior que /16, e não envia inventário vazio quando todas as faixas falharam —
apagar o último estado bom é pior que não atualizar.

**[Larify](https://github.com/jvS0uzx/Larify)** — Bot de Telegram que responde o que o
Spotify não responde: quais das suas músicas curtidas não estão em nenhuma playlist. São
1.177 linhas de Python, 297 delas em teste, com OAuth por Authorization Code + PKCE e long
polling — só tráfego de saída, sem porta aberta, sem domínio, sem webhook. A definição de
órfã exclui de propósito a playlist que você apenas segue: contá-la esconderia justamente a
música que precisa ser arrumada. Nasceu de um pedido da minha esposa.

### Stack

- Go — `net/http`, goroutines, SSE, GORM sobre PostgreSQL, `x/crypto/ssh`
- Python — Django, Celery, pandas
- TypeScript — React, Vite, vitest
- Infraestrutura — Docker Compose, nginx, PostgreSQL, Redis, MinIO, Tailscale, systemd, GitHub Actions

### Contato

- joaovitordevv.py@gmail.com
- [linkedin.com/in/joãovitorbsouza](https://www.linkedin.com/in/joãovitorbsouza)

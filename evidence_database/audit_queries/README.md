# Evidências de Auditoria SQL

Esta pasta contém os resultados das consultas de auditoria exigidas no desafio, junto com o output do `EXPLAIN` de cada query.

## Interpretação dos planos

### 1. Lag médio SMS por gateway

O plano utiliza índice composto em `distribution_status(channel, status, delivered_at)` para filtrar registros SMS entregues no período. Os joins com `orders` e `lead_events` utilizam chaves primárias/FKs.

### 2. Leads pending há mais de 5 minutos

A consulta utiliza o índice `idx_distribution_status_created(status, created_at)`, permitindo buscar rapidamente registros pendentes mais antigos que 5 minutos.

### 3. Taxa de sucesso SMS por produto/hora

O plano utiliza índice em `distribution_status(channel, status, delivered_at)` para filtrar registros SMS no período. A etapa de agrupamento por produto/hora pode gerar `Using temporary` ou `Using filesort`, comportamento esperado para relatório analítico.

### 4. DLQ por motivo

A consulta agrupa registros de `lead_dead_letter` por origem e erro. Em datasets pequenos, o MySQL pode optar por `type = ALL`, pois é mais barato varrer poucas linhas do que utilizar índice.

### 5. Reconciliação approved x SMS delivered

A consulta compara eventos aprovados em `lead_events` com registros SMS delivered em `distribution_status`. Os joins utilizam `order_id`, garantindo consistência entre aprovação e distribuição.

## Observação

Mesmo quando o MySQL opta por `type = ALL` em alguma query, isso não necessariamente indica problema. Em tabelas pequenas, o otimizador pode decidir que um full scan é mais barato que usar índice. O ponto principal é que todas as queries executaram abaixo de 1 segundo no dataset fornecido.
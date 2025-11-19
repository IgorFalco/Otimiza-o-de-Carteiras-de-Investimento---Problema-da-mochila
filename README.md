# Sistema de Otimização de Carteiras - B3

Sistema de otimização de portfólios baseado no modelo de mochila usando programação linear inteira mista (MILP) com Gurobi, implementando restrições linearizadas de risco e retorno como médias ponderadas.

## 📋 Descrição

Este sistema processa dados históricos de cotações da B3 (COTAHIST) e otimiza carteiras de investimento usando MILP com o solver Gurobi 12.0.0. O modelo lineariza as restrições de risco e retorno como médias ponderadas, implementa diversificação setorial com variáveis binárias, e permite exclusão de ativos com retorno negativo.

### Características:

- **Processamento de dados**: Leitura e análise de arquivos COTAHIST da B3
- **Filtragem de liquidez**: Seleção de ativos líquidos (≥200 dias, ≥R$1M volume médio)
- **Otimização MILP**: Modelo linearizado com restrições de risco/retorno como médias ponderadas
- **Diversificação setorial**: Variáveis binárias z_setor para garantir número mínimo de setores
- **Exclusão de retornos negativos**: Opção de excluir automaticamente ativos com retorno < 0
- **Análise completa**: Visualizações gráficas, relatórios e exportação para Excel
- **Três cenários**: Conservador (30.49% retorno), Moderado (65.46%), Agressivo (104.60%)

## 🚀 Instalação

### Pré-requisitos

1. **Python 3.10+** instalado
2. **Gurobi 12.0.0** instalado com licença válida
   - Download: https://www.gurobi.com/downloads/
   - Licença acadêmica gratuita: https://www.gurobi.com/academia/academic-program-and-licenses/
   - **Importante**: O projeto usa `gurobipy==12.0.0` (compatível com licença acadêmica)

### Passos de Instalação

1. **Clone ou baixe o projeto**

2. **Crie e ative ambiente virtual**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate.bat
   ```

3. **Instale as dependências**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure a licença do Gurobi**:
   - Obtenha sua licença acadêmica em https://www.gurobi.com/academia/
   - Salve o arquivo `gurobi.lic` em `C:\Users\<seu_usuario>\gurobi.lic`
   - Ou configure a variável: `set GRB_LICENSE_FILE=C:\caminho\para\gurobi.lic`

5. **Baixe os dados históricos da B3**:
   - Acesse: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/
   - Baixe o arquivo COTAHIST anual (exemplo: 2024)
   - Extraia o arquivo `COTAHIST_A2024.TXT` do ZIP
   - Coloque o arquivo na pasta `data/`
   - **Instruções detalhadas**: Veja `data/README.md`

## 📊 Uso

### Execução via Batch Script (Recomendado)

```powershell
.\run.bat
```

### Execução Manual

```powershell
.venv\Scripts\activate.bat
python main.py
```

### Menu Interativo

O sistema apresenta um menu com as seguintes opções:

1. **Processar dados históricos** - Lê e processa o arquivo COTAHIST
2. **Otimizar carteira** - Executa otimização (requer dados processados)
3. **Pipeline completo** - Processa + Otimiza + Analisa (tudo de uma vez)
4. **Analisar carteira existente** - Re-analisa carteira já otimizada
0. **Sair**

### Cenários de Investimento

Ao otimizar, escolha um dos três cenários:

- **Conservador**: Risco ≤25%, retorno ≥8%, 10-20 ativos, máx 25% por setor, mín 4 setores, exclui retornos negativos
  - *Resultado real*: 11 ativos, 30.49% retorno, 25% risco, Sharpe 1.22, 5 setores
  
- **Moderado**: Risco ≤35%, retorno ≥12%, 5-15 ativos, máx 35% por setor, mín 3 setores
  - *Resultado real*: 5 ativos, 65.46% retorno, 35% risco, Sharpe 1.87, 5 setores
  
- **Agressivo**: Risco ≤50%, retorno ≥18%, 3-10 ativos, máx 60% por ativo, mín 2 setores, alta concentração
  - *Resultado real*: 6 ativos, 104.60% retorno, 50% risco, Sharpe 2.09, 5 setores

## 📈 Modelo Matemático

O sistema implementa um modelo de otimização de portfólio tipo mochila com restrições linearizadas:

**Função Objetivo**: Maximizar Σ (μᵢ × pᵢ × yᵢ) (retorno total esperado)

**Restrições Linearizadas** (risco e retorno como médias ponderadas):
- **Orçamento**: Σ (pᵢ × yᵢ) ≤ B (investimento total limitado)
- **Risco**: Σ (σᵢ × pᵢ × yᵢ) - R × Σ (pᵢ × yᵢ) ≤ 0 (média ponderada ≤ R)
- **Retorno mínimo**: Σ (μᵢ × pᵢ × yᵢ) - T × Σ (pᵢ × yᵢ) ≥ 0 (média ponderada ≥ T)
- **Quantidade de ativos**: Lmin ≤ Σ xᵢ ≤ Lmax
- **Limite por setor**: Σ (pᵢ × yᵢ) para i∈setor s ≤ αmax × B
- **Limite por ativo**: pᵢ × yᵢ ≤ β × B
- **Rastreamento de setores**: Σ (pᵢ × yᵢ) setor s ≤ B × z_setor[s] (vincula uso do setor)
- **Mínimo de setores**: Σ z_setor[s] ≥ num_setores_min
- **Exclusão de negativos**: xᵢ = 0 se μᵢ < 0 (quando `excluir_retorno_negativo=True`)
- **Relação seleção/alocação**: yᵢ ≤ ymax × xᵢ (força yᵢ=0 se xᵢ=0)

**Variáveis**:
- xᵢ ∈ {0, 1}: binária de seleção do ativo i
- yᵢ ∈ ℤ⁺: quantidade inteira (lotes de 100 ações) do ativo i
- z_setor[s] ∈ {0, 1}: binária indicando se o setor s é usado

## 📦 Dependências

- `pandas`: Manipulação de dados (leitura COTAHIST, DataFrames)
- `numpy`: Cálculos numéricos (retorno, desvio padrão, Sharpe)
- `gurobipy==12.0.0`: Solver MILP de otimização (compatível com licença acadêmica)
- `matplotlib`: Visualização de gráficos (barras, scatter, pizza)
- `seaborn`: Gráficos estatísticos (paleta de cores)
- `openpyxl`: Exportação para Excel (análise completa)

**Instalação**: `pip install -r requirements.txt`

## 🔧 Configuração

Edite `src/config.py` para ajustar parâmetros:

```python
# Filtragem de liquidez
MIN_DIAS_NEGOCIACAO = 200      # mínimo 200 dias negociados no ano
MIN_VOLUME_MEDIO = 1_000_000   # volume médio ≥ R$1 milhão
DIAS_ANUALIZACAO = 252         # dias úteis para anualização

# Solver Gurobi
TIME_LIMIT = 600               # limite de 600 segundos
MIP_GAP = 0.0                  # buscar solução ótima (0% de gap)

# Cenários (exemplo: CENARIO_CONSERVADOR)
CENARIO_CONSERVADOR = {
    'orcamento': 100_000.0,
    'risco_maximo': 0.25,               # 25% de desvio-padrão médio ponderado
    'retorno_minimo': 0.08,             # 8% de retorno mínimo
    'num_ativos_min': 10,
    'num_ativos_max': 20,
    'alpha_setor_max': 0.25,            # máx 25% em qualquer setor
    'num_setores_min': 4,               # mínimo 4 setores diferentes
    'max_ativo_pct': 0.20,              # máx 20% por ativo individual
    'excluir_retorno_negativo': True,   # não investir em ativos com retorno < 0
}
```

## 📄 Arquivos de Saída

### 1. `output/metricas_ativos.csv` (compartilhado)
Métricas calculadas para todos os 215 ativos líquidos do COTAHIST:
- Ticker, nome da empresa, setor
- Retorno esperado anualizado (252 dias úteis)
- Desvio padrão (risco)
- Sharpe Ratio
- Estatísticas de negociação (dias, volume médio, preço médio)

### 2. `output/{cenario}/carteira_otimizada.csv`
Carteira selecionada pelo otimizador para cada cenário:
- Ativos escolhidos (com seleção binária xᵢ)
- Quantidade de lotes (yᵢ) e investimento em reais
- Pesos percentuais
- Métricas individuais (retorno, risco, Sharpe)

### 3. `output/{cenario}/resultados_carteira.png`
Gráficos com 4 painéis:
- Distribuição de investimento por ativo (barras)
- Composição setorial (pizza)
- Dispersão risco-retorno (scatter plot)
- Sharpe ratio por ativo (barras horizontais)

### 4. `output/{cenario}/relatorio_otimizacao.txt`
Relatório completo em texto:
- Métricas gerais: retorno, risco, Sharpe, investimento total
- Distribuição setorial: número de ativos, valor e percentual por setor
- Lista detalhada de ativos: ticker, empresa, setor, investimento, % alocação
- Tempo de otimização e gap de otimalidade (0.00% = solução ótima)

### 5. `output/{cenario}/analise_completa.xlsx`
Planilha Excel com 3 abas:
- **Carteira**: Dados completos dos ativos selecionados com métricas
- **Setores**: Agregação por setor (valor, peso, número de ativos)
- **Métricas**: Indicadores gerais da carteira (retorno, risco, Sharpe)

## ⚠️ Troubleshooting

### Erro de licença do Gurobi
```
GurobiError: No Gurobi license found
```
**Solução**: Configure `GRB_LICENSE_FILE` ou coloque `gurobi.lic` em `C:\Users\<usuario>\`

### Versão incompatível do Gurobi
```
GurobiError: Current version is X.X.X but license is for Y.Y.Y
```
**Solução**: Este projeto usa `gurobipy==12.0.0` (compatível com licença acadêmica). Reinstale:
```powershell
pip uninstall gurobipy
pip install gurobipy==12.0.0
```
**Nota**: Se sua licença for para versão diferente (ex: 11.x ou 13.x), ajuste o `requirements.txt`

## 📚 Referências

- **Modelo Base**: Problema da Mochila (Knapsack Problem) com restrições de risco e retorno
- **Linearização**: Restrições de risco e retorno implementadas como médias ponderadas
- **Diversificação**: Variáveis binárias z_setor para rastreamento de setores usados
- **Dados**: B3 - Brasil, Bolsa, Balcão (https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)
- **Solver**: Gurobi Optimization 12.0.0 (https://www.gurobi.com)
- **Repositório**: https://github.com/IgorFalco/Otimiza-o-de-Carteiras-de-Investimento---Problema-da-mochila

## 📝 Licença

Este projeto é para fins acadêmicos e de pesquisa.

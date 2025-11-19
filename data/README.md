# Dados de Entrada

Este diretório deve conter os arquivos de cotações históricas da B3.

## Como obter o arquivo COTAHIST

### 1. Acesse o site da B3
Vá para: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/

### 2. Baixe o arquivo anual
- Clique na aba **"Ações"** ou **"Séries Históricas"**
- Selecione o ano desejado (exemplo: **2024**)
- Baixe o arquivo compactado (ZIP)

### 3. Extraia o arquivo
- Descompacte o arquivo ZIP baixado
- Você encontrará um arquivo no formato: `COTAHIST_A2024.TXT`
- Coloque esse arquivo neste diretório (`data/`)

### 4. Estrutura esperada
```
data/
├── COTAHIST_A2024.TXT    ← Arquivo de cotações históricas
├── setores.csv            ← Mapeamento de setores (já incluído)
└── README.md              ← Este arquivo
```

## Formato do arquivo COTAHIST

O arquivo COTAHIST é um arquivo de texto com layout de largura fixa contendo:
- Cotações diárias de todos os ativos negociados na B3
- Volumes financeiros e quantidades negociadas
- Preços de abertura, fechamento, máximo e mínimo
- Dados de ajuste de proventos (dividendos, splits, etc.)

**Importante**: O sistema processa automaticamente o formato COTAHIST da B3, não é necessário modificar o arquivo.

## Filtragem de liquidez

O sistema aplica os seguintes filtros automaticamente:
- **Dias de negociação**: Mínimo 200 dias no ano (≈80% dos dias úteis)
- **Volume médio**: Mínimo R$ 1.000.000,00 por dia
- **Tipo de ativo**: Apenas ações ordinárias (ON) e preferenciais (PN)

Após a filtragem, o sistema gera o arquivo `output/metricas_ativos.csv` com as métricas calculadas (retorno, risco, Sharpe) para os ativos líquidos.

## Outros anos

Para usar dados de outros anos:
1. Baixe o arquivo COTAHIST do ano desejado
2. Coloque o arquivo neste diretório
3. Atualize a variável `ARQUIVO_COTAHIST` no arquivo `src/config.py`:
   ```python
   ARQUIVO_COTAHIST = "data/COTAHIST_A2023.TXT"  # exemplo para 2023
   ```

## Troubleshooting

### Arquivo não encontrado
```
❌ Arquivo não encontrado: data/COTAHIST_A2024.TXT
```
**Solução**: Baixe o arquivo COTAHIST seguindo as instruções acima.

### Erro de codificação
```
UnicodeDecodeError: 'utf-8' codec can't decode byte...
```
**Solução**: O arquivo COTAHIST usa codificação `latin-1` (ISO-8859-1). O sistema já está configurado para tratar isso automaticamente. Se o erro persistir, verifique se o arquivo não foi modificado.

### Arquivo vazio ou corrompido
```
ValueError: No columns to parse from file
```
**Solução**: O arquivo pode estar corrompido. Baixe novamente da B3.

## Mais informações

- **Layout COTAHIST**: http://www.b3.com.br/data/files/33/67/B9/50/D84057102C784E47AC094EA8/SeriesHistoricas_Layout.pdf
- **Documentação B3**: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/
- **Suporte**: Em caso de dúvidas, consulte a documentação oficial da B3

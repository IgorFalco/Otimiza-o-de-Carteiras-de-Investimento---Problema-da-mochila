"""
Configurações do sistema de otimização de carteiras.
"""

# Processamento de dados
ARQUIVO_COTAHIST = "data/COTAHIST_A2024.TXT"
MIN_DIAS_NEGOCIACAO = 200
MIN_VOLUME_MEDIO = 1_000_000
DIAS_ANUALIZACAO = 252

# Diretórios de saída
ARQUIVO_METRICAS_CSV = "output/metricas_ativos.csv"

# Solver Gurobi
TIME_LIMIT = 600
MIP_GAP = 0.0

# Visualização
TOP_N_ATIVOS = 20


CENARIO_CONSERVADOR = {
    'orcamento': 100_000.0,
    'risco_maximo': 0.25,        # 25% de desvio-padrão médio ponderado (conservador)
    'retorno_minimo': 0.08,      # 8% de retorno mínimo
    'num_ativos_min': 10,
    'num_ativos_max': 20,
    'diversificacao_setor': True,
    'alpha_setor_min': 0.0,      # Sem mínimo obrigatório por setor
    'alpha_setor_max': 0.25,     # Máximo 25% em qualquer setor
    'num_setores_min': 4,        # Pelo menos 4 setores diferentes
    'max_ativo_pct': 0.20,       # Máximo 20% do orçamento em um único ativo
    'excluir_retorno_negativo': True,  # Não investir em ativos com retorno negativo
}

CENARIO_MODERADO = {
    'orcamento': 100_000.0,
    'risco_maximo': 0.35,        # 35% de desvio-padrão médio ponderado (moderado)
    'retorno_minimo': 0.12,      # 12% de retorno mínimo
    'num_ativos_min': 5,
    'num_ativos_max': 15,
    'diversificacao_setor': True,
    'alpha_setor_min': 0.0,
    'alpha_setor_max': 0.35,     # Máximo 35% em qualquer setor
    'num_setores_min': 3,        # Pelo menos 3 setores diferentes
    'max_ativo_pct': 0.40,       # Máximo 40% do orçamento em um único ativo
}

CENARIO_AGRESSIVO = {
    'orcamento': 100_000.0,
    'risco_maximo': 0.50,        # 50% de desvio-padrão médio ponderado (agressivo)
    'retorno_minimo': 0.18,      # 18% de retorno mínimo
    'num_ativos_min': 3,
    'num_ativos_max': 10,
    'diversificacao_setor': True,
    'alpha_setor_min': 0.0,
    'alpha_setor_max': 1.0,      # Sem limite por setor (pode concentrar)
    'num_setores_min': 2,        # Pelo menos 2 setores diferentes
    'max_ativo_pct': 0.60,       # Máximo 60% do orçamento em um único ativo
}


def obter_config(cenario='moderado'):
    """Retorna configuração do cenário escolhido."""
    cenarios = {
        'conservador': CENARIO_CONSERVADOR,
        'moderado': CENARIO_MODERADO,
        'agressivo': CENARIO_AGRESSIVO,
    }
    
    config = cenarios.get(cenario.lower(), CENARIO_MODERADO).copy()
    config.update({
        'time_limit': TIME_LIMIT,
        'mip_gap': MIP_GAP,
        'top_n_ativos': TOP_N_ATIVOS,
        'cenario_nome': cenario.lower(),
    })
    
    return config


def obter_diretorios_cenario(cenario='moderado'):
    """Retorna caminhos de arquivos para o cenário específico."""
    import os
    
    cenario_dir = f"output/{cenario.lower()}/"
    os.makedirs(cenario_dir, exist_ok=True)
    
    return {
        'dir': cenario_dir,
        'carteira_csv': f"{cenario_dir}carteira_otimizada.csv",
        'relatorio_txt': f"{cenario_dir}relatorio_otimizacao.txt",
        'grafico_png': f"{cenario_dir}resultados_carteira.png",
        'analise_xlsx': f"{cenario_dir}analise_completa.xlsx",
    }

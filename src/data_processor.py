"""
Processador de dados históricos da B3 (COTAHIST).
"""

import pandas as pd
import numpy as np


class CotacaoProcessor:
    """Processa cotações históricas e calcula métricas para otimização."""
    
    def __init__(self, arquivo_cotahist):
        self.arquivo_cotahist = arquivo_cotahist
        self.df_completo = None
        self.df_acoes = None
        self.df_retornos = None
        self.metricas = None
        
    def processar_cotahist(self):
        """Lê e processa arquivo COTAHIST da B3."""
        colunas_spec = [
            ('tipo_registro', 0, 2), ('data_pregao', 2, 10), ('cod_bdi', 10, 12),
            ('ticker', 12, 24), ('tipo_mercado', 24, 27), ('nome_empresa', 27, 39),
            ('especificacao', 39, 49), ('prazo_dias', 49, 52), ('moeda', 52, 56),
            ('preco_abertura', 56, 69), ('preco_maximo', 69, 82), ('preco_minimo', 82, 95),
            ('preco_medio', 95, 108), ('preco_ultimo', 108, 121),
            ('preco_melhor_compra', 121, 134), ('preco_melhor_venda', 134, 147),
            ('total_negocios', 147, 152), ('quantidade_negociada', 152, 170),
            ('volume_total', 170, 188), ('preco_exercicio', 188, 201),
            ('indicador_correcao', 201, 202), ('data_vencimento', 202, 210),
            ('fator_cotacao', 210, 217), ('preco_exercicio_pontos', 217, 230),
            ('isin', 230, 242), ('distribuicao', 242, 245)
        ]
        
        dados = []
        print(f"Processando arquivo {self.arquivo_cotahist}...")
        
        with open(self.arquivo_cotahist, 'r', encoding='latin1') as f:
            for linha_num, linha in enumerate(f, 1):
                if linha.startswith('00') or linha.startswith('99'):
                    continue
                
                if linha.startswith('01'):
                    registro = {nome: linha[inicio:fim].strip() 
                               for nome, inicio, fim in colunas_spec}
                    dados.append(registro)
                
                if linha_num % 100000 == 0:
                    print(f"  {linha_num:,} linhas processadas...")
        
        print(f"Total: {len(dados):,} registros")
        
        df = pd.DataFrame(dados)
        df['data_pregao'] = pd.to_datetime(df['data_pregao'], format='%Y%m%d')
        
        campos_preco = ['preco_abertura', 'preco_maximo', 'preco_minimo', 
                       'preco_medio', 'preco_ultimo']
        for campo in campos_preco:
            df[campo] = pd.to_numeric(df[campo], errors='coerce') / 100
        
        df['volume_total'] = pd.to_numeric(df['volume_total'], errors='coerce') / 100
        df['quantidade_negociada'] = pd.to_numeric(df['quantidade_negociada'], errors='coerce')
        df['total_negocios'] = pd.to_numeric(df['total_negocios'], errors='coerce')
        df['ticker'] = df['ticker'].str.strip()
        df['nome_empresa'] = df['nome_empresa'].str.strip()
        df = df.sort_values(['data_pregao', 'ticker'])
        
        self.df_completo = df
        return df
    
    def filtrar_acoes_principais(self, min_dias_negociacao=200, min_volume_medio=1000000):
        """Filtra ações com liquidez mínima."""
        df_acoes = self.df_completo[self.df_completo['cod_bdi'] == '02'].copy()
        df_acoes = df_acoes[df_acoes['ticker'].str.match(r'^[A-Z]{4}(3|4|5|6|11)$')]
        
        liquidez = df_acoes.groupby('ticker').agg({
            'data_pregao': 'count',
            'volume_total': 'mean',
            'total_negocios': 'mean'
        }).rename(columns={
            'data_pregao': 'dias_negociacao',
            'volume_total': 'volume_medio',
            'total_negocios': 'negocios_medio'
        })
        
        ativos_liquidos = liquidez[
            (liquidez['dias_negociacao'] >= min_dias_negociacao) &
            (liquidez['volume_medio'] >= min_volume_medio)
        ].index
        
        df_acoes = df_acoes[df_acoes['ticker'].isin(ativos_liquidos)]
        
        print(f"\nAções filtradas: {df_acoes['ticker'].nunique()} ativos únicos")
        print(f"Critérios: ≥{min_dias_negociacao} dias, volume ≥R$ {min_volume_medio:,.0f}")
        
        self.df_acoes = df_acoes
        return df_acoes
    
    def calcular_retornos(self):
        """Calcula retornos logarítmicos diários."""
        print("\nCalculando retornos...")
        
        df_precos = self.df_acoes.pivot(
            index='data_pregao',
            columns='ticker',
            values='preco_ultimo'
        )
        
        df_retornos = np.log(df_precos / df_precos.shift(1))
        df_retornos = df_retornos.dropna(how='all')
        
        self.df_retornos = df_retornos
        print(f"Retornos: {df_retornos.shape[0]} dias × {df_retornos.shape[1]} ativos")
        
        return df_retornos
    
    def calcular_metricas(self, dias_anualizacao=252):
        """Calcula métricas de risco-retorno para cada ativo."""
        print("\nCalculando métricas...")
        
        metricas = pd.DataFrame(index=self.df_retornos.columns)
        metricas['retorno_esperado'] = self.df_retornos.mean() * dias_anualizacao
        metricas['desvio_padrao'] = self.df_retornos.std() * np.sqrt(dias_anualizacao)
        metricas['sharpe_ratio'] = metricas['retorno_esperado'] / metricas['desvio_padrao']
        metricas['preco_atual'] = self.df_acoes.groupby('ticker')['preco_ultimo'].last()
        metricas['volume_medio'] = self.df_acoes.groupby('ticker')['volume_total'].mean()
        metricas['nome_empresa'] = self.df_acoes.groupby('ticker')['nome_empresa'].first()
        metricas = metricas.dropna()
        
        self.metricas = metricas
        print(f"Métricas calculadas: {len(metricas)} ativos")
        
        return metricas
    
    def classificar_setores(self):
        """Classifica ativos por setor usando arquivo setores.csv."""
        import os
        
        arquivo_setores = 'data/setores.csv'
        
        # Carregar mapeamento de setores do CSV
        df_setores = pd.read_csv(arquivo_setores, header=None, names=['setor', 'prefixo'])
        
        # Criar dicionário prefixo -> setor
        mapa_setores = {}
        for _, row in df_setores.iterrows():
            prefixo = row['prefixo'].strip()
            setor = row['setor'].strip()
            mapa_setores[prefixo] = setor
        
        # Classificar cada ativo
        def obter_setor(ticker):
            # Tentar buscar com ticker completo primeiro (para casos como EMBR3, BRFS3)
            if ticker in mapa_setores:
                return mapa_setores[ticker]
            # Se não encontrar, tentar com os 4 primeiros caracteres (padrão)
            prefixo = ticker[:4]
            return mapa_setores.get(prefixo, 'Outros')
        
        self.metricas['setor'] = self.metricas.index.map(obter_setor)
        
        print(f"\nDistribuição por setor:")
        dist = self.metricas['setor'].value_counts()
        for setor, count in dist.items():
            print(f"  {setor:<40} {count:>3} ativos")
        
        return self.metricas
    
    def salvar_metricas(self, arquivo=None):
        """Salva métricas em arquivo CSV."""
        if arquivo is None:
            from . import config
            arquivo = config.ARQUIVO_METRICAS_CSV
        
        if self.metricas is not None:
            self.metricas.to_csv(arquivo, encoding='utf-8-sig')
            print(f"\nMétricas salvas: {arquivo}")
    
    def executar_pipeline_completo(self, min_dias=200, min_volume=1000000):
        """Executa todo o pipeline de processamento."""
        print("="*60)
        print("PROCESSAMENTO DE DADOS")
        print("="*60)
        
        self.processar_cotahist()
        self.filtrar_acoes_principais(min_dias, min_volume)
        self.calcular_retornos()
        self.calcular_metricas()
        self.classificar_setores()
        self.salvar_metricas()
        
        print("\n" + "="*60)
        print("PROCESSAMENTO CONCLUÍDO")
        print("="*60)
        
        return self.metricas

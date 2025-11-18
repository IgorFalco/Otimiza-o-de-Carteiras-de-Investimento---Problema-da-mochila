import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_processor import CotacaoProcessor
from src.optimizer import PortfolioOptimizer
from src.results_analyzer import ResultsAnalyzer
from src import config


def exibir_banner():
    """Banner do sistema."""
    print("\n" + "="*80)
    print(" "*20 + "OTIMIZAÇÃO DE CARTEIRAS - B3")
    print(" "*25 + "Modelo de Mochila Robusto")
    print("="*80 + "\n")


def menu_principal():
    """Menu principal do sistema."""
    print("\n" + "─"*80)
    print("MENU PRINCIPAL")
    print("─"*80)
    print("1. Processar dados históricos (COTAHIST)")
    print("2. Otimizar carteira")
    print("3. Pipeline completo (processar + otimizar + analisar)")
    print("4. Analisar carteira existente")
    print("0. Sair")
    print("─"*80)
    
    return input("\nOpção: ").strip()


def processar_dados():
    """Processa dados históricos."""
    print("\n" + "="*80)
    print("PROCESSAMENTO DE DADOS")
    print("="*80)
    
    arquivo = config.ARQUIVO_COTAHIST
    if not os.path.exists(arquivo):
        print(f"\nArquivo não encontrado: {arquivo}")
        print("   Coloque o arquivo COTAHIST na pasta 'data/'")
        return None
    
    processor = CotacaoProcessor(arquivo)
    metricas = processor.executar_pipeline_completo(
        min_dias=config.MIN_DIAS_NEGOCIACAO,
        min_volume=config.MIN_VOLUME_MEDIO
    )
    
    print("\nProcessamento concluído")
    return metricas


def otimizar_carteira(metricas=None, cenario='moderado'):
    """Otimiza carteira."""
    print("\n" + "="*80)
    print("OTIMIZAÇÃO DE CARTEIRA")
    print("="*80)
    
    if metricas is None:
        arquivo_metricas = config.ARQUIVO_METRICAS_CSV
        if not os.path.exists(arquivo_metricas):
            print(f"\nMétricas não encontradas: {arquivo_metricas}")
            print("   Execute primeiro a opção 1 (Processar dados)")
            return None
        
        print(f"\nCarregando métricas: {arquivo_metricas}")
        import pandas as pd
        metricas = pd.read_csv(arquivo_metricas, index_col=0)
        print(f"{len(metricas)} ativos carregados")
    
    cfg = config.obter_config(cenario)
    
    print(f"\nCenário: {cenario.upper()}")
    print(f"  Orçamento: R$ {cfg['orcamento']:,.2f}")
    print(f"  Risco máximo: {cfg['risco_maximo']:.2f}")
    print(f"  Retorno mínimo: {cfg['retorno_minimo']:.1%}")
    print(f"  Ativos: [{cfg['num_ativos_min']}, {cfg['num_ativos_max']}]")
    
    try:
        optimizer = PortfolioOptimizer(metricas, cfg)
        solucao = optimizer.executar_otimizacao_completa()
        
        if solucao is None:
            print("\nOtimização falhou")
            return None
        
        print("\nOtimização concluída")
        return solucao, metricas
    
    except Exception as e:
        print(f"\nErro: {str(e)}")
        return None


def analisar_resultados(solucao=None, metricas=None, cenario='moderado'):
    """Analisa e visualiza resultados."""
    print("\n" + "="*80)
    print("ANÁLISE DE RESULTADOS")
    print("="*80)
    
    import pandas as pd
    
    if solucao is None:
        from src import config
        dirs = config.obter_diretorios_cenario(cenario)
        arquivo_carteira = dirs['carteira_csv']
        if not os.path.exists(arquivo_carteira):
            print(f"\nCarteira não encontrada: {arquivo_carteira}")
            return
        
        print(f"\nCarregando carteira: {arquivo_carteira}")
        carteira_df = pd.read_csv(arquivo_carteira)
        
        solucao = {
            'carteira': carteira_df,
            'num_ativos': len(carteira_df),
            'retorno_total': carteira_df['retorno_esperado'].mean() if 'retorno_esperado' in carteira_df else 0,
            'risco_total': carteira_df['desvio_padrao'].sum() if 'desvio_padrao' in carteira_df else 0,
            'sharpe_carteira': 0.5,
            'investimento_total': carteira_df['investimento'].sum() if 'investimento' in carteira_df else 0,
            'gap': 0.0,
            'tempo_exec': 0.0
        }
    
    if metricas is None:
        arquivo_metricas = config.ARQUIVO_METRICAS_CSV
        if os.path.exists(arquivo_metricas):
            metricas = pd.read_csv(arquivo_metricas, index_col=0)
        else:
            metricas = solucao['carteira'].set_index('ticker')
    
    analyzer = ResultsAnalyzer(solucao, metricas)
    analyzer.imprimir_resumo()
    
    try:
        analyzer.gerar_graficos(cenario=cenario)
    except Exception as e:
        print(f"\nErro ao gerar gráficos: {str(e)}")
    
    analyzer.exportar_relatorio(cenario=cenario)
    
    try:
        analyzer.salvar_excel(cenario=cenario)
    except Exception as e:
        print(f"\nErro ao salvar Excel: {str(e)}")
    
    print("\nAnálise concluída")


def pipeline_completo():
    """Executa pipeline completo."""
    exibir_banner()
    print("Pipeline completo: processar -> otimizar -> analisar\n")
    
    print("Cenário de investimento:")
    print("1. Conservador (baixo risco)")
    print("2. Moderado (risco médio)")
    print("3. Agressivo (alto risco)")
    
    escolha = input("\nOpção (1/2/3) [padrão: 2]: ").strip() or '2'
    cenarios = {'1': 'conservador', '2': 'moderado', '3': 'agressivo'}
    cenario = cenarios.get(escolha, 'moderado')
    
    # Processar
    metricas = processar_dados()
    if metricas is None:
        return
    
    # Otimizar
    resultado = otimizar_carteira(metricas, cenario)
    if resultado is None:
        return
    
    solucao, metricas = resultado
    
    # Analisar
    analisar_resultados(solucao, metricas, cenario)
    
    print("\n" + "="*80)
    print(" "*25 + "PIPELINE CONCLUÍDO")
    print("="*80)
    print(f"\nArquivos gerados na pasta 'output/{cenario}/:")
    print("   • carteira_otimizada.csv")
    print("   • resultados_carteira.png")
    print("   • relatorio_otimizacao.txt")
    print("   • analise_completa.xlsx")
    print()
    print("\nMétricas gerais na pasta 'output/':")
    print("   • metricas_ativos.csv")


def main():
    """Função principal."""
    os.makedirs('data', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    exibir_banner()
    
    while True:
        escolha = menu_principal()
        
        if escolha == '0':
            print("\nEncerrando...\n")
            break
        
        elif escolha == '1':
            processar_dados()
        
        elif escolha == '2':
            print("\nCenário:")
            print("1. Conservador")
            print("2. Moderado")
            print("3. Agressivo")
            escolha_cenario = input("Opção (1/2/3) [padrão: 2]: ").strip() or '2'
            cenarios = {'1': 'conservador', '2': 'moderado', '3': 'agressivo'}
            cenario = cenarios.get(escolha_cenario, 'moderado')
            
            resultado = otimizar_carteira(cenario=cenario)
            if resultado:
                solucao, metricas = resultado
                resposta = input("\nAnalisar resultados agora? (s/n): ").strip().lower()
                if resposta == 's':
                    analisar_resultados(solucao, metricas, cenario)
        
        elif escolha == '3':
            pipeline_completo()
        
        elif escolha == '4':
            print("\nCenário:")
            print("1. Conservador")
            print("2. Moderado")
            print("3. Agressivo")
            escolha_cenario = input("Opção (1/2/3) [padrão: 2]: ").strip() or '2'
            cenarios = {'1': 'conservador', '2': 'moderado', '3': 'agressivo'}
            cenario = cenarios.get(escolha_cenario, 'moderado')
            analisar_resultados(cenario=cenario)
        
        else:
            print("\nOpção inválida")
        
        input("\nPressione ENTER para continuar...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperação cancelada")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

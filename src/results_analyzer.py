"""
Analisador de resultados da otimização com visualizações.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime


class ResultsAnalyzer:
    """Analisa e visualiza resultados da otimização."""
    
    def __init__(self, solucao, metricas_completas):
        self.solucao = solucao
        self.metricas = metricas_completas
        self.carteira = solucao['carteira']
        
    def imprimir_resumo(self):
        """Imprime resumo da carteira otimizada."""
        print("\n" + "="*80)
        print(" "*25 + "CARTEIRA OTIMIZADA")
        print("="*80)
        
        print(f"\nMÉTRICAS:")
        print(f"  {'Ativos:':<25} {self.solucao['num_ativos']}")
        print(f"  {'Retorno esperado:':<25} {self.solucao['retorno_total']:.2%}")
        print(f"  {'Risco (desvio-padrão):':<25} {self.solucao['risco_total']:.4f}")
        print(f"  {'Sharpe Ratio:':<25} {self.solucao['sharpe_carteira']:.4f}")
        print(f"  {'Investimento:':<25} R$ {self.solucao['investimento_total']:,.2f}")
        print(f"  {'Gap otimalidade:':<25} {self.solucao['gap']:.2%}")
        print(f"  {'Tempo execução:':<25} {self.solucao['tempo_exec']:.2f}s")
        
        print(f"\nDISTRIBUIÇÃO POR SETOR:")
        dist_setor = self.carteira.groupby('setor').agg({
            'investimento': 'sum',
            'ticker': 'count'
        }).rename(columns={'ticker': 'num_ativos'})
        dist_setor['percentual'] = dist_setor['investimento'] / dist_setor['investimento'].sum()
        dist_setor = dist_setor.sort_values('investimento', ascending=False)
        
        for setor, row in dist_setor.iterrows():
            print(f"  {setor:<20} {row['num_ativos']:>2} ativos  "
                  f"R$ {row['investimento']:>12,.2f}  ({row['percentual']:>6.1%})")
        
        print(f"\nATIVOS SELECIONADOS:")
        print(f"  {'#':<3} {'Ticker':<8} {'Empresa':<20} {'Setor':<15} "
              f"{'Invest.(R$)':>12} {'%':>6} {'Ret.':>7} {'Sharpe':>7}")
        print("  " + "-"*95)
        
        carteira_sorted = self.carteira.sort_values('investimento', ascending=False)
        for idx, row in enumerate(carteira_sorted.itertuples(), 1):
            pct = row.investimento / self.solucao['investimento_total']
            print(f"  {idx:<3} {row.ticker:<8} {row.nome[:20]:<20} {row.setor[:15]:<15} "
                  f"{row.investimento:>12,.2f} {pct:>6.1%} {row.retorno_esperado:>7.2%} "
                  f"{row.sharpe_ratio:>7.3f}")
        
        print("="*80 + "\n")
    
    def comparar_com_benchmark(self, benchmark_ticker='IBOV11'):
        """Compara carteira com benchmark."""
        if benchmark_ticker not in self.metricas.index:
            print(f"Benchmark {benchmark_ticker} não encontrado")
            return
        
        bench = self.metricas.loc[benchmark_ticker]
        
        print(f"\nCOMPARAÇÃO COM {benchmark_ticker}:")
        print(f"  {'Métrica':<20} {'Carteira':>15} {'Benchmark':>15} {'Diferença':>15}")
        print("  " + "-"*65)
        
        metricas = [
            ('Retorno', f"{self.solucao['retorno_total']:.2%}", 
             f"{bench['retorno_esperado']:.2%}",
             f"{(self.solucao['retorno_total'] - bench['retorno_esperado']):.2%}"),
            ('Risco', f"{self.solucao['risco_total']:.4f}", 
             f"{bench['desvio_padrao']:.4f}",
             f"{(self.solucao['risco_total'] - bench['desvio_padrao']):.4f}"),
            ('Sharpe', f"{self.solucao['sharpe_carteira']:.4f}", 
             f"{bench['sharpe_ratio']:.4f}",
             f"{(self.solucao['sharpe_carteira'] - bench['sharpe_ratio']):.4f}"),
        ]
        
        for metrica, cart, bench_val, diff in metricas:
            print(f"  {metrica:<20} {cart:>15} {bench_val:>15} {diff:>15}")
    
    def gerar_graficos(self, arquivo=None, cenario='moderado'):
        """Gera visualizações gráficas."""
        if arquivo is None:
            from . import config
            dirs = config.obter_diretorios_cenario(cenario)
            arquivo = dirs['grafico_png']
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('Análise da Carteira Otimizada', fontsize=16, fontweight='bold')
        
        # 1. Investimento por ativo
        ax1 = axes[0, 0]
        carteira_sorted = self.carteira.sort_values('investimento', ascending=False)
        colors = plt.cm.viridis(np.linspace(0, 1, len(carteira_sorted)))
        ax1.barh(carteira_sorted['ticker'], carteira_sorted['investimento'], color=colors)
        ax1.set_xlabel('Investimento (R$)', fontsize=11)
        ax1.set_ylabel('Ativo', fontsize=11)
        ax1.set_title('Distribuição do Investimento', fontsize=12, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        # 2. Distribuição setorial
        ax2 = axes[0, 1]
        dist_setor = self.carteira.groupby('setor')['investimento'].sum().sort_values(ascending=False)
        colors_setor = plt.cm.Set3(np.linspace(0, 1, len(dist_setor)))
        wedges, texts, autotexts = ax2.pie(
            dist_setor, labels=dist_setor.index, autopct='%1.1f%%',
            colors=colors_setor, startangle=90
        )
        ax2.set_title('Distribuição por Setor', fontsize=12, fontweight='bold')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # 3. Retorno vs Risco
        ax3 = axes[1, 0]
        scatter = ax3.scatter(
            self.carteira['desvio_padrao'], self.carteira['retorno_esperado'],
            s=self.carteira['investimento'] / 100,
            c=self.carteira['sharpe_ratio'], cmap='RdYlGn',
            alpha=0.7, edgecolors='black', linewidth=1
        )
        for _, row in self.carteira.iterrows():
            ax3.annotate(row['ticker'], 
                        (row['desvio_padrao'], row['retorno_esperado']),
                        fontsize=8, alpha=0.7)
        ax3.set_xlabel('Risco (Desvio-Padrão)', fontsize=11)
        ax3.set_ylabel('Retorno Esperado', fontsize=11)
        ax3.set_title('Retorno vs Risco', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax3, label='Sharpe Ratio')
        
        # 4. Sharpe Ratio
        ax4 = axes[1, 1]
        carteira_sharpe = self.carteira.sort_values('sharpe_ratio', ascending=True)
        colors_sharpe = ['green' if x > 0 else 'red' for x in carteira_sharpe['sharpe_ratio']]
        ax4.barh(carteira_sharpe['ticker'], carteira_sharpe['sharpe_ratio'], color=colors_sharpe)
        ax4.set_xlabel('Sharpe Ratio', fontsize=11)
        ax4.set_ylabel('Ativo', fontsize=11)
        ax4.set_title('Sharpe Ratio por Ativo', fontsize=12, fontweight='bold')
        ax4.axvline(x=0, color='black', linestyle='--', linewidth=0.8)
        ax4.grid(axis='x', alpha=0.3)
        
        # 5. Investimento vs Retorno Esperado
        ax5 = axes[1, 2]
        scatter2 = ax5.scatter(
            self.carteira['investimento'], 
            self.carteira['retorno_esperado'],
            s=200,
            c=self.carteira['sharpe_ratio'], 
            cmap='RdYlGn',
            alpha=0.7, 
            edgecolors='black', 
            linewidth=1.5
        )
        for _, row in self.carteira.iterrows():
            ax5.annotate(row['ticker'], 
                        (row['investimento'], row['retorno_esperado']),
                        fontsize=9, alpha=0.8, fontweight='bold')
        ax5.set_xlabel('Investimento (R$)', fontsize=11)
        ax5.set_ylabel('Retorno Esperado (%)', fontsize=11)
        ax5.set_title('Investimento vs Retorno Esperado', fontsize=12, fontweight='bold')
        ax5.grid(True, alpha=0.3)
        
        # Formatar eixo Y como percentual
        ax5.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))
        
        # Adicionar colorbar
        plt.colorbar(scatter2, ax=ax5, label='Sharpe Ratio')
        
        plt.tight_layout()
        plt.savefig(arquivo, dpi=300, bbox_inches='tight')
        print(f"\nGráficos salvos: {arquivo}")
        
        # Salvar gráficos individuais
        import os
        from . import config
        dirs = config.obter_diretorios_cenario(cenario)
        graficos_dir = dirs['dir']
        
        # 1. Salvar gráfico de investimento por ativo
        fig1, ax_temp = plt.subplots(figsize=(10, 8))
        carteira_sorted = self.carteira.sort_values('investimento', ascending=False)
        colors = plt.cm.viridis(np.linspace(0, 1, len(carteira_sorted)))
        ax_temp.barh(carteira_sorted['ticker'], carteira_sorted['investimento'], color=colors)
        ax_temp.set_xlabel('Investimento (R$)', fontsize=12)
        ax_temp.set_ylabel('Ativo', fontsize=12)
        ax_temp.set_title('Distribuição do Investimento por Ativo', fontsize=14, fontweight='bold')
        ax_temp.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{graficos_dir}01_investimento_por_ativo.png", dpi=300, bbox_inches='tight')
        plt.close(fig1)
        
        # 2. Salvar gráfico de distribuição setorial
        fig2, ax_temp = plt.subplots(figsize=(10, 8))
        dist_setor = self.carteira.groupby('setor')['investimento'].sum().sort_values(ascending=False)
        colors_setor = plt.cm.Set3(np.linspace(0, 1, len(dist_setor)))
        wedges, texts, autotexts = ax_temp.pie(
            dist_setor, labels=dist_setor.index, autopct='%1.1f%%',
            colors=colors_setor, startangle=90
        )
        ax_temp.set_title('Distribuição por Setor', fontsize=14, fontweight='bold')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        plt.tight_layout()
        plt.savefig(f"{graficos_dir}02_distribuicao_setorial.png", dpi=300, bbox_inches='tight')
        plt.close(fig2)
        
        # 3. Salvar gráfico de retorno vs risco
        fig3, ax_temp = plt.subplots(figsize=(10, 8))
        scatter_temp = ax_temp.scatter(
            self.carteira['desvio_padrao'], self.carteira['retorno_esperado'],
            s=self.carteira['investimento'] / 100,
            c=self.carteira['sharpe_ratio'], cmap='RdYlGn',
            alpha=0.7, edgecolors='black', linewidth=1
        )
        for _, row in self.carteira.iterrows():
            ax_temp.annotate(row['ticker'], 
                        (row['desvio_padrao'], row['retorno_esperado']),
                        fontsize=9, alpha=0.7)
        ax_temp.set_xlabel('Risco (Desvio-Padrão)', fontsize=12)
        ax_temp.set_ylabel('Retorno Esperado', fontsize=12)
        ax_temp.set_title('Retorno vs Risco', fontsize=14, fontweight='bold')
        ax_temp.grid(True, alpha=0.3)
        plt.colorbar(scatter_temp, ax=ax_temp, label='Sharpe Ratio')
        plt.tight_layout()
        plt.savefig(f"{graficos_dir}03_retorno_vs_risco.png", dpi=300, bbox_inches='tight')
        plt.close(fig3)
        
        # 4. Salvar gráfico de Sharpe Ratio
        fig4, ax_temp = plt.subplots(figsize=(10, 8))
        carteira_sharpe = self.carteira.sort_values('sharpe_ratio', ascending=True)
        colors_sharpe = ['green' if x > 0 else 'red' for x in carteira_sharpe['sharpe_ratio']]
        ax_temp.barh(carteira_sharpe['ticker'], carteira_sharpe['sharpe_ratio'], color=colors_sharpe)
        ax_temp.set_xlabel('Sharpe Ratio', fontsize=12)
        ax_temp.set_ylabel('Ativo', fontsize=12)
        ax_temp.set_title('Sharpe Ratio por Ativo', fontsize=14, fontweight='bold')
        ax_temp.axvline(x=0, color='black', linestyle='--', linewidth=0.8)
        ax_temp.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{graficos_dir}04_sharpe_ratio.png", dpi=300, bbox_inches='tight')
        plt.close(fig4)
        
        # 5. Salvar gráfico de investimento vs retorno
        fig5, ax_temp = plt.subplots(figsize=(10, 8))
        scatter2_temp = ax_temp.scatter(
            self.carteira['investimento'], 
            self.carteira['retorno_esperado'],
            s=200,
            c=self.carteira['sharpe_ratio'], 
            cmap='RdYlGn',
            alpha=0.7, 
            edgecolors='black', 
            linewidth=1.5
        )
        for _, row in self.carteira.iterrows():
            ax_temp.annotate(row['ticker'], 
                        (row['investimento'], row['retorno_esperado']),
                        fontsize=10, alpha=0.8, fontweight='bold')
        ax_temp.set_xlabel('Investimento (R$)', fontsize=12)
        ax_temp.set_ylabel('Retorno Esperado (%)', fontsize=12)
        ax_temp.set_title('Investimento vs Retorno Esperado', fontsize=14, fontweight='bold')
        ax_temp.grid(True, alpha=0.3)
        ax_temp.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))
        plt.colorbar(scatter2_temp, ax=ax_temp, label='Sharpe Ratio')
        plt.tight_layout()
        plt.savefig(f"{graficos_dir}05_investimento_vs_retorno.png", dpi=300, bbox_inches='tight')
        plt.close(fig5)
        
        print(f"   Gráficos individuais salvos em: {graficos_dir}")
        print(f"     - 01_investimento_por_ativo.png")
        print(f"     - 02_distribuicao_setorial.png")
        print(f"     - 03_retorno_vs_risco.png")
        print(f"     - 04_sharpe_ratio.png")
        print(f"     - 05_investimento_vs_retorno.png")
        
        return fig
    
    def exportar_relatorio(self, arquivo=None, cenario='moderado'):
        """Exporta relatório completo em texto."""
        if arquivo is None:
            from . import config
            dirs = config.obter_diretorios_cenario(cenario)
            arquivo = dirs['relatorio_txt']
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(" "*20 + "RELATÓRIO DE OTIMIZAÇÃO DE CARTEIRA\n")
            f.write(" "*25 + f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            f.write("MÉTRICAS GERAIS\n" + "-"*80 + "\n")
            f.write(f"Ativos: {self.solucao['num_ativos']}\n")
            f.write(f"Retorno: {self.solucao['retorno_total']:.4f} ({self.solucao['retorno_total']:.2%})\n")
            f.write(f"Risco: {self.solucao['risco_total']:.4f}\n")
            f.write(f"Sharpe: {self.solucao['sharpe_carteira']:.4f}\n")
            f.write(f"Investimento: R$ {self.solucao['investimento_total']:,.2f}\n")
            f.write(f"Gap: {self.solucao['gap']:.2%}\n")
            f.write(f"Tempo: {self.solucao['tempo_exec']:.2f}s\n\n")
            
            f.write("DISTRIBUIÇÃO SETORIAL\n" + "-"*80 + "\n")
            dist_setor = self.carteira.groupby('setor').agg({
                'investimento': 'sum', 'ticker': 'count'
            }).rename(columns={'ticker': 'num_ativos'})
            dist_setor['percentual'] = dist_setor['investimento'] / dist_setor['investimento'].sum()
            
            for setor, row in dist_setor.iterrows():
                f.write(f"{setor:<20} {row['num_ativos']:>2} ativos  "
                       f"R$ {row['investimento']:>12,.2f}  ({row['percentual']:>6.1%})\n")
            
            f.write("\nDETALHAMENTO DOS ATIVOS\n" + "-"*80 + "\n")
            f.write(f"{'Ticker':<8} {'Empresa':<25} {'Setor':<15} {'Invest.':<12} "
                   f"{'%':<6} {'Retorno':<8} {'Risco':<8} {'Sharpe':<8}\n")
            f.write("-"*80 + "\n")
            
            for _, row in self.carteira.sort_values('investimento', ascending=False).iterrows():
                pct = row['investimento'] / self.solucao['investimento_total']
                f.write(f"{row['ticker']:<8} {row['nome'][:25]:<25} {row['setor'][:15]:<15} "
                       f"{row['investimento']:>12,.2f} {pct:>6.1%} {row['retorno_esperado']:>8.2%} "
                       f"{row['desvio_padrao']:>8.4f} {row['sharpe_ratio']:>8.4f}\n")
            
            f.write("\n" + "="*80 + "\n")
        
        print(f"\nRelatório salvo: {arquivo}")
    
    def salvar_excel(self, arquivo=None, cenario='moderado'):
        """Salva análise em Excel com múltiplas abas."""
        if arquivo is None:
            from . import config
            dirs = config.obter_diretorios_cenario(cenario)
            arquivo = dirs['analise_xlsx']
        with pd.ExcelWriter(arquivo, engine='openpyxl') as writer:
            self.carteira.to_excel(writer, sheet_name='Carteira', index=False)
            
            dist_setor = self.carteira.groupby('setor').agg({
                'investimento': ['sum', 'mean'],
                'ticker': 'count',
                'retorno_esperado': 'mean',
                'desvio_padrao': 'mean',
                'sharpe_ratio': 'mean'
            })
            dist_setor.to_excel(writer, sheet_name='Setores')
            
            metricas_gerais = pd.DataFrame({
                'Métrica': ['Ativos', 'Retorno', 'Risco', 'Sharpe', 
                           'Investimento', 'Gap', 'Tempo (s)'],
                'Valor': [self.solucao['num_ativos'], self.solucao['retorno_total'],
                         self.solucao['risco_total'], self.solucao['sharpe_carteira'],
                         self.solucao['investimento_total'], self.solucao['gap'],
                         self.solucao['tempo_exec']]
            })
            metricas_gerais.to_excel(writer, sheet_name='Métricas', index=False)
        
        print(f"\nExcel salvo: {arquivo}")

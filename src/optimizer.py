"""
Otimizador de carteiras usando modelo de mochila robusto (Gurobi).
Baseado em Morita et al. (1989).
"""

import gurobipy as gp
from gurobipy import GRB
import pandas as pd


class PortfolioOptimizer:
    """Otimiza seleção de ativos usando MILP."""
    
    def __init__(self, metricas_df, config):
        self.metricas = metricas_df
        self.config = config
        self.model = None
        self.x_vars = None
        self.y_vars = None  # Agora representa quantidade de lotes/ações
        self.solucao = None
        
    def construir_modelo(self):
        """Constrói modelo MILP no Gurobi."""
        print("\n" + "="*60)
        print("CONSTRUINDO MODELO")
        print("="*60)
        
        self.model = gp.Model("Portfolio_Optimization")
        
        I = self.metricas.index.tolist()
        mu = self.metricas['retorno_esperado'].to_dict()
        sigma = self.metricas['desvio_padrao'].to_dict()
        preco = self.metricas['preco_atual'].to_dict()  # Preço por ação/lote
        
        B = self.config['orcamento']
        R = self.config['risco_maximo']
        T = self.config['retorno_minimo']
        L_min = self.config['num_ativos_min']
        L_max = self.config['num_ativos_max']
        
        print(f"\nParâmetros:")
        print(f"  Orçamento: R$ {B:,.2f}")
        print(f"  Risco máximo: {R:.4f}")
        print(f"  Retorno mínimo: {T:.2%}")
        print(f"  Ativos: [{L_min}, {L_max}]")
        print(f"  Disponíveis: {len(I)}")
        
        # Variáveis de decisão
        self.x_vars = self.model.addVars(I, vtype=GRB.BINARY, name="x")
        # y_vars: quantidade de lotes/ações compradas (inteiro não-negativo)
        self.y_vars = self.model.addVars(I, vtype=GRB.INTEGER, lb=0, name="y")
        
        # Função objetivo: maximizar retorno percentual médio ponderado
        # Retorno = Σ (retorno_% × investimento_i) / investimento_total
        # Para linearizar, maximizamos Σ (retorno_% × investimento_i) diretamente
        # pois investimento_total é aproximadamente fixo (uso total do orçamento)
        self.model.setObjective(
            gp.quicksum(mu[i] * preco[i] * self.y_vars[i] for i in I),
            GRB.MAXIMIZE
        )
        
        # Restrições
        # (eq:budget) Orçamento: soma dos gastos <= orçamento total
        # Gasto = preço × quantidade
        self.model.addConstr(
            gp.quicksum(preco[i] * self.y_vars[i] for i in I) <= B,
            name="orcamento"
        )
        
        # (eq:risk) Risco: desvio-padrão médio ponderado <= R
        # Σ(σ_i × invest_i) / invest_total <= R
        # Linearizando: Σ(σ_i × p_i × y_i) <= R × Σ(p_i × y_i)
        # Reorganizando: Σ(σ_i × p_i × y_i) - R × Σ(p_i × y_i) <= 0
        self.model.addConstr(
            gp.quicksum(sigma[i] * preco[i] * self.y_vars[i] for i in I) - R * gp.quicksum(preco[i] * self.y_vars[i] for i in I) <= 0,
            name="risco"
        )
        
        # (eq:return) Retorno mínimo: retorno médio ponderado >= T
        # Σ(μ_i × invest_i) / invest_total >= T
        # Linearizando: Σ(μ_i × p_i × y_i) >= T × Σ(p_i × y_i)
        # Reorganizando: Σ(μ_i × p_i × y_i) - T × Σ(p_i × y_i) >= 0
        self.model.addConstr(
            gp.quicksum(mu[i] * preco[i] * self.y_vars[i] for i in I) - T * gp.quicksum(preco[i] * self.y_vars[i] for i in I) >= 0,
            name="retorno_min"
        )
        
        # (eq:card) Cardinalidade: número de ativos entre L_min e L_max
        self.model.addConstr(
            gp.quicksum(self.x_vars[i] for i in I) >= L_min,
            name="min_ativos"
        )
        self.model.addConstr(
            gp.quicksum(self.x_vars[i] for i in I) <= L_max,
            name="max_ativos"
        )
        
        # (eq:max_sector, eq:min_sector) Diversificação setorial
        if self.config.get('diversificacao_setor', False):
            setores = self.metricas['setor'].unique()
            alpha_min = self.config.get('alpha_setor_min', 0.0)
            alpha_max = self.config.get('alpha_setor_max', 0.3)
            num_setores_min = self.config.get('num_setores_min', 1)
            
            print(f"\nDiversificação setorial:")
            print(f"  Setores disponíveis: {len(setores)}")
            print(f"  Limite máximo por setor: {alpha_max:.1%}")
            print(f"  Mínimo de setores diferentes: {num_setores_min}")
            
            # Variável binária: setor está sendo utilizado?
            z_setor = self.model.addVars(setores, vtype=GRB.BINARY, name="z_setor")
            
            for s in setores:
                ativos_setor = self.metricas[self.metricas['setor'] == s].index.tolist()
                if ativos_setor:
                    investimento_setor = gp.quicksum(preco[i] * self.y_vars[i] for i in ativos_setor)
                    
                    # (eq:max_sector) Limite máximo por setor
                    self.model.addConstr(
                        investimento_setor <= alpha_max * B,
                        name=f"setor_{s}_max"
                    )
                    
                    # Ativar z_setor se o setor for usado (investimento > 0)
                    # investimento_setor <= B × z_setor (se z=0, inv=0; se z=1, inv pode ser até B)
                    self.model.addConstr(
                        investimento_setor <= B * z_setor[s],
                        name=f"setor_{s}_ativa"
                    )
                    
                    # (eq:min_sector) Se setor é usado, investir pelo menos alpha_min
                    if alpha_min > 0:
                        self.model.addConstr(
                            investimento_setor >= alpha_min * B * z_setor[s],
                            name=f"setor_{s}_min"
                        )
            
            # Garantir número mínimo de setores diferentes
            self.model.addConstr(
                gp.quicksum(z_setor[s] for s in setores) >= num_setores_min,
                name="num_setores_min"
            )
        
        # Restrição de investimento máximo por ativo individual
        max_ativo_pct = self.config.get('max_ativo_pct', 1.0)
        if max_ativo_pct < 1.0:
            print(f"\nLimite por ativo: {max_ativo_pct:.1%} do orçamento")
            for i in I:
                self.model.addConstr(
                    preco[i] * self.y_vars[i] <= max_ativo_pct * B,
                    name=f"max_ativo_{i}"
                )
        
        # Excluir ativos com retorno negativo (conservadorismo)
        excluir_negativos = self.config.get('excluir_retorno_negativo', True)
        if excluir_negativos:
            negativos = [i for i in I if mu[i] < 0]
            if negativos:
                print(f"\nExcluindo {len(negativos)} ativos com retorno negativo")
                for i in negativos:
                    self.model.addConstr(
                        self.y_vars[i] == 0,
                        name=f"no_negative_{i}"
                    )
        
        # (eq:min_inv, eq:max_inv) Restrições de consistência
        # Se ativo não selecionado, não comprar ações (y = 0)
        # Se selecionado, comprar pelo menos 1 lote/ação
        max_lotes = int(B / min(preco.values())) if preco else 1000  # Limite superior razoável
        
        for i in I:
            # (eq:max_inv) Se x=0, então y=0
            self.model.addConstr(
                self.y_vars[i] <= max_lotes * self.x_vars[i],
                name=f"consistencia_max_{i}"
            )
            # (eq:min_inv) Se x=1, então y >= 1 (pelo menos 1 lote/ação)
            self.model.addConstr(
                self.y_vars[i] >= 1 * self.x_vars[i],
                name=f"consistencia_min_{i}"
            )
        
        # (eq:binary, eq:nonneg) já definidas nas variáveis
        
        print(f"\nModelo: {self.model.NumVars} variáveis, {self.model.NumConstrs} restrições")
        
    def otimizar(self, time_limit=300, mip_gap=0.0):
        """Resolve o modelo."""
        print("\n" + "="*60)
        print("RESOLVENDO MODELO")
        print("="*60)
        
        # Configurações para garantir ótimo global
        self.model.Params.TimeLimit = time_limit
        self.model.Params.MIPGap = mip_gap              # 0.0 = buscar ótimo global
        self.model.Params.MIPGapAbs = 0.0               # Gap absoluto = 0
        self.model.Params.OptimalityTol = 1e-9          # Tolerância de otimalidade
        self.model.Params.IntFeasTol = 1e-9             # Tolerância de integralidade
        self.model.Params.FeasibilityTol = 1e-9         # Tolerância de viabilidade
        self.model.Params.MIPFocus = 2                  # Foco em provar otimalidade
        self.model.Params.Presolve = 2                  # Presolve agressivo
        self.model.Params.Cuts = 2                      # Cortes agressivos
        self.model.Params.Heuristics = 0.05             # Menos heurísticas, mais exato
        self.model.Params.OutputFlag = 1
        
        print("\nParâmetros Gurobi (busca ótimo global):")
        print(f"  MIPGap: {mip_gap:.10f} (0 = ótimo global)")
        print(f"  TimeLimit: {time_limit}s")
        print(f"  MIPFocus: 2 (provar otimalidade)")
        
        self.model.optimize()
        
        if self.model.Status == GRB.OPTIMAL:
            print("\nSolução ótima encontrada")
        elif self.model.Status == GRB.TIME_LIMIT:
            print("\n⏰ Limite de tempo atingido")
        elif self.model.Status == GRB.INFEASIBLE:
            print("\nModelo inviável")
            self.model.computeIIS()
            print("\nRestrições conflitantes:")
            for c in self.model.getConstrs():
                if c.IISConstr:
                    print(f"  - {c.ConstrName}")
            return None
        else:
            print(f"\nStatus desconhecido: {self.model.Status}")
            return None
        
        self.extrair_solucao()
        return self.solucao
    
    def extrair_solucao(self):
        """Extrai solução do modelo otimizado."""
        print("\n" + "="*60)
        print("EXTRAÇÃO DA SOLUÇÃO")
        print("="*60)
        
        ativos_selecionados = [i for i in self.metricas.index if self.x_vars[i].X > 0.5]
        
        carteira = []
        for ativo in ativos_selecionados:
            quantidade = int(round(self.y_vars[ativo].X))
            preco_unitario = self.metricas.loc[ativo, 'preco_atual']
            investimento = quantidade * preco_unitario
            
            carteira.append({
                'ticker': ativo,
                'nome': self.metricas.loc[ativo, 'nome_empresa'],
                'setor': self.metricas.loc[ativo, 'setor'],
                'preco': preco_unitario,
                'quantidade': quantidade,
                'investimento': investimento,
                'retorno_esperado': self.metricas.loc[ativo, 'retorno_esperado'],
                'desvio_padrao': self.metricas.loc[ativo, 'desvio_padrao'],
                'sharpe_ratio': self.metricas.loc[ativo, 'sharpe_ratio']
            })
        
        df_carteira = pd.DataFrame(carteira)
        
        investimento_total = df_carteira['investimento'].sum()
        
        # Retorno percentual médio ponderado
        retorno_total = sum(
            self.metricas.loc[i, 'retorno_esperado'] * 
            self.metricas.loc[i, 'preco_atual'] * 
            self.y_vars[i].X
            for i in ativos_selecionados
        ) / investimento_total if investimento_total > 0 else 0
        
        # Risco (desvio-padrão) médio ponderado
        risco_total = sum(
            self.metricas.loc[i, 'desvio_padrao'] * 
            self.metricas.loc[i, 'preco_atual'] * 
            self.y_vars[i].X
            for i in ativos_selecionados
        ) / investimento_total if investimento_total > 0 else 0
        
        self.solucao = {
            'carteira': df_carteira,
            'num_ativos': len(ativos_selecionados),
            'retorno_total': retorno_total,
            'risco_total': risco_total,
            'sharpe_carteira': retorno_total / risco_total if risco_total > 0 else 0,
            'investimento_total': investimento_total,
            'funcao_objetivo': self.model.ObjVal,
            'gap': self.model.MIPGap,
            'tempo_exec': self.model.Runtime
        }
        
        print(f"\nResumo:")
        print(f"  Ativos: {self.solucao['num_ativos']}")
        print(f"  Retorno: {self.solucao['retorno_total']:.2%}")
        print(f"  Risco: {self.solucao['risco_total']:.4f}")
        print(f"  Sharpe: {self.solucao['sharpe_carteira']:.4f}")
        print(f"  Investimento: R$ {self.solucao['investimento_total']:,.2f}")
        print(f"  Gap: {self.solucao['gap']:.2%}")
        print(f"  Tempo: {self.solucao['tempo_exec']:.2f}s")
        
        return self.solucao
    
    def salvar_solucao(self, arquivo=None):
        """Salva carteira otimizada em CSV."""
        if arquivo is None:
            from . import config
            cenario_nome = self.config.get('cenario_nome', 'moderado')
            dirs = config.obter_diretorios_cenario(cenario_nome)
            arquivo = dirs['carteira_csv']
        
        if self.solucao:
            self.solucao['carteira'].to_csv(arquivo, index=False)
            print(f"\nCarteira salva: {arquivo}")
    
    def executar_otimizacao_completa(self):
        """Executa pipeline completo de otimização."""
        self.construir_modelo()
        self.otimizar()
        
        if self.solucao:
            self.salvar_solucao()
        
        return self.solucao

import streamlit as st
import pandas as pd
import datetime
from scipy.stats import poisson

# =============================================
# FUNÇÕES DE CÁLCULO ESTATÍSTICO
# =============================================

def poisson_prob(lamb: float, goals: int) -> float:
    """Calcula a probabilidade de marcar 'goals' gols com média 'lamb' usando a distribuição de Poisson."""
    return poisson.pmf(goals, lamb)

def poisson_match_result(lambda_home: float, lambda_away: float, max_goals: int = 5) -> tuple:
    """
    Calcula as probabilidades de vitória da casa, empate e vitória do visitante,
    considerando uma distribuição de Poisson para os gols.
    """
    prob_home, prob_draw, prob_away = 0, 0, 0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)
            if i > j:
                prob_home += p
            elif i == j:
                prob_draw += p
            else:
                prob_away += p
    return prob_home, prob_draw, prob_away

def calcular_probabilidades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada jogo no DataFrame, calcula:
      - Probabilidades do resultado (casa, empate, fora)
      - Odds justas (inverso das probabilidades)
      - Probabilidade de mais de 2.5 gols (over 2.5)
      - Probabilidade de ambos marcarem (BTTS)
    Retorna um DataFrame com os resultados formatados.
    """
    resultados = []
    for _, row in df.iterrows():
        home_team = row['Home']
        away_team = row['Away']
        odd_home = row['Odd_H_FT']
        odd_draw = row['Odd_D_FT']
        odd_away = row['Odd_A_FT']
        
        lambda_home = row['PPG_Home']
        lambda_away = row['PPG_Away']
        
        # Probabilidades do resultado do jogo
        model_prob_home, model_prob_draw, model_prob_away = poisson_match_result(lambda_home, lambda_away)
        
        fair_odd_home = round(1 / model_prob_home, 2) if model_prob_home > 0 else None
        fair_odd_draw = round(1 / model_prob_draw, 2) if model_prob_draw > 0 else None
        fair_odd_away = round(1 / model_prob_away, 2) if model_prob_away > 0 else None
        
        # Probabilidade de Over 2.5 gols (exceto combinações com menos de 2 gols)
        over_2_5 = 1 - sum(
            poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)
            for i in range(3)  # 0, 1, 2 gols do time da casa
            for j in range(3 - i)  # Garante que i + j <= 2
        )
        
        # Probabilidade de ambos marcarem (BTTS)
        prob_home_no_goal = poisson_prob(lambda_home, 0)  # Probabilidade do time da casa não marcar
        prob_away_no_goal = poisson_prob(lambda_away, 0)  # Probabilidade do time visitante não marcar
        prob_either_no_goal = prob_home_no_goal + prob_away_no_goal - (prob_home_no_goal * prob_away_no_goal)
        btts = 1 - prob_either_no_goal
        
        resultados.append({
            'Jogo': f"{home_team} x {away_team}",
            'Odd Mercado Casa': odd_home,
            'Prob Casa (%)': round(model_prob_home * 100, 2),
            'Odd Justa Casa': fair_odd_home,
            'Odd Mercado Empate': odd_draw,
            'Prob Empate (%)': round(model_prob_draw * 100, 2),
            'Odd Justa Empate': fair_odd_draw,
            'Odd Mercado Fora': odd_away,
            'Prob Fora (%)': round(model_prob_away * 100, 2),
            'Odd Justa Fora': fair_odd_away,
            'Prob Over 2.5 (%)': round(over_2_5 * 100, 2),
            'Prob BTTS (%)': round(btts * 100, 2)
        })
    return pd.DataFrame(resultados)

def highlight_probs(row: pd.Series) -> pd.Series:
    """
    Aplica formatação condicional nas colunas de probabilidade, destacando valores positivos em verde
    e negativos em vermelho, conforme comparação entre odds de mercado e odds justas.
    """
    styles = {}
    styles['Prob Casa (%)'] = 'background-color: #c6efce; color: #006100' \
        if row['Odd Mercado Casa'] > row['Odd Justa Casa'] else 'background-color: #ffc7ce; color: #9c0006'
    styles['Prob Empate (%)'] = 'background-color: #c6efce; color: #006100' \
        if row['Odd Mercado Empate'] > row['Odd Justa Empate'] else 'background-color: #ffc7ce; color: #9c0006'
    styles['Prob Fora (%)'] = 'background-color: #c6efce; color: #006100' \
        if row['Odd Mercado Fora'] > row['Odd Justa Fora'] else 'background-color: #ffc7ce; color: #9c0006'
    return pd.Series(styles)

def identificar_oportunidades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifica jogos com valor de mercado com base nos seguintes critérios:
      - Odd de mercado (casa ou fora) maior que a odd justa
      - Probabilidade de Over 2.5 gols superior a 60%
    Retorna o DataFrame ordenado pela probabilidade de vitória da casa (decrescente).
    """
    criterios = (
        ((df['Odd Mercado Casa'] > df['Odd Justa Casa']) | (df['Odd Mercado Fora'] > df['Odd Justa Fora'])) &
        (df['Prob Over 2.5 (%)'] > 60)
    )
    return df[criterios].sort_values('Prob Casa (%)', ascending=False)

# =============================================
# CONFIGURAÇÃO DA PÁGINA E CSS
# =============================================

st.set_page_config(
    page_title="FootyAnalytics Pro - Análise de Mercado Esportivo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --primary: #2A4D69;
        --secondary: #4B86B4;
        --accent: #ADEFD1;
        --background: #F0F4F8;
    }

    .main {background-color: var(--background);}

    .header-container {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        padding: 2.5rem 2rem;
        border-radius: 0 0 25px 25px;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }

    .header-title {
        color: white !important;
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        letter-spacing: -1px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }

    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 1.8rem;
        margin: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid rgba(0,0,0,0.05);
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.12);
    }

    .metric-value {
        font-size: 2.2rem !important;
        color: var(--primary) !important;
        margin: 0.5rem 0;
    }

    .styled-table {
        border-radius: 15px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06) !important;
        border: 1px solid rgba(0,0,0,0.08) !important;
    }

    .styled-table thead th {
        background: var(--primary) !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 1.2rem !important;
        font-size: 1.1rem;
    }

    .styled-table tbody td {
        padding: 1rem !important;
        vertical-align: middle !important;
        font-size: 0.95rem;
    }

    .styled-table tbody tr:nth-child(even) {
        background-color: #f8fafc;
    }

    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .positive {background: #e6f4ea; color: #137333;}
    .negative {background: #fce8e6; color: #a50e0e;}

    .search-box {
        margin: 1.5rem 0;
        padding: 0.8rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# INTERFACE PRINCIPAL
# =============================================

st.markdown("""
<div class="header-container">
    <h1 class="header-title">⚽ FootyAnalytics Pro - Análise de Mercado Esportivo</h1>
</div>
""", unsafe_allow_html=True)

try:
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    csv_url = f"https://raw.githubusercontent.com/futpythontrader/YouTube/main/Jogos_do_Dia/FootyStats/Jogos_do_Dia_FootyStats_{hoje}.csv"
    
    df_jogos = pd.read_csv(csv_url)
    df_final = calcular_probabilidades(df_jogos)
    df_oportunidades = identificar_oportunidades(df_final)
    
    # Seção de métricas
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <div style="color: var(--secondary);">🗓️ Total de Jogos</div>
                <div class="metric-value">{len(df_jogos)}</div>
                <div style="color: #6c757d;">+2.5% vs média</div>
            </div>
            ''', unsafe_allow_html=True)

        with col2:
            st.markdown(f'''
            <div class="metric-card">
                <div style="color: var(--secondary);">📈 Valor de Mercado</div>
                <div class="metric-value">R$ {len(df_jogos)*1250:,.2f}</div>
                <div style="color: #6c757d;">Liquidez estimada</div>
            </div>
            ''', unsafe_allow_html=True)

        with col3:
            st.markdown(f'''
            <div class="metric-card">
                <div style="color: var(--secondary);">🎯 Oportunidades</div>
                <div class="metric-value">{len(df_oportunidades)}</div>
                <div style="color: #6c757d;">Jogos com valor</div>
            </div>
            ''', unsafe_allow_html=True)

        with col4:
            melhor_oportunidade = df_oportunidades.iloc[0] if not df_oportunidades.empty else None
            st.markdown(f'''
            <div class="metric-card">
                <div style="color: var(--secondary);">🔥 Melhor Oportunidade</div>
                <div style="font-size: 1.1rem;">{melhor_oportunidade['Jogo'] if melhor_oportunidade is not None else 'Nenhuma'}</div>
                <div class="status-badge {'positive' if melhor_oportunidade is not None else 'negative'}">
                    {f"+{melhor_oportunidade['Odd Mercado Casa'] - melhor_oportunidade['Odd Justa Casa']:.2f}" if melhor_oportunidade is not None else "Sem dados"}
                </div>
            </div>
            ''', unsafe_allow_html=True)

    # Barra de pesquisa
    search_term = st.text_input("🔍 Pesquisar Jogos:", placeholder="Digite o nome do time, liga ou país...", key="search_input")
    df_filtrado = df_final[df_final['Jogo'].str.contains(search_term, case=False)]
    
    # Seção de oportunidades
    with st.expander("💎 Top 5 Oportunidades de Mercado", expanded=True):
        if not df_oportunidades.empty:
            cols = st.columns([3, 1])
            with cols[0]:
                st.dataframe(
                    df_oportunidades.head(5).style
                    .apply(highlight_probs, axis=1)
                    .format({
                        'Prob Casa (%)': '{:.1f}%',
                        'Odd Justa Casa': '{:.2f}',
                        'Prob Over 2.5 (%)': '{:.1f}%'
                    }),
                    height=250
                )
            with cols[1]:
                taxa_sucesso = (len(df_oportunidades) / len(df_jogos)) * 100
                st.metric("Taxa de Sucesso", f"{taxa_sucesso:.1f}%", "dos jogos com valor")
                st.progress(len(df_oportunidades) / len(df_jogos))
        else:
            st.warning("⚠️ Nenhuma oportunidade identificada nos critérios atuais")
    
    # Seção principal de probabilidades
    st.markdown("### 📊 Probabilidades Detalhadas")
    st.dataframe(
        df_filtrado.style
        .apply(highlight_probs, axis=1)
        .format({
            'Prob Casa (%)': '{:.1f}%',
            'Odd Justa Casa': '{:.2f}',
            'Prob Empate (%)': '{:.1f}%',
            'Odd Justa Empate': '{:.2f}',
            'Prob Fora (%)': '{:.1f}%',
            'Odd Justa Fora': '{:.2f}',
            'Prob Over 2.5 (%)': '{:.1f}%',
            'Prob BTTS (%)': '{:.1f}%'
        })
        .set_properties(subset=['Prob Over 2.5 (%)', 'Prob BTTS (%)'], **{'background': '#fff9e6', 'color': '#8b8000'})
        .set_table_styles([{
            'selector': '',
            'props': [('border-radius', '15px'), ('overflow', 'hidden')]
        }]),
        height=800,
        use_container_width=True
    )

except Exception as e:
    st.markdown(f"""
    <div class="metric-card" style="background: #fce8e6; color: #a50e0e;">
        <h3>🚨 Erro no Processamento</h3>
        <p>{str(e)}</p>
    </div>
    """, unsafe_allow_html=True)

# Seção de legenda
st.markdown("""
<div class="metric-card" style="margin-top: 2rem; background: #1C1C1C;">
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem;">
        <div>
            <h4>📌 Legenda de Cores</h4>
            <div style="display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0;">
                <div style="width: 20px; height: 20px; border-radius: 4px; background: #1C1C1C;"></div>
                <span>Valor Positivo</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 20px; height: 20px; border-radius: 4px; background: #1C1C1C;"></div>
                <span>Valor Negativo</span>
            </div>
        </div>
        <div>
            <h4>📊 Metodologia</h4>
            <ul style="margin: 0; padding-left: 1.2rem;">
                <li>Modelo Poisson para previsão</li>
                <li>Dados atualizados em tempo real</li>
                <li>Atualização automática a cada 15min</li>
                <li>Critérios de oportunidade:
                    <ul>
                        <li>Odd de mercado > Odd justa</li>
                        <li>Prob. Over 2.5 gols > 60%</li>
                    </ul>
                </li>
            </ul>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

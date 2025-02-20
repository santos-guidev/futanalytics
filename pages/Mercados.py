import streamlit as st
import pandas as pd
import psycopg2
import math
import difflib

# =============================
# 1) CSS Personalizado
# =============================
css = """
<style>
/* Cor de fundo da aplicação */
.stApp {
    background-color: #0f0d09;
}

/* Estilo para os títulos (h1, h2, h3) */
h1, h2, h3 {
    font-family: 'Arial', sans-serif;
    color: #333333;
}

/* Estilo para os widgets de texto e botões */
.css-1c2j2mg {
    color: #333333;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# =============================
# 2) Carregamento dos Dados
# =============================
@st.cache_data(show_spinner=True)
def load_all_data():
    """
    Conecta ao PostgreSQL, carrega os dados da tabela 'tabela_ligas'
    e retorna um DataFrame pandas.
    """
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="matches",
            user="postgres",
            password="1408",
            port="5432"
        )
        query = "SELECT * FROM tabela_ligas;"
        data = pd.read_sql(query, conn)
        conn.close()
        return data
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {e}")
        return pd.DataFrame()

data = load_all_data()

# =============================
# 3) Ajuste e Mapeamento de Times
# =============================
if data.empty:
    st.error("Não foram encontrados dados no banco de dados.")
    st.stop()

teams = set(data['home'].unique()).union(set(data['away'].unique()))
teams_lower = {team.lower() for team in teams if isinstance(team, str)}
team_map = {team.lower(): team for team in teams if isinstance(team, str)}

# =============================
# 4) Título e Introdução
# =============================
st.title("⚽ Predição de Partidas - Análise Avançada")
st.markdown("---")
st.write("""
Este aplicativo utiliza um **modelo estatístico** (Poisson) para estimar:
- **Gols esperados** na partida
- **Odds justas** para diferentes mercados (Over 2.5, Back Favorito, Lay Zebra e Ambas Marcam)
- **Valor esperado** de cada aposta, comparando com as odds do mercado

Preencha as informações abaixo para iniciar a análise.
""")

# =============================
# 5) Entrada de Dados do Usuário
# =============================
col_input1, col_input2 = st.columns(2)
with col_input1:
    input_home = st.text_input("🟢 Time da Casa").strip()
    input_away = st.text_input("🔴 Time Visitante").strip()

with col_input2:
    market_odd_input = st.text_input("Odd Real do Mercado para Over 2.5 gols", value="")
    market_odd_back = st.text_input("Odd Real do Mercado para Back Favorito", value="")
    market_odd_lay = st.text_input("Odd Real do Mercado para Lay Zebra", value="")
    market_odd_both = st.text_input("Odd Real do Mercado para Ambas Marcam", value="")

# Função para buscar times similares (usando cutoff=0.4)
def find_similar_team(input_team, teams_set, cutoff=0.4):
    matches = difflib.get_close_matches(input_team.lower(), teams_set, n=5, cutoff=cutoff)
    return [team_map.get(match, match) for match in matches]

# =============================
# 6) Botão de Análise
# =============================
if st.button("Analisar Partida"):
    if not input_home or not input_away:
        st.error("Por favor, insira os nomes dos dois times.")
        st.stop()

    # Ajusta para minúsculo
    input_home_lower = input_home.lower()
    input_away_lower = input_away.lower()
    
    # Verifica time da casa
    if input_home_lower not in teams_lower:
        similar_home = find_similar_team(input_home, teams_lower)
        if similar_home:
            if len(similar_home) == 1:
                home_team = similar_home[0]
                st.info(f"Time da Casa não encontrado exatamente. Usando a sugestão: {home_team}")
            else:
                st.error(f"Time da Casa não encontrado. Você quis dizer: {', '.join(similar_home)}?")
                st.stop()
        else:
            st.error("Time da Casa não encontrado e nenhuma sugestão foi encontrada.")
            st.stop()
    else:
        home_team = team_map[input_home_lower]
    
    # Verifica time visitante
    if input_away_lower not in teams_lower:
        similar_away = find_similar_team(input_away, teams_lower)
        if similar_away:
            if len(similar_away) == 1:
                away_team = similar_away[0]
                st.info(f"Time Visitante não encontrado exatamente. Usando a sugestão: {away_team}")
            else:
                st.error(f"Time Visitante não encontrado. Você quis dizer: {', '.join(similar_away)}?")
                st.stop()
        else:
            st.error("Time Visitante não encontrado e nenhuma sugestão foi encontrada.")
            st.stop()
    else:
        away_team = team_map[input_away_lower]
    
    # Filtra dados de cada time
    home_matches = data[data['home'] == home_team]
    away_matches = data[data['away'] == away_team]
    
    if home_matches.empty or away_matches.empty:
        st.error("Não foram encontrados dados suficientes para um ou ambos os times. Verifique a disponibilidade dos dados.")
        st.stop()

    # =============================
    # 7) Cálculo de Estatísticas
    # =============================
    home_avg_goals_scored = home_matches['goals_h_ft'].mean()
    home_avg_goals_conceded = home_matches['goals_a_ft'].mean()
    away_avg_goals_scored = away_matches['goals_a_ft'].mean()
    away_avg_goals_conceded = away_matches['goals_h_ft'].mean()
    
    # Exibição das estatísticas básicas
    st.markdown("### 📊 Estatísticas Básicas dos Times")
    st.write(f"**{home_team} (Casa)**")
    st.write(f"- Média de Gols Marcados: {home_avg_goals_scored:.2f}")
    st.write(f"- Média de Gols Sofridos: {home_avg_goals_conceded:.2f}")
    
    st.write(f"**{away_team} (Fora)**")
    st.write(f"- Média de Gols Marcados: {away_avg_goals_scored:.2f}")
    st.write(f"- Média de Gols Sofridos: {away_avg_goals_conceded:.2f}")

    # Cálculo de gols esperados
    expected_home_goals = home_avg_goals_scored
    expected_away_goals = away_avg_goals_scored
    lambda_total = expected_home_goals + expected_away_goals
    
    st.markdown("### ⚽ Previsão de Gols (Modelo Poisson)")
    st.write(f"Gols esperados na partida (total): **{lambda_total:.2f}**")

    # =============================
    # 8) Over 2.5 - Cálculo e Valor
    # =============================
    st.markdown("### 🔍 Over 2.5 Gols - Odd Justa")
    p0 = math.exp(-lambda_total)
    p1 = lambda_total * math.exp(-lambda_total)
    p2 = (lambda_total**2 / 2) * math.exp(-lambda_total)
    prob_under_2_5 = p0 + p1 + p2
    prob_over_2_5 = 1 - prob_under_2_5
    fair_odd_over25 = 1 / prob_over_2_5 if prob_over_2_5 > 0 else None
    
    st.write(f"**Probabilidade de over 2.5 gols:** {prob_over_2_5*100:.2f}%")
    if fair_odd_over25:
        st.write(f"**Odd Justa (Over 2.5):** {fair_odd_over25:.2f}")
    else:
        st.error("Não foi possível calcular a odd justa para Over 2.5 gols.")

    st.markdown("#### 🔎 Valor Esperado - Over 2.5 Gols")
    try:
        market_odd = float(market_odd_input)
        if fair_odd_over25:
            if market_odd > fair_odd_over25:
                st.success("A aposta em Over 2.5 pode ter valor (valor esperado positivo).")
            else:
                st.warning("A aposta em Over 2.5 pode não ter valor.")
        else:
            st.error("Não foi possível comparar, pois a odd justa não pôde ser calculada.")
    except ValueError:
        st.error("Por favor, insira uma odd real válida para Over 2.5 gols.")

    # =============================
    # 9) Back Favorito & Lay Zebra
    # =============================
    st.markdown("### ⚖️ Back Favorito e Lay Zebra - Odds Justas")
    def poisson_probability(k, lambd):
        return (lambd**k) * math.exp(-lambd) / math.factorial(k)
    
    def compute_match_probabilities(lambda_home, lambda_away, max_goals=10):
        home_win = 0
        draw = 0
        away_win = 0
        for x in range(max_goals+1):
            for y in range(max_goals+1):
                p = poisson_probability(x, lambda_home) * poisson_probability(y, lambda_away)
                if x > y:
                    home_win += p
                elif x == y:
                    draw += p
                else:
                    away_win += p
        return {'home_win': home_win, 'draw': draw, 'away_win': away_win}

    probs = compute_match_probabilities(expected_home_goals, expected_away_goals)
    
    # Determina favorito e azarão
    if expected_home_goals > expected_away_goals:
        favorite = home_team
        underdog = away_team
        back_favorito_prob = probs['home_win']
        lay_zebra_prob = probs['away_win']
    elif expected_home_goals < expected_away_goals:
        favorite = away_team
        underdog = home_team
        back_favorito_prob = probs['away_win']
        lay_zebra_prob = probs['home_win']
    else:
        favorite = 'Indefinido (times iguais)'
        underdog = 'Indefinido (times iguais)'
        back_favorito_prob = probs['home_win']
        lay_zebra_prob = probs['away_win']
    
    fair_odd_back = 1 / back_favorito_prob if back_favorito_prob > 0 else None
    fair_odd_lay = 1 / lay_zebra_prob if lay_zebra_prob > 0 else None
    
    st.write(f"**Probabilidade de vitória do favorito ({favorite}):** {back_favorito_prob*100:.2f}%")
    if fair_odd_back:
        st.write(f"**Odd Justa (Back Favorito):** {fair_odd_back:.2f}")
    else:
        st.error("Não foi possível calcular a odd justa para Back Favorito.")
    
    st.write(f"**Probabilidade de vitória do azarão ({underdog}):** {lay_zebra_prob*100:.2f}%")
    if fair_odd_lay:
        st.write(f"**Odd Justa (Lay Zebra):** {fair_odd_lay:.2f}")
    else:
        st.error("Não foi possível calcular a odd justa para Lay Zebra.")

    # Análise de valor - Back e Lay
    st.markdown("#### 🔎 Valor Esperado - Back e Lay")
    try:
        market_odd_back_val = float(market_odd_back)
        market_odd_lay_val = float(market_odd_lay)
        
        # Back Favorito
        st.write(f"**Análise de Valor - Back Favorito ({favorite})**")
        if fair_odd_back:
            if market_odd_back_val > fair_odd_back:
                st.success("A aposta no Back Favorito pode ter valor (valor esperado positivo).")
            else:
                st.warning("A aposta no Back Favorito pode não ter valor.")
        else:
            st.error("Não foi possível comparar, pois a odd justa para Back Favorito não pôde ser calculada.")
        
        # Lay Zebra
        st.write(f"**Análise de Valor - Lay Zebra ({underdog})**")
        if fair_odd_lay:
            if market_odd_lay_val > fair_odd_lay:
                st.success("A aposta no Lay Zebra pode ter valor (valor esperado positivo).")
            else:
                st.warning("A aposta no Lay Zebra pode não ter valor.")
        else:
            st.error("Não foi possível comparar, pois a odd justa para Lay Zebra não pôde ser calculada.")
    except ValueError:
        st.error("Por favor, insira odds reais válidas para Back Favorito e Lay Zebra.")

    # =============================
    # 10) Ambas Marcam (BTTS)
    # =============================
    st.markdown("### 🔍 Ambas Marcam (BTTS) - Odd Justa")
    prob_both = (1 - math.exp(-expected_home_goals)) * (1 - math.exp(-expected_away_goals))
    fair_odd_both = 1 / prob_both if prob_both > 0 else None
    
    st.write(f"**Probabilidade de ambas marcarem:** {prob_both*100:.2f}%")
    if fair_odd_both:
        st.write(f"**Odd Justa (Ambas Marcam):** {fair_odd_both:.2f}")
    else:
        st.error("Não foi possível calcular a odd justa para Ambas Marcam.")

    st.markdown("#### 🔎 Valor Esperado - Ambas Marcam")
    try:
        market_odd_both_val = float(market_odd_both)
        if fair_odd_both:
            if market_odd_both_val > fair_odd_both:
                st.success("A aposta para Ambas Marcam pode ter valor (valor esperado positivo).")
            else:
                st.warning("A aposta para Ambas Marcam pode não ter valor.")
        else:
            st.error("Não foi possível comparar, pois a odd justa para Ambas Marcam não pôde ser calculada.")
    except ValueError:
        st.error("Por favor, insira uma odd real válida para Ambas Marcam.")

# =============================
# RODAPÉ
# =============================
st.markdown("---")
st.markdown("**Desenvolvido por Gui Santos** • Modelo de Análise de Partidas")

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import datetime
import numpy as np

# =============================
# 1) CONFIGURAÇÃO DA PÁGINA
# =============================
st.set_page_config(
    page_title="Análise Futebolística Avançada",
    page_icon="⚽",
    layout="wide"
)

# =============================
# 2) FUNÇÃO DE CARREGAMENTO
# =============================
@st.cache_data(show_spinner="Carregando dados das ligas...")
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

# =============================
# 3) CARREGAR E PRÉ-PROCESSAR
# =============================
data = load_all_data()

if not data.empty:
    # Ajusta tipo de data
    data['match_date'] = pd.to_datetime(data['match_date']).dt.date
    
    # Cria coluna de Resultado (Vitória Casa, Empate ou Vitória Fora)
    data['Resultado'] = data.apply(
        lambda x: 'Vitória Casa' if x['goals_h_ft'] > x['goals_a_ft']
        else 'Vitória Fora' if x['goals_h_ft'] < x['goals_a_ft']
        else 'Empate', 
        axis=1
    )
    
    # Garante que a coluna de gols totais seja numérica
    data['totalgoals_ft'] = pd.to_numeric(data['totalgoals_ft'], errors='coerce').fillna(0)
    
    # Cria coluna para indicar se ambas as equipes marcaram (BTTS)
    data['AmbasMarcam'] = data.apply(
        lambda x: 'Sim' if (x['goals_h_ft'] > 0 and x['goals_a_ft'] > 0) else 'Não',
        axis=1
    )
else:
    st.warning("Não foram encontrados dados no banco de dados.")

# =============================
# 4) INTERFACE PRINCIPAL
# =============================
st.title("⚽ Painel de Análise Futebolística")
st.markdown("---")

# 4.1) SIDEBAR COM FILTROS
with st.sidebar:
    st.header("⚙ Filtros")
    if not data.empty:
        # Listar todos os times removendo valores nulos
        times = sorted([x for x in set(data['home'].unique()).union(set(data['away'].unique())) if pd.notnull(x)])
        selecionados = st.multiselect(
            'Selecione times para análise:',
            options=times,
            max_selections=2
        )
        
        # Filtro de data
        min_date = data['match_date'].min()
        max_date = data['match_date'].max()
        date_range = st.date_input(
            "Período de análise:",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
    else:
        selecionados = []
        date_range = []

# 4.2) FILTRO PRINCIPAL NOS DADOS
if selecionados:
    df_filtrado = data[
        (data['home'].isin(selecionados)) | 
        (data['away'].isin(selecionados))
    ]
else:
    df_filtrado = data.copy()

if len(date_range) == 2 and not df_filtrado.empty:
    df_filtrado = df_filtrado[
        (df_filtrado['match_date'] >= date_range[0]) &
        (df_filtrado['match_date'] <= date_range[1])
    ]

# =============================
# 5) EXIBIÇÃO DE RESULTADOS
# =============================
if not df_filtrado.empty:
    # 5.1) VISÃO GERAL INSTANTÂNEA
    st.subheader("📊 Visão Geral Instantânea")
    col1, col2, col3, col4, col5 = st.columns(5)

    # Cálculos rápidos
    total_partidas = len(df_filtrado)
    media_gols = df_filtrado['totalgoals_ft'].mean().round(2)
    jogos_over_2_5 = df_filtrado[df_filtrado['totalgoals_ft'] > 2.5]
    perc_over_2_5 = len(jogos_over_2_5) / total_partidas * 100 if total_partidas else 0
    media_escanteios = df_filtrado['totalcorners_ft'].mean().round(1)
    
    # Ambas Marcam
    jogos_btts_sim = df_filtrado[df_filtrado['AmbasMarcam'] == 'Sim']
    perc_btts_sim = len(jogos_btts_sim) / total_partidas * 100 if total_partidas else 0

    # Exibição das métricas
    col1.metric("Partidas Analisadas", total_partidas)
    col2.metric("Média de Gols/Partida", media_gols)
    col3.metric("Jogos Over 2.5", f"{len(jogos_over_2_5)} ({perc_over_2_5:.1f}%)")
    col4.metric("Escanteios/Jogo", media_escanteios)
    col5.metric("Ambas Marcam", f"{len(jogos_btts_sim)} ({perc_btts_sim:.1f}%)")

    # 5.2) CRIAÇÃO DAS ABAS
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Desempenho",
        "📋 Estatísticas Detalhadas",
        "🔄 Evolução Temporal",
        "🤝 Ambas Marcam (BTTS)"
    ])
    
    # =============================
    # ABA 1 - DESEMPENHO
    # =============================
    with tab1:
        st.subheader("Análise de Desempenho")
        st.write("Nesta seção, você visualiza como os times se saíram em termos de gols e resultados finais.")
        
        col_a, col_b = st.columns([3, 2])
        
        # --- Gols por Partida (Barras) ---
        with col_a:
            fig_gols = px.bar(
                df_filtrado,
                x='match_date',
                y=['goals_h_ft', 'goals_a_ft'],
                title='Gols por Partida',
                labels={
                    'value': 'Gols',
                    'variable': 'Equipe',
                    'match_date': 'Data'
                },
                hover_data=['home', 'away'],  # exibe times no hover
                color_discrete_map={'goals_h_ft': '#2A9D8F', 'goals_a_ft': '#E76F51'}
            )
            fig_gols.update_layout(
                xaxis_title="Data",
                yaxis_title="Quantidade de Gols",
                hovermode="x unified"
            )
            st.plotly_chart(fig_gols, use_container_width=True)
        
        # --- Distribuição de Resultados (Pizza) ---
        with col_b:
            st.subheader("Distribuição de Resultados")
            resultado_counts = df_filtrado['Resultado'].value_counts()
            fig_resultados = px.pie(
                names=resultado_counts.index,
                values=resultado_counts.values,
                color=resultado_counts.index,
                color_discrete_map={
                    'Vitória Casa': '#2A9D8F',
                    'Empate': '#E9C46A',
                    'Vitória Fora': '#E76F51'
                },
                title='Distribuição de Resultados',
                hole=0.3  # transforma em "donut chart"
            )
            # Exibe porcentagem e rótulo dentro do gráfico
            fig_resultados.update_traces(
                textposition='inside',
                textinfo='percent+label'
            )
            fig_resultados.update_layout(showlegend=True)
            st.plotly_chart(fig_resultados, use_container_width=True)

    # =============================
    # ABA 2 - ESTATÍSTICAS DETALHADAS
    # =============================
    with tab2:
        st.subheader("🔍 Comparativo Detalhado")
        st.write("Compare métricas específicas dos times selecionados, tanto como mandantes quanto como visitantes.")
        
        col_left, col_right = st.columns(2)
        
        # --- Desempenho como Mandante ---
        with col_left:
            st.markdown("**🏠 Desempenho como Mandante**")
            home_stats = df_filtrado.groupby('home').agg({
                'totalgoals_ft': 'mean',
                'shots_h': 'mean',
                'corners_h_ft': 'mean'
            }).rename(columns={
                'totalgoals_ft': 'Média Gols',
                'shots_h': 'Chutes/Jogo',
                'corners_h_ft': 'Escanteios/Jogo'
            }).round(2)
            
            if selecionados:
                home_stats = home_stats.loc[home_stats.index.intersection(selecionados)]
            
            st.dataframe(
                home_stats.style
                .background_gradient(subset=['Média Gols'], cmap='Greens')
                .background_gradient(subset=['Chutes/Jogo'], cmap='Blues')
                .format("{:.2f}")
                .set_properties(**{'text-align': 'center'}),
                height=400
            )

        # --- Desempenho como Visitante ---
        with col_right:
            st.markdown("**✈️ Desempenho como Visitante**")
            away_stats = df_filtrado.groupby('away').agg({
                'totalgoals_ft': 'mean',
                'shots_a': 'mean',
                'corners_a_ft': 'mean'
            }).rename(columns={
                'totalgoals_ft': 'Média Gols',
                'shots_a': 'Chutes/Jogo',
                'corners_a_ft': 'Escanteios/Jogo'
            }).round(2)
            
            if selecionados:
                away_stats = away_stats.loc[away_stats.index.intersection(selecionados)]
            
            st.dataframe(
                away_stats.style
                .background_gradient(subset=['Média Gols'], cmap='Oranges')
                .format("{:.2f}")
                .set_properties(**{'text-align': 'center'}),
                height=400
            )

        st.markdown("---")
        st.subheader("📌 Comparação Direta de Desempenho (Mandante x Visitante)")
        st.write("Selecione **2 times** na barra lateral para visualizar um comparativo lado a lado das principais métricas.")

        # Comparação entre 2 times (Mandante vs. Visitante)
        if len(selecionados) == 2:
            try:
                times_selecionados = selecionados
                
                # Estatísticas como mandante
                home_comp = (
                    df_filtrado[df_filtrado['home'].isin(times_selecionados)]
                    .groupby('home')
                    .agg({
                        'totalgoals_ft': 'mean',
                        'shots_h': 'mean',
                        'corners_h_ft': 'mean'
                    })
                    .rename(columns={
                        'totalgoals_ft': 'TotalGoals_Home',
                        'shots_h': 'Shots_Home',
                        'corners_h_ft': 'Corners_Home'
                    })
                    .reindex(times_selecionados)
                    .fillna(0)
                )
                
                # Estatísticas como visitante
                away_comp = (
                    df_filtrado[df_filtrado['away'].isin(times_selecionados)]
                    .groupby('away')
                    .agg({
                        'totalgoals_ft': 'mean',
                        'shots_a': 'mean',
                        'corners_a_ft': 'mean'
                    })
                    .rename(columns={
                        'totalgoals_ft': 'TotalGoals_Away',
                        'shots_a': 'Shots_Away',
                        'corners_a_ft': 'Corners_Away'
                    })
                    .reindex(times_selecionados)
                    .fillna(0)
                )
                
                # Combina em um único DataFrame
                comparison_data = pd.concat([home_comp, away_comp], axis=1).reset_index()

                # Melt para formatação em gráfico
                comparison_data = comparison_data.melt(
                    id_vars='index', 
                    var_name='variable',
                    value_name='value'
                )
                
                # Separar estatística e tipo (Home/Away)
                comparison_data[['Estatística', 'Tipo']] = (
                    comparison_data['variable']
                    .str.split('_', n=1, expand=True)
                )
                
                fig_comp = px.bar(
                    comparison_data,
                    x='Estatística',
                    y='value',
                    color='index',
                    barmode='group',
                    facet_row='Tipo',
                    labels={'value': 'Valor Médio', 'index': 'Time'},
                    color_discrete_sequence=['#2A9D8F', '#E76F51'],
                    text_auto='.2f'
                )
                
                fig_comp.update_layout(
                    xaxis_title="Estatísticas",
                    hovermode="x unified",
                    showlegend=True,
                    height=600
                )
                # Remove legendas redundantes nos títulos
                fig_comp.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
                
                st.plotly_chart(fig_comp, use_container_width=True)
                
            except Exception as e:
                st.error(f"Erro na geração da comparação: {str(e)}")
        else:
            st.info("Selecione 2 times para ver a comparação direta.")

    # =============================
    # ABA 3 - EVOLUÇÃO TEMPORAL
    # =============================
    with tab3:
        st.subheader("Linha do Tempo de Desempenho")
        st.write("Acompanhe a evolução de gols e escanteios ao longo das datas selecionadas.")
        
        col_a, col_b = st.columns([3, 2])
        
        with col_a:
            # Evolução de gols (Linha)
            fig_goals_timeline = px.line(
                df_filtrado.sort_values('match_date'),
                x='match_date',
                y='totalgoals_ft',
                markers=True,
                title='Evolução de Gols Totais por Partida',
                labels={'totalgoals_ft': 'Gols', 'match_date': 'Data'},
                color_discrete_sequence=['#2A9D8F']
            )
            fig_goals_timeline.update_layout(
                height=400,
                xaxis_title="Data",
                yaxis_title="Total de Gols",
                hovermode="x unified"
            )
            
            # Linha de referência da média de gols
            avg_goals = df_filtrado['totalgoals_ft'].mean()
            fig_goals_timeline.add_hline(
                y=avg_goals,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Média = {avg_goals:.2f}",
                annotation_position="top left"
            )
            
            st.plotly_chart(fig_goals_timeline, use_container_width=True)
            
            # Escanteios por partida (Barras)
            fig_corners_timeline = px.bar(
                df_filtrado.sort_values('match_date'),
                x='match_date',
                y=['corners_h_ft', 'corners_a_ft'],
                title='Escanteios por Partida',
                labels={'value': 'Escanteios', 'variable': 'Equipe', 'match_date': 'Data'},
                color_discrete_map={'corners_h_ft': '#2A9D8F', 'corners_a_ft': '#E76F51'},
                barmode='group'
            )
            fig_corners_timeline.update_layout(
                height=400,
                xaxis_title="Data",
                yaxis_title="Total de Escanteios"
            )
            st.plotly_chart(fig_corners_timeline, use_container_width=True)
        
        # Últimos 10 Jogos
        with col_b:
            st.subheader("Últimos 10 Jogos")
            ultimos_jogos = df_filtrado.sort_values('match_date', ascending=False).head(10)[[
                'match_date', 'home', 'away', 'goals_h_ft', 'goals_a_ft', 'totalcorners_ft'
            ]]
            # Formatação de data
            ultimos_jogos['match_date'] = pd.to_datetime(ultimos_jogos['match_date']).dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                ultimos_jogos.style
                .format({'totalcorners_ft': '{:.0f} ⚪'})
                .background_gradient(subset=['goals_h_ft', 'goals_a_ft'], cmap='YlGnBu')
                .set_properties(**{
                    'text-align': 'center',
                    'min-width': '150px',
                    'white-space': 'nowrap'
                })
                .set_table_styles([{
                    'selector': 'table',
                    'props': [('height', '600px'), ('overflow-y', 'auto')]
                }]),
                height=600
            )

    # =============================
    # ABA 4 - AMBAS MARCAM (BTTS)
    # =============================
    with tab4:
        st.subheader("🤝 Análise de Ambas Marcam (BTTS)")
        st.write("Visualize quantos jogos tiveram gols de ambas as equipes e como isso evolui ao longo do tempo.")
        
        # Distribuição de jogos com e sem BTTS
        btts_counts = df_filtrado['AmbasMarcam'].value_counts()
        fig_btts = px.pie(
            names=btts_counts.index,
            values=btts_counts.values,
            color=btts_counts.index,
            color_discrete_map={'Sim': '#2A9D8F', 'Não': '#E76F51'},
            title="Distribuição de Jogos com Ambas Marcam (BTTS)",
            hole=0.3
        )
        fig_btts.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )
        st.plotly_chart(fig_btts, use_container_width=True)

        # Evolução temporal de BTTS
        df_btts_timeline = (
            df_filtrado
            .groupby(['match_date', 'AmbasMarcam'])
            .size()
            .reset_index(name='count')
            .sort_values('match_date')
        )
        fig_btts_timeline = px.bar(
            df_btts_timeline,
            x='match_date',
            y='count',
            color='AmbasMarcam',
            barmode='group',
            color_discrete_map={'Sim': '#2A9D8F', 'Não': '#E76F51'},
            title="Linha do Tempo de Ambas Marcam",
            labels={'match_date': 'Data', 'count': 'Quantidade de Jogos'}
        )
        fig_btts_timeline.update_layout(
            xaxis_title="Data",
            yaxis_title="Quantidade de Jogos",
            hovermode="x unified",
            height=400
        )
        st.plotly_chart(fig_btts_timeline, use_container_width=True)

else:
    st.warning("⚠️ Nenhum dado encontrado para os critérios selecionados ou o banco de dados está vazio.")

# =============================
# RODAPÉ
# =============================
st.markdown("---")
st.markdown(
    f"**Desenvolvido por Gui Santos** • Dados atualizados em: {datetime.today().strftime('%d/%m/%Y')}"
)

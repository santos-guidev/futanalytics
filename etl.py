import pandas as pd
import psycopg2
from psycopg2 import sql
import schedule
import time
import logging

# Configurar logging para acompanhar a execução
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Dicionário com os links Excel (raw GitHub)
data_sources = {
    "Argentina Primera División": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Argentina%20Primera%20Divisi%C3%B3n_2025.xlsx",
    "Austria Bundesliga": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Austria%20Bundesliga_20242025.xlsx",
    "Belgium Pro League": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Belgium%20Pro%20League_20242025.xlsx",
    "Bulgaria First League": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Bulgaria%20First%20League_20242025.xlsx",
    "Brasil Serie A - 2024": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Brazil%20Serie%20A_2024.xlsx",
    "Brasil Serie A": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Brazil%20Serie%20A_2025.xlsx",
    "Chile Primeira Division": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Chile%20Primera%20Divisi%C3%B3n_2025.xlsx",
    "Egypt Premier League": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Egypt%20Egyptian%20Premier%20League_20242025.xlsx",
    "England Championship": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/England%20Championship_20242025.xlsx",
    "England EFL League One": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/England%20EFL%20League%20One_20242025.xlsx",
    "England Premier League": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/England%20Premier%20League_20242025.xlsx",
    "France Ligue 1": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/France%20Ligue%201_20242025.xlsx",
    "France Ligue 2": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/France%20Ligue%202_20242025.xlsx",
    "Greece Super League": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Greece%20Super%20League_20242025.xlsx",
    "Germany 2. Bundesliga": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Germany%202.%20Bundesliga_20242025.xlsx",
    "Germany Bundesliga": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Germany%20Bundesliga_20242025.xlsx",
    "Italy Serie A": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Italy%20Serie%20A_20232024.xlsx",
    "Japan J1 League": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Japan%20J1%20League_2024.xlsx",
    "Netherlands Eerste Divisie": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Netherlands%20Eredivisie_20242025.xlsx",
    "Portugal Liga NOS": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Portugal%20Liga%20NOS_20242025.xlsx",
    "Portugal LigaPro": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Portugal%20LigaPro_20242025.xlsx",
    "Republic of Ireland Premier Division": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Republic%20of%20Ireland%20Premier%20Division_2025.xlsx",
    "Spain La Liga": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Spain%20La%20Liga_20242025.xlsx",
    "Turkey Süper Lig": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/Turkey%20S%C3%BCper%20Lig_20242025.xlsx",
    "USA MLS": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/USA%20MLS_2024.xlsx",
    "USA MLS": "https://github.com/futpythontrader/YouTube/raw/refs/heads/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2025)/USA%20MLS_2025.xlsx"
}

def atualizar_banco():
    # 1. Conexão com o PostgreSQL
    conn = psycopg2.connect(
        host="localhost",
        database="matches",
        user="postgres",
        password="1408",
        port="5432"
    )
    conn.autocommit = True  # para confirmar cada inserção automaticamente

    try:
        with conn.cursor() as cur:
            # 2. Criar a tabela se ela não existir
            create_table_query = """
            CREATE TABLE IF NOT EXISTS tabela_ligas (
                numero              SERIAL PRIMARY KEY,
                id_jogo             TEXT,
                league              TEXT,
                season              TEXT,
                match_date          DATE,
                rodada              INTEGER,
                home                TEXT,
                away                TEXT,
                goals_h_ht          INTEGER,
                goals_a_ht          INTEGER,
                totalgoals_ht       INTEGER,
                goals_h_ft          INTEGER,
                goals_a_ft          INTEGER,
                totalgoals_ft       INTEGER,
                goals_h_minutes     TEXT,
                goals_a_minutes     TEXT,
                odd_h_ht            NUMERIC(10,2),
                odd_d_ht            NUMERIC(10,2),
                odd_a_ht            NUMERIC(10,2),
                odd_over05_ht       NUMERIC(10,2),
                odd_under05_ht      NUMERIC(10,2),
                odd_over15_ht       NUMERIC(10,2),
                odd_under15_ht      NUMERIC(10,2),
                odd_over25_ht       NUMERIC(10,2),
                odd_under25_ht      NUMERIC(10,2),
                odd_h_ft            NUMERIC(10,2),
                odd_d_ft            NUMERIC(10,2),
                odd_a_ft            NUMERIC(10,2),
                odd_over05_ft       NUMERIC(10,2),
                odd_under05_ft      NUMERIC(10,2),
                odd_over15_ft       NUMERIC(10,2),
                odd_under15_ft      NUMERIC(10,2),
                odd_over25_ft       NUMERIC(10,2),
                odd_under25_ft      NUMERIC(10,2),
                odd_btts_yes        NUMERIC(10,2),
                odd_btts_no         NUMERIC(10,2),
                odd_dc_1x           NUMERIC(10,2),
                odd_dc_12           NUMERIC(10,2),
                odd_dc_x2           NUMERIC(10,2),
                ppg_home_pre        NUMERIC(10,2),
                ppg_away_pre        NUMERIC(10,2),
                ppg_home            NUMERIC(10,2),
                ppg_away            NUMERIC(10,2),
                xg_home_pre         NUMERIC(10,2),
                xg_away_pre         NUMERIC(10,2),
                xg_total_pre        NUMERIC(10,2),
                shotsontarget_h     INTEGER,
                shotsontarget_a     INTEGER,
                shotsofftarget_h    INTEGER,
                shotsofftarget_a    INTEGER,
                shots_h             INTEGER,
                shots_a             INTEGER,
                corners_h_ft        INTEGER,
                corners_a_ft        INTEGER,
                totalcorners_ft     INTEGER,
                odd_corners_h       NUMERIC(10,2),
                odd_corners_d       NUMERIC(10,2),
                odd_corners_a       NUMERIC(10,2),
                odd_corners_over75  NUMERIC(10,2),
                odd_corners_under75 NUMERIC(10,2),
                odd_corners_over85  NUMERIC(10,2),
                odd_corners_under85 NUMERIC(10,2),
                odd_corners_over95  NUMERIC(10,2),
                odd_corners_under95 NUMERIC(10,2),
                odd_corners_over105 NUMERIC(10,2),
                odd_corners_under105 NUMERIC(10,2),
                odd_corners_over115 NUMERIC(10,2),
                odd_corners_under115 NUMERIC(10,2)
            );
            """
            cur.execute(create_table_query)

        # 3. Processar cada liga e inserir os dados
        for liga, url_excel in data_sources.items():
            logging.info(f"Processando liga: {liga}")
            df = pd.read_excel(url_excel)
            # Renomear colunas, se necessário
            mapeamento_colunas = {
                "Nº": "numero",
                "Date": "match_date"
            }
            df.rename(columns=mapeamento_colunas, inplace=True)
            # Remover linhas com valores ausentes em 'Home' ou 'Away'
            df = df.dropna(subset=["Home", "Away"])

            with conn.cursor() as cur:
                # Caso queira limpar os dados anteriores, descomente a linha abaixo:
                # cur.execute("TRUNCATE TABLE tabela_ligas;")
                for index, row in df.iterrows():
                    insert_query = sql.SQL("""
                        INSERT INTO tabela_ligas (
                            id_jogo,
                            league,
                            season,
                            match_date,
                            rodada,
                            home,
                            away,
                            goals_h_ht,
                            goals_a_ht,
                            totalgoals_ht,
                            goals_h_ft,
                            goals_a_ft,
                            totalgoals_ft,
                            goals_h_minutes,
                            goals_a_minutes,
                            odd_h_ht,
                            odd_d_ht,
                            odd_a_ht,
                            odd_over05_ht,
                            odd_under05_ht,
                            odd_over15_ht,
                            odd_under15_ht,
                            odd_over25_ht,
                            odd_under25_ht,
                            odd_h_ft,
                            odd_d_ft,
                            odd_a_ft,
                            odd_over05_ft,
                            odd_under05_ft,
                            odd_over15_ft,
                            odd_under15_ft,
                            odd_over25_ft,
                            odd_under25_ft,
                            odd_btts_yes,
                            odd_btts_no,
                            odd_dc_1x,
                            odd_dc_12,
                            odd_dc_x2,
                            ppg_home_pre,
                            ppg_away_pre,
                            ppg_home,
                            ppg_away,
                            xg_home_pre,
                            xg_away_pre,
                            xg_total_pre,
                            shotsontarget_h,
                            shotsontarget_a,
                            shotsofftarget_h,
                            shotsofftarget_a,
                            shots_h,
                            shots_a,
                            corners_h_ft,
                            corners_a_ft,
                            totalcorners_ft,
                            odd_corners_h,
                            odd_corners_d,
                            odd_corners_a,
                            odd_corners_over75,
                            odd_corners_under75,
                            odd_corners_over85,
                            odd_corners_under85,
                            odd_corners_over95,
                            odd_corners_under95,
                            odd_corners_over105,
                            odd_corners_under105,
                            odd_corners_over115,
                            odd_corners_under115
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s
                        )
                    """)
                    data_tuple = (
                        row.get("Id_Jogo", None),
                        row.get("League", None),
                        row.get("Season", None),
                        row.get("match_date", None),
                        row.get("Rodada", None),
                        row.get("Home", None),
                        row.get("Away", None),
                        row.get("Goals_H_HT", None),
                        row.get("Goals_A_HT", None),
                        row.get("TotalGoals_HT", None),
                        row.get("Goals_H_FT", None),
                        row.get("Goals_A_FT", None),
                        row.get("TotalGoals_FT", None),
                        row.get("Goals_H_Minutes", None),
                        row.get("Goals_A_Minutes", None),
                        row.get("Odd_H_HT", None),
                        row.get("Odd_D_HT", None),
                        row.get("Odd_A_HT", None),
                        row.get("Odd_Over05_HT", None),
                        row.get("Odd_Under05_HT", None),
                        row.get("Odd_Over15_HT", None),
                        row.get("Odd_Under15_HT", None),
                        row.get("Odd_Over25_HT", None),
                        row.get("Odd_Under25_HT", None),
                        row.get("Odd_H_FT", None),
                        row.get("Odd_D_FT", None),
                        row.get("Odd_A_FT", None),
                        row.get("Odd_Over05_FT", None),
                        row.get("Odd_Under05_FT", None),
                        row.get("Odd_Over15_FT", None),
                        row.get("Odd_Under15_FT", None),
                        row.get("Odd_Over25_FT", None),
                        row.get("Odd_Under25_FT", None),
                        row.get("Odd_BTTS_Yes", None),
                        row.get("Odd_BTTS_No", None),
                        row.get("Odd_DC_1X", None),
                        row.get("Odd_DC_12", None),
                        row.get("Odd_DC_X2", None),
                        row.get("PPG_Home_Pre", None),
                        row.get("PPG_Away_Pre", None),
                        row.get("PPG_Home", None),
                        row.get("PPG_Away", None),
                        row.get("XG_Home_Pre", None),
                        row.get("XG_Away_Pre", None),
                        row.get("XG_Total_Pre", None),
                        row.get("ShotsOnTarget_H", None),
                        row.get("ShotsOnTarget_A", None),
                        row.get("ShotsOffTarget_H", None),
                        row.get("ShotsOffTarget_A", None),
                        row.get("Shots_H", None),
                        row.get("Shots_A", None),
                        row.get("Corners_H_FT", None),
                        row.get("Corners_A_FT", None),
                        row.get("TotalCorners_FT", None),
                        row.get("Odd_Corners_H", None),
                        row.get("Odd_Corners_D", None),
                        row.get("Odd_Corners_A", None),
                        row.get("Odd_Corners_Over75", None),
                        row.get("Odd_Corners_Under75", None),
                        row.get("Odd_Corners_Over85", None),
                        row.get("Odd_Corners_Under85", None),
                        row.get("Odd_Corners_Over95", None),
                        row.get("Odd_Corners_Under95", None),
                        row.get("Odd_Corners_Over105", None),
                        row.get("Odd_Corners_Under105", None),
                        row.get("Odd_Corners_Over115", None),
                        row.get("Odd_Corners_Under115", None)
                    )
                    cur.execute(insert_query, data_tuple)
            logging.info(f"Liga {liga} inserida com sucesso.")
        logging.info("Processo concluído!")
    except Exception as e:
        logging.error("Ocorreu um erro: %s", e)
    finally:
        conn.close()

# =============================
# AGENDAMENTO DA TAREFA
# =============================
if __name__ == "__main__":
    # Execução imediata para atualizar o banco ao iniciar
    atualizar_banco()
    logging.info("Atualização inicial concluída.")

    # Agendar para executar todos os dias às 15:00 e 22:00
    schedule.every().day.at("15:00").do(atualizar_banco)
    schedule.every().day.at("22:00").do(atualizar_banco)
    logging.info("Agendamento configurado para as 15:00 e 22:00.")

    # Loop de execução que verifica as tarefas pendentes a cada minuto
    while True:
        schedule.run_pending()
        time.sleep(60)

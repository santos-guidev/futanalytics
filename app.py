import streamlit as st

# CSS personalizado para manter a consistência visual
css = """
<style>
/* Fundo da aplicação */
.stApp {
    background-color: #0f0d09;
}

/* Títulos */
h1 {
    font-family: 'Arial', sans-serif;
    color: #333333;
    text-align: center;
    margin-top: 50px;
}

/* Texto introdutório */
.intro-text {
    font-family: 'Arial', sans-serif;
    color: #555555;
    text-align: center;
    font-size: 20px;
    margin-top: 20px;
}

/* Subtítulo ou mensagem adicional */
.sub-text {
    font-family: 'Arial', sans-serif;
    color: #777777;
    text-align: center;
    font-size: 16px;
    margin-top: 10px;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# Título principal
st.title("Bem-vindo ao Aplicativo de Análise de Futebol")

# Texto introdutório com instruções
st.markdown('<div class="intro-text">Sua fonte completa de análises, predições e estatísticas sobre futebol.</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">Utilize o menu à esquerda para navegar entre as seções: Dashboards, predições, estatísticas e atualizações automáticas.</div>', unsafe_allow_html=True)

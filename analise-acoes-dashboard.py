import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Função para tratar valores em reais ou percentuais
def formatar_valor(valor, tipo="real"):
    if pd.isna(valor):
        return "N/A"
    if tipo == "real":
        return f"R$ {valor:,.2f}".replace(",", ".").replace(".", ",", 1)
    if tipo == "percentual":
        return f"{valor * 100:.2f}%"
    return valor

# Função para obter dados de múltiplos ativos
def obter_dados_tickers(tickers, start_date, end_date):
    dados = {}
    erros = []
    for ticker in tickers:
        try:
            stock_data = yf.Ticker(ticker)
            
            # Tentar carregar histórico para o intervalo especificado
            history = stock_data.history(start=start_date, end=end_date, interval="1d", timeout=60)
            
            # Verificar se o histórico está vazio
            if history.empty:
                erros.append(f"{ticker}: Nenhum dado encontrado no intervalo especificado.")
            else:
                dados[ticker] = {
                    "info": stock_data.info,
                    "history": history,
                }
        except Exception as e:
            erros.append(f"{ticker}: Erro ao buscar dados ({str(e)}).")
    return dados, erros

# Função para criar gráfico com linhas horizontais e rótulos
def criar_grafico_com_linhas(history, ticker):
    if history.empty:
        return None

    # Determinar valores máximo, mínimo e último fechamento
    max_valor = history["Close"].max()
    min_valor = history["Close"].min()
    ultimo_fechamento = history["Close"].iloc[-1]
    fechamento_anterior = history["Close"].iloc[-2] if len(history) > 1 else ultimo_fechamento

    # Determinar a cor do rótulo do último fechamento
    cor_ultimo = "green" if ultimo_fechamento > fechamento_anterior else "red"

    # Criar o gráfico
    fig = go.Figure()

    # Linha do preço de fechamento
    fig.add_trace(go.Scatter(
        x=history.index,
        y=history["Close"],
        mode="lines",
        name="Fechamento",
        line=dict(color="blue")
    ))

    # Linha horizontal do valor máximo
    fig.add_hline(
        y=max_valor,
        line_color="green",
        annotation_text=f"Máximo: {formatar_valor(max_valor)}",
        annotation_position="top right",
        annotation_font_size=12,
        annotation_font_color="green",
        line_width=2
    )

    # Linha horizontal do valor mínimo
    fig.add_hline(
        y=min_valor,
        line_color="red",
        annotation_text=f"Mínimo: {formatar_valor(min_valor)}",
        annotation_position="bottom right",
        annotation_font_size=12,
        annotation_font_color="red",
        line_width=2
    )

    # Adicionar rótulo para o último fechamento
    fig.add_trace(go.Scatter(
        x=[history.index[-1]],
        y=[ultimo_fechamento],
        mode="markers+text",
        name="Último Fechamento",
        marker=dict(color=cor_ultimo, size=10),
        text=[f"{formatar_valor(ultimo_fechamento)}"],
        textposition="top center",
        textfont=dict(color=cor_ultimo, size=12)
    ))

    # Configuração do layout
    fig.update_layout(
        title=f"Histórico de Preços - {ticker}",
        xaxis_title="Data",
        yaxis_title="Preço de Fechamento",
        height=500,
    )

    return fig

# Função para criar gráfico de radar
def criar_grafico_radar(valuation, nome_ativo):
    categorias = list(valuation.keys())
    valores = list(valuation.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill='toself',
        name=nome_ativo
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=True,
        title=f"Gráfico de Radar - {nome_ativo}"
    )
    return fig

# Layout do Streamlit
st.title("Dashboard Completo de Análise de Ações")
st.sidebar.title("Configurações")

# Entrada dos tickers pelo usuário
tickers = st.sidebar.text_input("Digite os Tickers separados por vírgula (ex: AAPL, PETR4.SA)", "PETR4.SA, VALE3.SA")
tickers = [ticker.strip() for ticker in tickers.split(",")]

# Opções de seleção de período
st.sidebar.subheader("Selecione o período de análise:")
tipo_periodo = st.sidebar.radio(
    "Escolha o método de seleção de período:",
    ("Atalhos Rápidos", "Personalizado")
)

# Configuração do intervalo de tempo
if tipo_periodo == "Atalhos Rápidos":
    intervalo = st.sidebar.selectbox(
        "Escolha o intervalo de tempo:",
        ["7 dias", "30 dias", "90 dias", "12 meses"]
    )
    hoje = datetime.today()
    if intervalo == "7 dias":
        start_date, end_date = hoje - timedelta(days=7), hoje
    elif intervalo == "30 dias":
        start_date, end_date = hoje - timedelta(days=30), hoje
    elif intervalo == "90 dias":
        start_date, end_date = hoje - timedelta(days=90), hoje
    else:  # 12 meses
        start_date, end_date = hoje - timedelta(days=365), hoje
else:
    start_date = st.sidebar.date_input("Data de Início", datetime.today() - timedelta(days=30))
    end_date = st.sidebar.date_input("Data Final", datetime.today())
    if start_date > end_date:
        st.sidebar.error("A data de início deve ser anterior à data final.")

# Botão para buscar dados
if st.sidebar.button("Analisar"):
    with st.spinner("Obtendo dados..."):
        dados, erros = obter_dados_tickers(tickers, start_date, end_date)

        # Exibição dos erros
        if erros:
            st.warning("Erros encontrados nos seguintes tickers:")
            for erro in erros:
                st.write(erro)

        # Criando abas para cada ativo
        if dados:
            abas = st.tabs([ticker for ticker in dados.keys()])
            for i, (ticker, data) in enumerate(dados.items()):
                with abas[i]:
                    info = data["info"]
                    history = data["history"]

                    # Informações do ativo
                    nome_ativo = info.get("longName", ticker)
                    logotipo = info.get("logo_url")

                    st.header(f"{ticker} - {nome_ativo}")
                    if logotipo:
                        st.image(logotipo, width=100)
                    else:
                        st.write(f"Logotipo não disponível para {nome_ativo}")

                    # Gráfico de preços
                    st.subheader("Gráfico de Preço")
                    if not history.empty:
                        fig = criar_grafico_com_linhas(history, ticker)
                        st.plotly_chart(fig)
                    else:
                        st.warning(f"Nenhum dado histórico disponível para {ticker}.")

                    # Análise Fundamentalista
                    st.subheader("Análise Fundamentalista")
                    valuation = {
                        "P/L (Preço/Lucro)": info.get("trailingPE", 0),
                        "P/L Projetado": info.get("forwardPE", 0),
                        "P/VP": info.get("priceToBook", 0),
                        "Dividend Yield (%)": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
                        "Payout Ratio (%)": info.get("payoutRatio", 0) * 100 if info.get("payoutRatio") else 0,
                    }
                    st.write(valuation)

                    # Gráfico de Radar
                    st.subheader("Gráfico de Radar")
                    fig_radar = criar_grafico_radar(valuation, nome_ativo)
                    st.plotly_chart(fig_radar)

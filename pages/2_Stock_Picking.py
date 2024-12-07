# pages/2_Recherche_Ticker.py

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go

def main():
    if 'wishlist' not in st.session_state:
        st.session_state.wishlist = []
    
    #CSS pour ajuster la largeur de la zone de contenu
    st.markdown(
        """
        <style>
        div.block-container {
            max-width: 90%;
            margin: auto;
            padding: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    df = pd.read_csv("/home/onyxia/work/Pi.Squared.Trading/Indices boursiers/CACSNPDAXRUSSEL.csv")
    
    st.title("Stock picking")

    #Sélection de l'indice
    indices = ["Tous les indices"] + df["Ind"].unique().tolist()
    selected_index = st.selectbox("Choisissez un indice :", indices)

    #Filtrer le dataframe en fonction de l'indice sélectionné
    if selected_index == "Tous les indices":
        filtered_df = df
    else:
        filtered_df = df[df["Ind"] == selected_index]

    #Sélection entreprise
    companies = filtered_df["Company"].tolist()
    selected_company = st.selectbox("Choisissez une entreprise :", companies)

    #Afficher le ticker associé
    ticker = filtered_df[filtered_df["Company"] == selected_company]["Ticker"].values[0]
    st.write(f"Le ticker de l'entreprise sélectionnée ({selected_company}) est : **{ticker}**")
    
    period_options = ['1 mois', '3 mois', '6 mois', '1 an', '2 ans', '5 ans', 'Max']
    period_mapping = {
            '1 mois': '1mo',
            '3 mois': '3mo',
            '6 mois': '6mo',
            '1 an': '1y',
            '2 ans': '2y',
            '5 ans': '5y',
            'Max': 'max'
        }
    period_choice = st.selectbox("Sélectionnez la période :", period_options, index=3)
    period = period_mapping[period_choice]
    
    if ticker and ticker != "Ticker non trouvé":
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
    
            info = stock.info
    
            if not data.empty:
                #Informations actions
                st.subheader(f"Informations sur {ticker.upper()}")
    
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    st.metric("Entreprise", info.get('longName', 'N/A'))
                    st.metric("Secteur", info.get('sector', 'N/A'))
                with col2:
                    st.metric("Industrie", info.get('industry', 'N/A'))
                    market_cap = info.get('marketCap', None)

                    if market_cap:
                        if market_cap >= 1e12:
                            market_cap_formatted = f"{market_cap / 1e12:.2f} T"
                        elif market_cap >= 1e9:
                            market_cap_formatted = f"{market_cap / 1e9:.2f} B"
                        elif market_cap >= 1e6:
                            market_cap_formatted = f"{market_cap / 1e6:.2f} M"
                        else:
                            market_cap_formatted = f"${market_cap:,}"
                        st.metric("Capitalisation Boursière", f"${market_cap_formatted}")
                    else:
                        st.metric("Capitalisation Boursière", 'N/A')
                with col3:
                    trailing_pe = info.get('trailingPE', 'N/A')
                    st.metric("Ratio P/E", f"{trailing_pe}" if trailing_pe != 'N/A' else 'N/A')
                    dividend_yield = info.get('dividendYield', None)
                    if dividend_yield is not None:
                        st.metric("Rendement Dividende", f"{dividend_yield * 100:.2f}%")
                    else:
                        st.metric("Rendement Dividende", 'N/A')
                with col4:

                    #Bouton wishlit
                    if ticker.upper() in st.session_state.wishlist:
                        wishlist_label = "★"  
                        wishlist_action = "retirer"
                        tooltip = "Retirer de la Wishlist"
                    else:
                        wishlist_label = "☆"  
                        wishlist_action = "ajouter"
                        tooltip = "Ajouter à la Wishlist"
    
                    if st.button(wishlist_label, key=f"wishlist_{ticker.upper()}"):
                        if ticker.upper() in st.session_state.wishlist:
                            st.session_state.wishlist.remove(ticker.upper())
                            st.success(f"{ticker.upper()} a été retiré de votre wishlist.")
                        else:
                            st.session_state.wishlist.append(ticker.upper())
                            st.success(f"{ticker.upper()} a été ajouté à votre wishlist.")
    
                #Résumé de l'entreprise
                st.markdown("### Résumé de l'entreprise")
                summary = info.get('longBusinessSummary', 'Aucun résumé disponible.')
                justified_summary = f"""
                <div style='text-align: justify; text-justify: inter-word;'>
                    {summary}
                </div>
                """
                st.markdown(justified_summary, unsafe_allow_html=True)
    
                fig = go.Figure(data=[go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    increasing_line_color='#2e7d32',  #Vert foncé
                    decreasing_line_color='#c62828'  #Rouge foncé
                )])
    
                fig.update_layout(
                    title=f"Cours de l'action {ticker.upper()} sur {period_choice}",
                    xaxis_title='Date',
                    yaxis_title='Prix',
                    width=800,   
                    height=700,
                    xaxis_rangeslider_visible=True,
                    template='plotly_white',
                    bargap=0
                )

                st.plotly_chart(fig, use_container_width=True)
    
                st.subheader("Ratios Financiers")
    
                #Ratios et leurs descriptions
                ratios = {
                    "P/E Ratio": {
                        "value": info.get('trailingPE', 'N/A'),
                        "description": "Price to Earnings Ratio. Indique combien les investisseurs sont prêts à payer par rapport aux bénéfices actuels."
                    },
                    "ROE": {
                        "value": f"{info.get('returnOnEquity', 'N/A')*100:.2f}%" if info.get('returnOnEquity') else 'N/A',
                        "description": "Return on Equity. Mesure la rentabilité en fonction des capitaux propres."
                    },
                    "PEG Ratio": {
                        "value": info.get('pegRatio', 'N/A'),
                        "description": "Price/Earnings to Growth Ratio. Évalue le P/E ratio en fonction de la croissance des bénéfices."
                    },
                    "Debt/Equity": {
                        "value": info.get('debtToEquity', 'N/A'),
                        "description": "Debt to Equity Ratio. Compare la dette totale aux capitaux propres."
                    }
                }
    
                # Utiliser st.columns pour aligner les métriques
                ratio_cols = st.columns(len(ratios))
                for col, (ratio, details) in zip(ratio_cols, ratios.items()):
                    with col:
                        st.metric(label=ratio, value=details["value"])
                        st.caption(details["description"])
    
                # ACTUALITES À VOIR SI L'ON INTERÈGE OU NON
                # st.markdown("### Actualités Récentes")
                # news = stock.news
                # if news:
                #     for article in news[:5]:  # Afficher les 5 dernières actualités
                #         title = article.get('title', 'Sans Titre')
                #         link = article.get('link', '#')
                #         summary = article.get('summary', 'Aucun résumé disponible.')
                #         st.markdown(f"**[{title}]({link})**")
                #         st.write(summary)
                #         st.write("---")
                # else:
                #     st.write("Aucune actualité disponible pour cette action.")
    
            else:
                st.error("Les données pour ce ticker ne sont pas disponibles.")
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")

if __name__ == "__main__":
    main()

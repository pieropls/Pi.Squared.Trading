#Portfolio_visualizer.py

import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu  # Assurez-vous que streamlit_option_menu est installé
import yfinance as yf
import plotly.graph_objs as go
import plotly.express as px
import numpy as np  # type: ignore
from utils.graph_utils import plot_performance, plot_pie  # type: ignore


def get_company_name(ticker):
    try:
        company = yf.Ticker(ticker).info.get('longName', 'N/A')
    except:
        company = 'N/A'
    return company

# Fonction pour calculer la performance historique du portefeuille
def calculate_portfolio_performance(tickers, weights, period='1y'):
    data = yf.download(tickers, period=period)['Adj Close']
    if isinstance(data, pd.Series):  
        data = data.to_frame()  # CAS OU IL Y A UN SEUL TICKER 
    returns = data.pct_change().dropna()
    weighted_returns = returns.multiply(weights, axis=1)
    portfolio_returns = weighted_returns.sum(axis=1)
    portfolio_cumulative = (1 + portfolio_returns).cumprod()
    return portfolio_cumulative, portfolio_returns

# Initialisation des listes dans session_state
if 'tickers' not in st.session_state:
    st.session_state.tickers = ['']
if 'weights' not in st.session_state:
    st.session_state.weights = [0.0]
if 'wishlist' not in st.session_state:
    st.session_state.wishlist = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0  # Initialiser current_index pour la page d'accueil

# Fonction pour ajouter un actif
def add_asset():
    st.session_state.tickers.append('')
    st.session_state.weights.append(0.0)

# Fonction pour supprimer un actif
def remove_asset(index):
    del st.session_state.tickers[index]
    del st.session_state.weights[index]

def local_css(css_text):
    st.markdown(f'<style>{css_text}</style>', unsafe_allow_html=True)

# Styles CSS améliorés avec animations et effets de parallaxe
css = """
/* Votre CSS ici... */
"""
local_css(css)

# Inclure la bibliothèque AOS pour les animations
st.markdown("""
<link href="https://unpkg.com/aos@2.3.4/dist/aos.css" rel="stylesheet">
<script src="https://unpkg.com/aos@2.3.4/dist/aos.js"></script>
<script>
  AOS.init({
    duration: 1200,
  });
</script>
""", unsafe_allow_html=True)


df_companies = pd.read_csv("/home/onyxia/work/Pi.Squared.Trading/Indices boursiers/CACSNPDAXRUSSEL.csv")

def main():
    st.title("Portfolio visualizer")
    st.write("Veuillez entrer les actifs que vous souhaitez inclure dans votre portefeuille ainsi que les poids associés.")

    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = pd.DataFrame(columns=['Actions', 'Nom de l\'Entreprise', 'Poids (%)'])

    #Filtre d'indice dans la page principale
    st.header("Filtrer par Indice")
    indices = df_companies['Ind'].unique().tolist()
    selected_indices = st.multiselect(
        "Choisissez un ou plusieurs indices",
        options=indices,
        default=indices 
    )

    if selected_indices:
        filtered_companies = df_companies[df_companies['Ind'].isin(selected_indices)]
    else:
        filtered_companies = df_companies.copy()

    if filtered_companies.empty:
        st.warning("Aucune entreprise trouvée pour les indices sélectionnés.")
    
    #Fonction callback pour définir l'index à supprimer
    def remove_asset_callback(index):
        if 0 <= index < len(st.session_state.tickers):
            remove_asset(index)

    #Fonction pour ajouter un actif
    def add_asset_callback():
        add_asset()

    #Bouton pour ajouter un actif
    st.button("➕ Ajouter un actif", on_click=add_asset_callback)

    for i in range(len(st.session_state.tickers)):
        cols = st.columns([2, 2, 1])
        with cols[0]:
            #Menu déroulant pour sélectionner une entreprise
            selected_company = st.selectbox(
                f"Entreprise {i+1}",
                options=[""] + filtered_companies["Company"].tolist(),
                key=f"company_{i}",
                index=0 
            )

            if selected_company:
                ticker = filtered_companies.loc[filtered_companies["Company"] == selected_company, "Ticker"].values[0]
                st.session_state.tickers[i] = ticker
            else:
                st.session_state.tickers[i] = ""  

        with cols[1]:
            weight = st.number_input(
                f"Poids {i+1} (%)",
                key=f"weight_{i}",
                min_value=0.0,
                max_value=100.0,
                value=st.session_state.weights[i],
                step=0.1
            )
            st.session_state.weights[i] = weight

        with cols[2]:
            st.button("🗑️ Supprimer", key=f"remove_{i}", on_click=remove_asset_callback, args=(i,))

    st.write("### Ajouter des actions depuis votre Wishlist")
    if st.session_state.wishlist:
        wishlist_selection = st.selectbox("Sélectionnez une action de votre wishlist :", st.session_state.wishlist, key="wishlist_select")

        def add_from_wishlist():
            selected_ticker = wishlist_selection.upper()
            if selected_ticker in st.session_state.tickers:
                st.warning(f"L'action **{selected_ticker}** est déjà dans votre portefeuille.")
            else:
                st.session_state.tickers.append(selected_ticker)
                st.session_state.weights.append(0.0)
                st.success(f"L'action **{selected_ticker}** a été ajoutée à votre portefeuille. Veuillez définir son poids.")

        st.button("➕ Ajouter depuis la Wishlist", on_click=add_from_wishlist)
    else:
        st.info("Votre wishlist est vide. Allez dans la section **Stock picking** pour ajouter des actions à votre wishlist.")

    #Affichage en temps réel de la somme des poids
    total_weight = sum(st.session_state.weights)
    st.markdown(f"**Poids Total Actuel : {total_weight:.2f}%**")
    if not np.isclose(total_weight, 100.0):
        st.warning("⚠️ La somme des poids doit être égale à 100%.")
    else:
        st.success("✅ La somme des poids est égale à 100%.")

    #Bouton validation portefeuille
    if st.button("✅ Valider le Portefeuille"):
        tickers = []
        weights = []
        for i in range(len(st.session_state.tickers)):
            ticker = st.session_state.tickers[i].strip().upper()
            weight = st.session_state.weights[i]  
            if ticker:
                tickers.append(ticker)
                weights.append(weight)

        st.session_state.tickers = tickers
        st.session_state.weights = weights

        duplicates = set([ticker for ticker in tickers if tickers.count(ticker) > 1])
        if duplicates:
            st.error(f"Les tickers suivants sont présents plusieurs fois dans votre portefeuille : {', '.join(duplicates)}. Veuillez modifier leurs poids ou changer de ticker.")
            st.stop()

        #Dataframe du portefeuille
        df = pd.DataFrame({
            'Ticker': tickers,
            'Poids (%)': weights
        })

        total_weight = df['Poids (%)'].sum()
        if total_weight == 0:
            st.error("La somme des poids est égale à 0%. Veuillez entrer des poids valides.")
            st.stop()

        try:
            df['Poids (%)'] = df['Poids (%)'].astype(float)
        except ValueError:
            st.error("Veuillez entrer des valeurs numériques valides pour les poids.")
            st.stop()

        #Vérification poids positifs
        if (df['Poids (%)'] <= 0).any():
            st.error("Tous les poids doivent être strictement positifs.")
            st.stop()
        else:
            #Vérification somme à 100%
            if not np.isclose(total_weight, 100.0):
                st.warning(f"⚠️ La somme des poids est de {total_weight:.2f}%. Elle doit être égale à 100%.")
                normalize = st.checkbox("Voulez-vous normaliser les poids automatiquement ?", key="normalize_validation")
                if normalize:
                    df['Poids (%)'] = df['Poids (%)'] * 100 / total_weight
                    total_weight = df['Poids (%)'].sum()
                    st.success("Les poids ont été normalisés.")
            #else:
                #st.success("✅ La somme des poids est égale à 100%.")

        valid_tickers = []
        invalid_tickers = []
        company_names = []

        for ticker in df['Ticker']:
            if ticker:  #
                try:
                    company_name = get_company_name(ticker)
                    if company_name != 'N/A':
                        valid_tickers.append(ticker.upper())
                        company_names.append(company_name)
                    else:
                        invalid_tickers.append(ticker)
                except Exception as e:
                    invalid_tickers.append(ticker)
                    st.error(f"Erreur lors de la vérification du ticker {ticker}: {e}")

        if invalid_tickers:
            st.error(f"Les tickers suivants ne sont pas valides ou les données ne sont pas disponibles : {', '.join(invalid_tickers)}")
            st.stop()
        elif not valid_tickers:
            st.error("Aucun ticker valide n'a été fourni.")
            st.stop()
        else:
            portfolio = {
                'Actions': valid_tickers,
                'Nom de l\'Entreprise': company_names,
                'Poids (%)': [df.loc[df['Ticker'] == ticker, 'Poids (%)'].values[0] for ticker in valid_tickers]
            }
            portfolio_df = pd.DataFrame(portfolio)
            portfolio_df.index = range(1, 1 + len(valid_tickers))

            #Métriques du portefeuilles
            total_weight = portfolio_df['Poids (%)'].sum()
            average_weight = portfolio_df['Poids (%)'].mean()
            max_weight = portfolio_df['Poids (%)'].max()
            min_weight = portfolio_df['Poids (%)'].min()

            #Rendement attendu annualisée
            portfolio_cumulative, portfolio_returns = calculate_portfolio_performance(
                valid_tickers,
                np.array(portfolio_df['Poids (%)'].tolist()) / 100,
                period='1y'
            )
            expected_return = portfolio_returns.mean() * 252  # 252 jours de bourse par an

            #Volatilité annualisée
            volatility = portfolio_returns.std() * np.sqrt(252)

            #Ratio de Sharpe (avec un taux sans risque de 2%)
            risk_free_rate = 0.02
            sharpe_ratio = (expected_return - risk_free_rate) / volatility if volatility != 0 else np.nan

            st.write("### Votre portefeuille :")
            st.write("#### Tableau Récapitulatif")

            fig_table = go.Figure(data=[go.Table(
                header=dict(
                    values=list(portfolio_df.columns),
                    fill_color='#0611ab',
                    font=dict(color='white', size=14),
                    align='center',
                    height=40
                ),
                cells=dict(
                    values=[portfolio_df[col] for col in portfolio_df.columns],
                    fill_color=['#f8f9fa']*len(portfolio_df),
                    font=dict(color='black', size=12),
                    align='center',
                    height=30
                )
            )])
            fig_table.update_layout(
                width=600,
                height=200,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig_table, use_container_width=True, key="visualizer_portfolio_table")

            #Statistiques du portefeuille
            st.write("### Statistiques du Portefeuille")
            metrics_labels = [
                "Poids Total", "Poids Moyen", "Poids Maximum", "Poids Minimum",
                "Rendement Attendu", "Volatilité", "Ratio de Sharpe"
            ]
            metrics_values = [
                f"{total_weight:.2f}%", f"{average_weight:.2f}%", f"{max_weight:.2f}%", f"{min_weight:.2f}%",
                f"{expected_return*100:.2f}%", f"{volatility*100:.2f}%", f"{sharpe_ratio:.2f}"
            ]
            metrics_descriptions = [
                "La somme des poids doit être de 100%.", "", "", "",
                "Rendement attendu annualisé.", "Volatilité annualisée du portefeuille.",
                "Ratio de Sharpe (rendement ajusté au risque)."
            ]

            num_metrics = len(metrics_labels)
            cols = st.columns(num_metrics)

            for col, label, value, description in zip(cols, metrics_labels, metrics_values, metrics_descriptions):
                with col:
                    st.metric(label, value)
                    if description:
                        st.caption(description)

            graph_cols = st.columns(2)

            with graph_cols[0]:
                    st.write("### Performance Historique du Portefeuille")
                    plot_performance(portfolio_cumulative)  #Module des fonctions graphiques

            with graph_cols[1]:
                    st.write("### Répartition des Poids dans le Portefeuille")
                    portfolio_df_sorted = portfolio_df.sort_values(by='Poids (%)', ascending=False)
                    plot_pie(portfolio_df_sorted)  #Module des fonctions graphiques

            #On stocke le portefeuille pour la partie opti
            st.session_state['portfolio'] = portfolio_df
            st.success("✅ Le portefeuille a été enregistré pour une utilisation ultérieure.")

if __name__ == "__main__":
    main()
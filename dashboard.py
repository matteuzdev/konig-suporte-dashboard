import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página de Elite - Identidade OFFICECOM
st.set_page_config(page_title="OFFICECOM | Suporte iGaming Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- PALETA OFFICECOM ---
# Primária: #EA465E (Vermelho/Rosa)
# Secundária: #20435C (Azul Marinho)
# Background: #F4F7F9 (Cinza Claro/Azul)

# --- SISTEMA DE SEGURANÇA ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True

    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown("<h1 style='text-align: center; color: #20435C;'>OFFICECOM</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Painel de Gestão de Suporte N2</p>", unsafe_allow_html=True)
        password = st.text_input("Senha de acesso:", type="password")
        if st.button("ENTRAR NO SISTEMA"):
            if password == "suporten2":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta.")
    return False

if not check_password():
    st.stop()

# --- INÍCIO DO DASHBOARD ---

SHEET_URL = "https://docs.google.com/spreadsheets/d/1LWuWM2iEPz-3f3qvXaaokiNrnLafjPP43LIAKz5tcoA/export?format=csv&gid=1321610989"

# CSS Personalizado OFFICECOM
st.markdown("""
    <style>
    /* Estilo Geral */
    .main { background-color: #F4F7F9; }
    .stMetric { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #E0E4E8; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    [data-testid="stMetricValue"] { color: #20435C !important; font-weight: bold; }
    [data-testid="stSidebar"] { background-color: #20435C; border-right: 1px solid #1a364a; }
    [data-testid="stSidebar"] * { color: white !important; }
    
    h1, h2, h3 { color: #20435C !important; font-family: 'Inter', sans-serif; }
    
    /* Botão Customizado Officecom */
    .stButton>button { 
        background-color: #EA465E !important; 
        color: white !important; 
        border-radius: 8px !important; 
        font-weight: bold !important; 
        border: none !important;
        padding: 10px !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #d63f56 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(234, 70, 94, 0.3);
    }
    
    /* Tabela Officecom */
    table { border-radius: 10px; overflow: hidden; }
    th { background-color: #20435C !important; color: white !important; text-align: left !important; }
    td { color: #444 !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL, encoding="utf-8")
        df.columns = ['ID', 'Titulo', 'Solicitante', 'Criacao', 'Status', 'Casas', 'Atualizacao', 'Leitura', 'Mesclado', 'Link']
        df['Criacao'] = pd.to_datetime(df['Criacao'], format='%d/%m/%Y', errors='coerce')
        df['Status'] = df['Status'].fillna('Sem Status')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>OFFICECOM</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 0.8rem;'>Business Creating Business</p>", unsafe_allow_html=True)
    if st.button("🚪 LOGOUT"):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown("---")
    if st.button("🔄 ATUALIZAR DADOS"):
        st.cache_data.clear()
        st.toast("Dados sincronizados!", icon="✅")
        st.rerun()
    st.markdown("---")
    st.subheader("Filtros")
    df_raw = load_data()
    if not df_raw.empty:
        status_list = ['Todos'] + sorted(df_raw['Status'].unique().tolist())
        selected_status = st.selectbox("Status", status_list)
        casa_list = ['Todas'] + sorted(df_raw['Casas'].str.split(', ').explode().unique().tolist())
        selected_casa = st.selectbox("Casa/Operadora", casa_list)

if 'filtros' not in st.session_state:
    st.session_state.filtros = {'Status': None, 'Casas': None}

if not df_raw.empty:
    df = df_raw.copy()
    if selected_status != 'Todos': df = df[df['Status'] == selected_status]
    if selected_casa != 'Todas': df = df[df['Casas'].str.contains(selected_casa, na=False)]
    if st.session_state.filtros['Status']: df = df[df['Status'] == st.session_state.filtros['Status']]
    if st.session_state.filtros['Casas']: df = df[df['Casas'].str.contains(st.session_state.filtros['Casas'], na=False)]

    # --- MÉTRICAS ---
    st.title("🛡️ Dashboard de Suporte N2")
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Total de Tickets", len(df))
    with m2: 
        dev = len(df[df['Status'] == 'Devolutiva'])
        st.metric("Devolutivas", dev, delta=f"{(dev/len(df)*100):.1f}%" if len(df)>0 else "0%")
    with m3: st.metric("Com Fornecedor", len(df[df['Status'].str.contains('Fornecedor', na=False)]))
    with m4:
        novos = len(df[df['Criacao'] >= pd.Timestamp.now().normalize() - pd.Timedelta(days=7)])
        st.metric("Novos (7 dias)", novos)

    st.markdown("---")

    # --- GRÁFICOS ---
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Distribuição por Status")
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Quantidade']
        fig_status = px.pie(status_counts, values='Quantidade', names='Status', hole=.4, color_discrete_sequence=['#EA465E', '#20435C', '#6C757D', '#ADB5BD'])
        fig_status.update_layout(margin=dict(t=30, b=0, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        sel_status = st.plotly_chart(fig_status, use_container_width=True, on_select="rerun")
        if sel_status and 'selection' in sel_status and sel_status['selection']['points']:
            st.session_state.filtros['Status'] = sel_status['selection']['points'][0]['label']
            st.rerun()

    with c2:
        st.subheader("Tickets por Casa")
        df_casas = df.assign(Casas=df['Casas'].str.split(', ')).explode('Casas')
        casa_counts = df_casas['Casas'].value_counts().reset_index().head(10)
        casa_counts.columns = ['Casa', 'Tickets']
        fig_casas = px.bar(casa_counts, x='Tickets', y='Casa', orientation='h', color_discrete_sequence=['#20435C'])
        fig_casas.update_layout(margin=dict(t=30, b=0, l=0, r=0))
        sel_casa = st.plotly_chart(fig_casas, use_container_width=True, on_select="rerun")
        if sel_casa and 'selection' in sel_casa and sel_casa['selection']['points']:
            st.session_state.filtros['Casas'] = sel_casa['selection']['points'][0]['y']
            st.rerun()

    # --- TABELA ---
    st.markdown("---")
    st.subheader("📋 Lista de Tickets")
    df_display = df.copy()
    df_display['Link'] = df_display['Link'].apply(lambda x: f'<a href="{x}" target="_blank" style="color: #EA465E; font-weight: bold;">Abrir</a>')
    st.write(df_display[['ID', 'Criacao', 'Solicitante', 'Status', 'Casas', 'Titulo', 'Link']].to_html(escape=False, index=False), unsafe_allow_html=True)

    st.markdown("<br><p style='text-align: center; color: #888;'>© 2026 Officecom | Powered by Konig Systems</p>", unsafe_allow_html=True)
else:
    st.error("Sem dados para exibir.")

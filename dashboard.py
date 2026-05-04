import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página de Elite
st.set_page_config(page_title="KONIG | Suporte iGaming Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- SISTEMA DE SEGURANÇA KONIG ---
def check_password():
    """Retorna True se a senha estiver correta."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Tela de Login
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.image("https://img.icons8.com/neon/96/lock.png", width=80)
        st.title("ACESSO RESTRITO")
        password = st.text_input("Insira a senha de acesso:", type="password")
        if st.button("ENTRAR NO SISTEMA"):
            if password == "suporten2":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta. Acesso negado.")
    return False

if not check_password():
    st.stop()  # Trava a execução aqui se não estiver autenticado

# --- INÍCIO DO DASHBOARD (SÓ EXECUTA APÓS O LOGIN) ---

# URL do Google Sheets (Exportação CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1LWuWM2iEPz-3f3qvXaaokiNrnLafjPP43LIAKz5tcoA/export?format=csv&gid=1321610989"

# CSS para Estética de Luxo
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    [data-testid="stSidebar"] { background-color: #0e1117; border-right: 1px solid #333; }
    h1, h2, h3 { color: #D1FF00 !important; }
    .stButton>button { background-color: #D1FF00; color: black; border-radius: 8px; font-weight: bold; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# Função de Carga
@st.cache_data(ttl=3600)
def load_data_from_sheets():
    try:
        df = pd.read_csv(SHEET_URL, encoding="utf-8")
        df.columns = [
            'ID', 'Titulo', 'Solicitante', 'Criacao', 'Status', 
            'Casas', 'Atualizacao', 'Leitura', 'Mesclado', 'Link'
        ]
        df['Criacao'] = pd.to_datetime(df['Criacao'], format='%d/%m/%Y', errors='coerce')
        df['Status'] = df['Status'].fillna('Sem Status')
        return df
    except Exception as e:
        st.error(f"Erro ao sincronizar com o Google Sheets: {e}")
        return pd.DataFrame()

# --- SIDEBAR FILTROS ---
with st.sidebar:
    st.image("https://img.icons8.com/neon/96/dashboard.png", width=80)
    st.title("KONIG CONTROL")
    if st.button("🚪 LOGOUT"):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown("---")
    
    if st.button("🔄 SINCRONIZAR AGORA"):
        st.cache_data.clear()
        st.toast("Dados atualizados com sucesso!", icon="✅")
        st.rerun()

    st.markdown("---")
    st.subheader("Filtros Globais")
    
    df_raw = load_data_from_sheets()
    
    if not df_raw.empty:
        status_list = ['Todos'] + sorted(df_raw['Status'].unique().tolist())
        selected_status = st.selectbox("Filtrar por Status", status_list)
        
        casa_list = ['Todas'] + sorted(df_raw['Casas'].str.split(', ').explode().unique().tolist())
        selected_casa = st.selectbox("Filtrar por Casa", casa_list)

# --- GESTÃO DE ESTADO (CROSS-FILTERING) ---
if 'filtros' not in st.session_state:
    st.session_state.filtros = {'Status': None, 'Casas': None}

# --- APLICAÇÃO DOS FILTROS ---
if not df_raw.empty:
    df = df_raw.copy()

    if selected_status != 'Todos':
        df = df[df['Status'] == selected_status]
    if selected_casa != 'Todas':
        df = df[df['Casas'].str.contains(selected_casa, na=False)]

    if st.session_state.filtros['Status']:
        df = df[df['Status'] == st.session_state.filtros['Status']]
    if st.session_state.filtros['Casas']:
        df = df[df['Casas'].str.contains(st.session_state.filtros['Casas'], na=False)]

    # --- CABEÇALHO ---
    st.title("🛡️ KONIG | Suporte N2 iGaming")
    st.markdown(f"Exibindo dados de **{len(df)}** tickets ativos (Protegido por Senha).")

    # --- MÉTRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total de Tickets", len(df))
    with m2:
        devolutiva = len(df[df['Status'] == 'Devolutiva'])
        st.metric("Aguardando Devolutiva", devolutiva, delta=f"{(devolutiva/len(df)*100):.1f}%" if len(df)>0 else "0%")
    with m3:
        fornecedor = len(df[df['Status'].str.contains('Fornecedor', na=False)])
        st.metric("Com Fornecedor", fornecedor)
    with m4:
        hoje = pd.Timestamp.now().normalize()
        novos_hoje = len(df[df['Criacao'] >= hoje - pd.Timedelta(days=7)])
        st.metric("Novos (7 dias)", novos_hoje)

    st.markdown("---")

    # --- GRÁFICOS INTERATIVOS ---
    c1, c2 = st.columns([1, 1])

    with c1:
        st.subheader("Status dos Tickets")
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Quantidade']
        fig_status = px.pie(status_counts, values='Quantidade', names='Status', hole=.4, color_discrete_sequence=px.colors.sequential.Greens_r)
        fig_status.update_layout(template="plotly_dark", margin=dict(t=0, b=0, l=0, r=0))
        selected_status_click = st.plotly_chart(fig_status, use_container_width=True, on_select="rerun")
        if selected_status_click and 'selection' in selected_status_click and selected_status_click['selection']['points']:
            st.session_state.filtros['Status'] = selected_status_click['selection']['points'][0]['label']
            st.rerun()

    with c2:
        st.subheader("Tickets por Casa (Operadora)")
        df_casas = df.assign(Casas=df['Casas'].str.split(', ')).explode('Casas')
        casa_counts = df_casas['Casas'].value_counts().reset_index()
        casa_counts.columns = ['Casa', 'Tickets']
        fig_casas = px.bar(casa_counts.head(10), x='Tickets', y='Casa', orientation='h', color='Tickets', color_continuous_scale='Viridis')
        fig_casas.update_layout(template="plotly_dark", margin=dict(t=0, b=0, l=0, r=0))
        selected_casa_click = st.plotly_chart(fig_casas, use_container_width=True, on_select="rerun")
        if selected_casa_click and 'selection' in selected_casa_click and selected_casa_click['selection']['points']:
            st.session_state.filtros['Casas'] = selected_casa_click['selection']['points'][0]['y']
            st.rerun()

    # --- TABELA DE DADOS ---
    st.markdown("---")
    st.subheader("📋 Detalhamento dos Tickets")
    df_display = df.copy()
    df_display['Link'] = df_display['Link'].apply(lambda x: f'<a href="{x}" target="_blank">Abrir Ticket</a>')
    st.write(df_display[['ID', 'Criacao', 'Solicitante', 'Status', 'Casas', 'Titulo', 'Link']].to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.error("Não foi possível carregar os dados.")

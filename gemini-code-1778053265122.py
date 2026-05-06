import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image

# --- ડેટાબેઝ કનેક્શન ---
conn = sqlite3.connect('anokha_optics.db', check_same_thread=False)
c = conn.cursor()

# જરૂરી ટેબલ્સ (Inventory, Sales, Customers)
c.execute('''CREATE TABLE IF NOT EXISTS inventory 
             (id INTEGER PRIMARY KEY, item_name TEXT, category TEXT, quantity INTEGER, price REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS sales 
             (id INTEGER PRIMARY KEY, customer_name TEXT, mobile TEXT, 
              re_sph TEXT, re_cyl TEXT, re_axis TEXT, le_sph TEXT, le_cyl TEXT, le_axis TEXT,
              item_details TEXT, total_amount REAL, date TEXT)''')
conn.commit()

# --- એપ સેટિંગ્સ ---
st.set_page_config(page_title="Anokha Chashma Ghar", layout="wide")

# CSS દ્વારા Blue અને Gold થીમ એપ્લાય કરવી
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { background-color: #003366; color: white; border-radius: 5px; border: 1px solid #D4AF37; }
    h1, h2, h3 { color: #003366; }
    .sidebar .sidebar-content { background-image: linear-gradient(#003366,#001a33); color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- સાઇડબાર: લોગો અને નામ ---
try:
    image = Image.open('logo.png') # તમારા ફોટાને logo.png નામ આપીને અહીં રાખવો
    st.sidebar.image(image, use_column_width=True)
except:
    st.sidebar.title("અનોખા ચશ્મા ઘર")

st.sidebar.markdown("<h2 style='text-align: center; color: #D4AF37;'>ANOKHA CHASHMA GHAR</h2>", unsafe_allow_html=True)
menu = ["📊 ડેશબોર્ડ", "🧾 નવું બિલ (Invoice)", "👓 સ્ટોક મેનેજમેન્ટ", "📜 વેચાણનો ઇતિહાસ"]
choice = st.sidebar.selectbox("મેનુ પસંદ કરો", menu)

# --- 1. DASHBOARD ---
if choice == "📊 ડેશબોર્ડ":
    st.title("દુકાનનો આજનો રિપોર્ટ")
    col1, col2, col3 = st.columns(3)
    
    total_sales = pd.read_sql("SELECT SUM(total_amount) FROM sales", conn).iloc[0,0] or 0
    stock_count = pd.read_sql("SELECT SUM(quantity) FROM inventory", conn).iloc[0,0] or 0
    
    col1.metric("કુલ કમાણી (Sales)", f"₹{total_sales}")
    col2.metric("બાકી સ્ટોક (Inventory)", stock_count)
    col3.metric("લોકેશન", "Surat, Gujarat")

# --- 2. BILLING SECTION ---
elif choice == "🧾 નવું બિલ (Invoice)":
    st.header("નવું કસ્ટમર બિલ અને નંબર")
    
    with st.form("invoice_form"):
        c1, c2 = st.columns(2)
        customer_name = c1.text_input("ગ્રાહકનું નામ")
        customer_mobile = c2.text_input("મોબાઇલ નંબર")
        
        st.markdown("---")
        st.subheader("👁️ આંખના નંબર (Prescription Record)")
        
        # આંખના નંબર માટેનું ટેબલ સ્ટ્રક્ચર
        p_col1, p_col2, p_col3, p_col4 = st.columns(4)
        p_col1.write("**Eye**")
        p_col2.write("**SPH**")
        p_col3.write("**CYL**")
        p_col4.write("**AXIS**")
        
        re_sph = p_col2.text_input("RE", key="re_sph", label_visibility="collapsed")
        re_cyl = p_col3.text_input("RE_C", key="re_cyl", label_visibility="collapsed")
        re_axis = p_col4.text_input("RE_A", key="re_axis", label_visibility="collapsed")
        
        le_sph = p_col2.text_input("LE", key="le_sph", label_visibility="collapsed")
        le_cyl = p_col3.text_input("LE_C", key="le_cyl", label_visibility="collapsed")
        le_axis = p_col4.text_input("LE_A", key="le_axis", label_visibility="collapsed")

        st.markdown("---")
        st.subheader("🛒 પ્રોડક્ટ વિગત")
        # સ્ટોકમાંથી આઈટમ લિસ્ટ મેળવવું
        items_in_stock = pd.read_sql("SELECT item_name FROM inventory WHERE quantity > 0", conn)
        item_list = items_in_stock['item_name'].tolist() if not items_in_stock.empty else ["સ્ટોક ખાલી છે"]
        
        selected_item = st.selectbox("ફ્રેમ / લેન્સ પસંદ કરો", item_list)
        price = st.number_input("બિલની રકમ (₹)", min_value=0.0)
        
        if st.form_submit_button("બિલ સેવ અને પ્રિન્ટ કરો"):
            # ડેટાબેઝમાં સેવ કરવું
            date_now = datetime.now().strftime("%d-%m-%Y %H:%M")
            c.execute("INSERT INTO sales (customer_name, mobile, re_sph, re_cyl, re_axis, le_sph, le_cyl, le_axis, item_details, total_amount, date) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (customer_name, customer_mobile, re_sph, re_cyl, re_axis, le_sph, le_cyl, le_axis, selected_item, price, date_now))
            # સ્ટોક ઓછો કરવો
            c.execute("UPDATE inventory SET quantity = quantity - 1 WHERE item_name = ?", (selected_item,))
            conn.commit()
            st.success(f"અનોખા ચશ્મા ઘર: {customer_name} નું બિલ સેવ થઈ ગયું છે.")

# --- 3. INVENTORY MANAGEMENT ---
elif choice == "👓 સ્ટોક મેનેજમેન્ટ":
    st.header("વેપારી પાસેથી આવેલ માલ (Inventory Entry)")
    
    with st.expander("➕ નવો સ્ટોક ઉમેરો"):
        with st.form("stock_form"):
            name = st.text_input("પ્રોડક્ટનું નામ (દા.ત. Ray-Ban Frame, Zeiss Lens)")
            cat = st.selectbox("કેટેગરી", ["Frame", "Lens", "Sunglasses", "Solution", "Other"])
            qty = st.number_input("જથ્થો", min_value=1)
            cost = st.number_input("ખરીદ કિંમત", min_value=0.0)
            if st.form_submit_button("સ્ટોક અપડેટ કરો"):
                c.execute("INSERT INTO inventory (item_name, category, quantity, price) VALUES (?,?,?,?)", (name, cat, qty, cost))
                conn.commit()
                st.success("માલ સ્ટોકમાં ઉમેરાઈ ગયો છે.")

    st.subheader("વર્તમાન સ્ટોકની યાદી")
    df_inv = pd.read_sql("SELECT item_name, category, quantity, price FROM inventory", conn)
    st.dataframe(df_inv, use_container_width=True)

# --- 4. SALES HISTORY ---
elif choice == "📜 વેચાણનો ઇતિહાસ":
    st.header("તમામ ગ્રાહકોના રેકોર્ડ અને નંબર")
    df_sales = pd.read_sql("SELECT * FROM sales", conn)
    st.dataframe(df_sales, use_container_width=True)
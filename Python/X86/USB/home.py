import streamlit as st
import demo
st.set_page_config(
    layout="wide",
)

if 'username' not in st.session_state:
    st.session_state['username'] = 'hanyang'
if 'areaA' not in st.session_state:
    st.session_state['areaA'] = 'hanyang,kenghzou' 
if 'areaUnknown' not in st.session_state:
    st.session_state['areaUnknown'] = '' 

st.title('Bind information from tag and Access Card')

with st.container():
    st.header("This is welcoming message")
    #st.image("https://static.streamlit.io/examples/cat.jpg")
col1, col2= st.columns(2)
with st.container():
    with col1:
       st.header("This is Area One")
      
       st.text_area(label="-",placeholder=st.session_state['areaA'],height=600,key=1)
       st.write(demo.get_result())

    with col2:
       st.header("This is UnknownArea") 
       st.text_area(label="-",placeholder=st.session_state['areaUnknown'],height=600,key=2)

st.session_state['areaA'] ="kitlin,kenghzou,hanyang"

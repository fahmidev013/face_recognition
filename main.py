# Frontend: face_recognition_streamlit.py
import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:5000"

st.title('Face Recognition System')

menu = ['Register', 'Recognize']
choice = st.sidebar.selectbox('Menu', menu)

if choice == 'Register':
    st.header('Register New User')
    name = st.text_input('Name')
    uploaded_file = st.file_uploader('Upload an image', type=['jpg', 'jpeg', 'png'])

    if st.button('Register'):
        if name and uploaded_file:
            files = {'image': uploaded_file}
            data = {'name': name}
            response = requests.post(f'{BACKEND_URL}/register', files=files, data=data)

            if response.status_code == 200:
                st.success(response.json().get('message'))
            else:
                st.error(response.json().get('message'))
        else:
            st.error('Please provide both name and image.')


if choice == 'Recognize':
    st.header('Recognize User')
    uploaded_file = st.file_uploader('Upload an image', type=['jpg', 'jpeg', 'png'])

    if st.button('Recognize'):
        if uploaded_file:
            files = {'image': uploaded_file}
            response = requests.post(f'{BACKEND_URL}/recognize', files=files)

            if response.status_code == 200:
                name = response.json().get('name')
                st.success(f'Recognized as: {name}')
            else:
                st.error(response.json().get('message'))
        else:
            st.error('Please upload an image.')

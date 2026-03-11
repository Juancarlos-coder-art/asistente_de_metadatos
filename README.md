##Dependencias
-Se debe de instalar las librerías de openai, groq, dotenv y streamlit
##Configuraciones
-Se debe crear un archivo .env que contenga dos parámetros:
  -Por un lado USE_OPENAI = false
  -Por otro lado GROQ_API_KEY = "Api que se haya creado en groq"
##LLM
Se utiliza GROQ_API_KEY debido a que es una API gratuita, pero el código da la opción de utilizar OPENAI siempre que se haya contratado la API

#Ejecución de Código
Para ejecuar el código se debe de llamar desde la terminal de la siguiente manera: 
-Streamlit run app.py
- Se abrirá una página en la que se podrá utilizar la interfaz de manera segura y en local.

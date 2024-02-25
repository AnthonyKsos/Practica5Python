import pandas as pd
import openpyxl
import sqlite3
import requests
from datetime import date

df_reactiva = pd.read_excel('reactiva.xlsx', sheet_name = 'TRANSFERENCIAS 2020')

####################################
## Genere una función de limpieza ##
####################################

def limpiar_columnas(df_reactiva):
    # A minúsculas
    df_reactiva.columns = df_reactiva.columns.str.lower()
    # Eliminar espacios
    df_reactiva.columns = df_reactiva.columns.str.replace(' ', '_')
    # Eliminar tildes
    df_reactiva.columns = df_reactiva.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    return df_reactiva

df_limpio = limpiar_columnas(df_reactiva)
print("Dataframe limpio")
df_limpio.head(2)

######################################
## Elimine ID y TipoMoneda repetida ##
######################################

df_limpio_eliminado = df_limpio.drop(['id', 'tipo_moneda.1'], axis= 1)
print("Dataframe limpio y sin repeticiones")
df_limpio_eliminado.head(2)

##############
## Sin coma ##
##############

df_limpio_eliminado_sin_coma = df_limpio_eliminado
df_limpio_eliminado_sin_coma['dispositivo_legal'] = df_limpio_eliminado_sin_coma['dispositivo_legal'].replace({'0m':''}, regex=True)
df_limpio_eliminado_sin_coma.head(2)

###############
## API Sunat ##
###############

def tipo_cambio_sunat(fecha):
    try:
        url = f"https://api.apis.net.pe/v1/tipo-cambio-sunat?fecha={fecha}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['compra']
    except requests.RequestException as e:
        print("Error:", e)
        return None

fecha_actual = date.today().strftime('%Y-%m-%d')
cambio_usd = tipo_cambio_sunat(fecha_actual)

df_sunat = df_limpio_eliminado_sin_coma
df_sunat['monto_inversion_dol'] = (df_sunat['monto_de_inversion'] / cambio_usd).round(2)
df_sunat['monto_transferencia2020_dol'] = (df_sunat['monto_de_transferencia_2020'] / cambio_usd).round(2)

if 'monto_dolares' in df_sunat.columns:
    df_sunat.drop('monto_dolares', axis=1, inplace=True)
df_sunat.head(2)

#################################
## Cambios a columna 'Estado' ###
#################################

df_estado = df_sunat
df_estado['estado'] = df_estado['estado'].replace('En Ejecución', 'Ejecución')
df_estado['estado'] = df_estado['estado'].replace('Convenio y/o Contrato Resuelto', 'Resuelto')
df_estado.estado.unique()

###############################
## Puntuar columna 'Estado' ###
###############################

# Definir la función en base a rangos
def puntuar_estado(estado):
    valor = estado
    if (valor == 'Resuelto'):
        puntuacion = 0
    elif valor == 'Actos Previos' :
        puntuacion = 1
    elif valor == 'Ejecución' :
        puntuacion = 2
    elif valor == 'Concluido':
        puntuacion = 3
    else:
        puntuacion = None
    return puntuacion
    
# Aplicar la funcion al dataframe
df_puntuar = df_estado
df_puntuar['puntuación'] = df_puntuar['estado'].apply(puntuar_estado)
df_puntuar.head(2)

######################
## Tabla de Ubigeos ##
######################

# Conectar a la bd
conexion = sqlite3.connect('ubicaciones.db')
ubigeo = df_puntuar[['ubigeo', 'region', 'provincia', 'distrito']].drop_duplicates() # Eliminar duplicados
ubigeo.to_sql('ubigeo', conexion, if_exists='replace', index=False) # Crear tabla y almacenar
conexion.commit()

# Cerrar conexion
conexion.close()

# Dataframe filtrado
filtrar = (df_puntuar['tipologia'] == 'Equipamiento Urbano') & (df_puntuar['puntuación'] >= 1) & (df_puntuar['puntuación'] <= 3)
df_filtrado = df_puntuar[filtrar]

# Aplicamos el filtro
regiones = df_filtrado['region'].unique()

for region in regiones:
    filtro = df_filtrado['region'] == region
    df_region = df_filtrado[filtro]
    if not df_region.empty:
        # Ordenando y sacando top 5
        df_region_ordenado = df_region.sort_values(by='monto_de_inversion', ascending=False)
        top_5 = df_region_ordenado.head(5)
        # Guardar en excel
        nombre_archivo = f"top_5_inversion_{region}.xlsx"
        top_5.to_excel(nombre_archivo, index=False)
        print(f"Archivo '{nombre_archivo}' generado correctamente.")
    else:
        print(f"No existen datos para '{region}'")
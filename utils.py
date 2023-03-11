# Creamos una funcion que nos devuelva los datos del usuario en base al nombre de invocador

def datos_invocador(nombres_invocador:list)->pd.DataFrame:
    
    # Definimos algunas variables
    key = 'RGAPI-31b23d7f-b374-4d30-bda3-286690965c41'
    region = 'LA2'
    
    # Creamos la variable para almacenar 
    df_personal_infomation = pd.DataFrame()
    
    # Creamos un bucle for para que funcionen la lista de nombres a emplear.
    for nombre_invocador in nombres_invocador:
        
        # Conectamos a la API
        url = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{nombre_invocador}?api_key={key}' 
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: no se pudo obtener la maestría de campeones del invocador {nombre_invocador}.")
            return None

        # Lo transformamos en un texto
        texto = response.text

        # Lo transformamos en un JSON y lo normalizamos en un pd.df
        json_info = json.loads(texto)
        personal_infomation = pd.json_normalize(json_info)

        # Almacenamos los datos
        df_personal_infomation = pd.concat([df_personal_infomation, personal_infomation], ignore_index=True)

        print(f'Se finalizo el proceso de transformacion para {nombre_invocador}.')
    
    return df_personal_infomation

######################################################################################
######################################################################################
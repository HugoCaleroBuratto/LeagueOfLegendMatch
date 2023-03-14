######################################################################################
######################################################################################

# Creamos una funcion que nos devuelva los datos del usuario en base al nombre de invocador

def datos_invocador(nombres_invocador:list)->pd.DataFrame:
    
    # Definimos algunas variables
    key = key_admin
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

# Creamos una funcion que nos traigan el nivel de maestria del jugafor con cada campeon

def champions_mastery(nombres_invocador:list)->pd.DataFrame():
    
    data_summoner = test #Aqui deberemos de nombrar la var igual que el df que almacene los datos de los jugadores
    
    # Definimos algunas variables
    key = key_admin
    region = 'LA2'
    
    # Creamos un dataframe vacio
    df_summoner_mastery = pd.DataFrame()
    
    # Tenemos que obtener el id del dataframe obtenido anteriormente en base al nombre que ingresemos
    summoners_id = data_summoner[data_summoner['name'] == nombres_invocador]['id']
    
    # Creamos un bucle for para que tome todos los nombre que indiquemos
    for summoner_id in summoners_id:
    
        # Nos conectamos a la api para obtener los datos
        api_for_mastery = f'https://{region}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{summoner_id}?api_key={key}'

        response = requests.get(api_for_mastery)
        if response.status_code != 200:
            print(f"Error: no se pudo obtener la maestría de campeones del invocador {summoner_id}.")
            return None

        # Lo transformamos en un texto
        texto = response.text

        # Lo transformamos en un JSON y lo normalizamos en un pd.df
        json_info = json.loads(texto)
        mastery_information = pd.json_normalize(json_info)

        # Almacenamos los datos
        df_summoner_mastery = pd.concat([df_summoner_mastery, mastery_information], ignore_index=True)

        print(f'Se finalizo el proceso de transformacion para {summoner_id}.')
        
    # Trabajamos los datos para que nos traiga como columna tambien el nombre del invocador
    df_summoner_mastery.rename(columns={'summonerId':'id'}, inplace = True)
    df_summoner_mastery = df_summoner_mastery.merge(data_summoner[['name', 'id']], on='id', how='left')
    
    return df_summoner_mastery

######################################################################################
######################################################################################

# Definimos una funcion que nos traiga los datos de los personajes segun la version de juego

def champions_information(version:str)->pd.DataFrame:
    
    # Definimos el url junto a nuestra version como variable 
    url_champions_information = f'http://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json'
    
    # Nos conectamos a la api para obtener los datos
    response = requests.get(url_champions_information) 
    if response.status_code != 200:
        print("Error: no se puedo conectar correctamente a la api, controlar version del juego")
        return None
    
    # Lo transformamos en un texto
    texto = response.text
    
    # Lo transformamos en un json y comenzamos a extraer los distintos datos
    json_info = json.loads(texto)
    
    # Convertimos los diccionarios anidados de "info" y "stats" en columnas separadas
    champions_data = []
    for champion_id, champion_data in json_info["data"].items():
        champion_data["id"] = champion_id
        champion_data.update(champion_data.pop("stats"))
        champion_data.update(champion_data.pop("info"))
        champions_data.append(champion_data)

    # Creamos el DataFrame
    champions_data = pd.DataFrame(champions_data)
    champions_data.drop(columns="image", inplace=True)

    return champions_data

######################################################################################
######################################################################################
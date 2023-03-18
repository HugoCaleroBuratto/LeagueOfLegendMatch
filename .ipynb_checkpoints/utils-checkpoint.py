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
    
    data_summoner = information #Aqui deberemos de nombrar la var igual que el df que almacene los datos de los jugadores
    
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
    
    # version = 13.5.1
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

# Definimos una funcion que nos traiga el id de las partidas que vamos a usar

def historial_partidas(nombre_invocador:str)->list:
    
    # En base al nombre del invocador deberemos conectarnos a sus datos y obtener el puuid
    puuid = list(datos_invocador([nombre_invocador])["puuid"])[0]
    
    # Definimos alguna variables
    start_time = 1577880000
    type_game = "ranked"
    start = 0 
    count = 100
    match_ids = []
    
    # Creamos el bucle
    # Hacer solicitudes GET a la API hasta que no haya más resultados disponibles
    while True:
        # Hacer solicitud GET a la API
        response = requests.get(f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?startTime={start_time}&type={type_game}&start={start}&count={count}&api_key={key_admin}")

        # Verificar si la solicitud fue exitosa
        if response.status_code != 200:
            print("Error al hacer la solicitud")
            break
        else:
            # Obtener la lista de Id de partida a partir de la respuesta JSON
            new_match_ids = response.json()

            # Si no hay más resultados disponibles, salir del bucle
            if len(new_match_ids) == 0:
                break
            else:
                # Agregar los nuevos Id de partida a la lista
                match_ids += new_match_ids

                # Incrementar el valor de "start" para obtener los próximos resultados
                start += count

    # Ordenar la lista de Id de partida por fecha de manera ascendente
    match_ids.sort(reverse=False)
    
    id_games = match_ids

    return id_games

######################################################################################
######################################################################################

### Eliminamos la columna que nos complica todco ###
# Definimos una funcion que nos devuelva el detalle de nuestra partida en base al id de la misma

def detalle_partidas(id_partida:str)->pd.DataFrame:
    
    # Establecemos una coneccion con la API para extraer los datos
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{id_partida}?api_key={key_admin}"
    
    try:
        # Establecemos la coneccion con la api
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error al obtener los datos de la partida {partida}.")
        else:
            None

        # Convertimos el json
        json_info = json.loads(response.text)

        # Comenzamos a transformar el json en un df
        match_information = pd.DataFrame(json_info['info']['participants'])
        
        # Reiniciamos el índice para evitar índices duplicados
        match_information.reset_index(drop=True, inplace=True)

        # Nos fijamos si existe la columna challenges
        if 'challenges'in match_information.columns: 

            # Desglozamos la columna que quedo como un diccionario
            match_information.drop(['challenges'], axis=1, inplace = True)
            
        else:
            None

        # Eliminamos las columnas que no nos sirven
        match_information.drop(['perks'], axis=1, inplace = True)

        # Establecemos una columna con el nombre del id de la partida
        match_information['id_game'] = id_partida
        print(f"Se finalizo el proceso para la partida {id_partida}")

        return match_information
    
    except Exception as e:
        print(f"Error al obtener los datos de la partida {id_partida}: {e}")
        return pd.DataFrame()

######################################################################################
######################################################################################

# Creamos una funcion que actue como bucle for
def detalle_partidas_lista(lista_partidas):
    # Creamos un DataFrame vacío para ir almacenando los resultados
    df_resultados = pd.DataFrame()
    
    # Iteramos sobre cada elemento de la lista
    for partida in lista_partidas:
        # Llamamos a la función detalle_partidas() para obtener el detalle de la partida actual
        detalle_partida = detalle_partidas(partida).reset_index(drop=True)
        
        # Concatenamos el resultado al DataFrame de resultados
        df_resultados = pd.concat([df_resultados, detalle_partida])
    
    # Devolvemos el DataFrame final con los detalles de todas las partidas
    return df_resultados.reset_index()

######################################################################################
######################################################################################

# Creamos una funcion que nos devuelva los detalles de challenges para aquellas partidas en donde exista.
def detalle_challenge_partida(id_partidas: list[str]) -> pd.DataFrame:
    # Definir un DataFrame vacío para almacenar la información de todas las partidas
    df_todas_las_partidas = pd.DataFrame()
    
    # Establecemos la conexión a la API
    for id_partida in id_partidas:
        url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{id_partida}?api_key={key_admin}"
        try:
            # Nos conectamos a la API
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error al obtener los datos de la partida {id_partida}.")
            else:
                None

            # Convertimos el json
            json_info = json.loads(response.text)

            # Comenzamos a transformar el json en un df
            match_information = pd.DataFrame(json_info['info']['participants'])

            # Reiniciamos el índice para evitar índices duplicados
            match_information.reset_index(drop=True, inplace=True)

            # Evaluamos la existencia de la columna challenge
            if 'challenges' in match_information.columns:

                # Desenglozamos los archivos
                df_challenges = pd.json_normalize(match_information['challenges'])

                # Le creamos la columna con el id de la partida
                df_challenges['id_game'] = id_partida
                df_challenges['summonerId'] = match_information['summonerId']

            # En caso de no existir que no haga nada
            else:
                print(f"No se encontraron datos sobre la columna challenges para {id_partida}")
                df_challenges = pd.DataFrame()

            # Concatenar el DataFrame temporal con el DataFrame vacío
            df_todas_las_partidas = pd.concat([df_todas_las_partidas, df_challenges], ignore_index=True)

        except Exception as e:
            # Que nos tire un error por no traer los datos
            print(f"Error al obtener los datos de la partida {id_partida}: {e}")
            
    # Devolver el DataFrame que contiene la información de todas las partidas
    return df_todas_las_partidas

######################################################################################
######################################################################################
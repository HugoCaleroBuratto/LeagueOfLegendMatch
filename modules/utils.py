import pandas as pd
import numpy as np
import requests
import json
import requests
import warnings as wn

# Para traer la api key
import os
from dotenv import load_dotenv

# Importamos la api key
# Obtén la ruta absoluta del archivo .env
env_path = os.path.join(os.path.dirname(__file__), '..', 'conf', '.env')

# Carga las variables de entorno desde el archivo .env
load_dotenv(env_path)

# Accede a la variable de entorno
key_admin = os.getenv('key_admin')

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
    
       
    # Definimos algunas variables
    key = key_admin
    region = 'LA2'
    
    # Creamos un dataframe vacio
    df_summoner_mastery = pd.DataFrame()
    
    # Generamos un df con los datos de los invocadores
    invocadores_info = datos_invocador(nombres_invocador)
    
    # Tenemos que obtener el id del dataframe obtenido anteriormente en base al nombre que ingresemos
    summoners_id =  invocadores_info[invocadores_info['name'] == nombres_invocador]['id']
    
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
        
    # Eliminaremos las columnas que no sean necesarias
    colstodrop = ['puuid', 'lastPlayTime', 'championPointsSinceLastLevel', 'championPointsUntilNextLevel',
                  'chestGranted', 'tokensEarned']
    df_summoner_mastery.drop(columns=colstodrop)
    
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

# Definimos algunos datos que vamos a definir para trabajar
def historial_del_jugador(nombre_jugador:str)->pd.DataFrame:
    # Extraemos el id del jugador
    id_del_jugador = df_games[df_games['summonerName'] == nombre_jugador]['summonerId'].unique().item()
    
    # Ahora con el id nos quedamos unicamente con las partidas que deseamos
    historial_partidas = df_games[df_games['summonerId'] == id_del_jugador]
    
    return historial_partidas


######################################################################################
######################################################################################

# Creamos la funcion para que nos de los datos de la partida en viv
    
def live_match(nombre_jugador:str)->pd.DataFrame:
    
    #definimos algunas variables
    key = key_admin
    region = 'la2'
        
    # Creamos el df para almacenar los datos
    df_match = pd.DataFrame()
    
    # Obtenemos el id del jugador
    id = datos_invocador([nombre_jugador])['id'][0]
    print(f'El id del jugador es: {id}')
    
    # Conexion a la API
    url = f'https://{region}.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{id}?api_key={key_admin}'
    response = requests.get(url)
    if response.status_code != 200:
        print(f'Error al obtener datos de: {nombre_jugador}')
        return None
    
    # Lo transformamos en texto 
    texto = response.text
    
    # Lo transformamos en JSON y normalziamos con pd
    json_info = json.loads(texto)
    df_match = pd.json_normalize(json_info)
    
    print(f'Se finalizo el proceso para la partida de {nombre_jugador}')
    
        # Creamos el df vacio
    detalle_partida = pd.DataFrame()

    # Creamos el bucle para normalizar cada JSON    
    for i in range(0,10,1):
        
        # Normalizamos cada jugador
        player_normalize = pd.json_normalize(pd.json_normalize(df_match['participants'])[i])
        
        # Guardamos los datos
        detalle_partida = pd.concat([detalle_partida, player_normalize])

    return detalle_partida

######################################################################################
######################################################################################

def detalle_partidas_for_train(id_partida:str)->pd.DataFrame:
    
    # Establecemos una coneccion con la API para extraer los datos
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{id_partida}?api_key={key_admin}"
    region = 'LA2'
    
    try:
        # Establecemos la coneccion con la api
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

        # Nos fijamos si existe la columna challenges
        if 'challenges'in match_information.columns: 

            # Desglozamos la columna que quedo como un diccionario
            match_information.drop(['challenges'], axis=1, inplace = True)
            
        else:
            None

        # # Eliminamos las columnas que no nos sirven
        # match_information.drop(['perks'], axis=1, inplace = True)

        # Establecemos una columna con el nombre del id de la partida
        match_information['id_game'] = id_partida
        print(f"Se finalizo el proceso para la partida {id_partida}")
        
        # Establecemos que A sea el df hasta el momento
        A = match_information
        
        # Eliminamos los warnings
        wn.filterwarnings('ignore')

        # Nos quedamos unicamente con las columnas que nos importan para entrenar
        information_to_train = A[['teamId', 'summonerId', 'championId', 'win']]
        information_to_train['perks_defense'] = pd.json_normalize(A['perks'])['statPerks.defense']
        information_to_train['perks_flex'] = pd.json_normalize(A['perks'])['statPerks.flex']
        information_to_train['perks_offense'] = pd.json_normalize(A['perks'])['statPerks.offense']
        information_to_train['subStyle'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[1])['style']
        information_to_train['primaryStyle'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[0])['style']
        information_to_train['primary1perk'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[0])['selections'])[0])['perk']
        # information_to_train['primary1var1'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[0])['selections'])[0])['var1']
        # information_to_train['primary1var2'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[0])['selections'])[0])['var2']
        # information_to_train['primary1var3'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[0])['selections'])[0])['var3']
        information_to_train['primary2perk'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[0])['selections'])[1])['perk']
        # information_to_train['primary2var1'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[0])['selections'])[1])['var1']
        # information_to_train['primary2var2'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[0])['selections'])[1])['var2']
        # information_to_train['primary2var3'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[0])['selections'])[1])['var3']
        information_to_train['sub1perk'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[1])['selections'])[0])['perk']
        # information_to_train['sub1var1'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[1])['selections'])[0])['var1']
        # information_to_train['sub1var2'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[1])['selections'])[0])['var2']
        # information_to_train['sub1var3'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[1])['selections'])[0])['var3']
        information_to_train['sub2perk'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[1])['selections'])[1])['perk']
        # information_to_train['sub2var1'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[1])['selections'])[1])['var1']
        # information_to_train['sub2var2'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[1])['selections'])[1])['var2']
        # information_to_train['sub2var3'] = pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(pd.json_normalize(A['perks'])['styles'])[1])['selections'])[1])['var3']
        
        ## Creamos la columna en donde esten los id de los campeones enemigos
        # Seleccionamos los campeones de cada equipo
        champions_team1 = information_to_train[information_to_train['teamId'] == 100]['championId']
        champions_team2 = information_to_train[information_to_train['teamId'] == 200]['championId']
        
        # Agrega la columna con los campeones enemigos
        information_to_train['enemy_champ_team'] = information_to_train.apply(lambda row: champions_team2.tolist() if row['teamId'] == 100 else champions_team1.tolist(), axis=1)

        # Tenemos que obtener el id del dataframe obtenido anteriormente en base al nombre que ingresemos
        summoners_id =  information_to_train['summonerId']
        df_summoner_mastery=pd.DataFrame()
        
        # Creamos un bucle for para que tome todos los nombre que indiquemos
        for summoner_id in summoners_id:
        
            # Nos conectamos a la api para obtener los datos
            api_for_mastery = f'https://{region}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{summoner_id}?api_key={key_admin}'

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
            
        # Eliminaremos las columnas que no sean necesarias
        colstodrop = ['puuid', 'lastPlayTime', 'championPointsSinceLastLevel', 'championPointsUntilNextLevel',
                    'chestGranted', 'tokensEarned']
        df_summoner_mastery.drop(columns=colstodrop, inplace=True)
        
        # Realizamos un merge entre ambos df para obtener los datos de maestria y puntos de campeon
        information_to_train02 = pd.merge(information_to_train, df_summoner_mastery, how='inner', on=['summonerId', 'championId'])
        
        print(f"Se finalizo la informacion de los jugadores")
        
        ## Ahora buscamos la informacion de los campeones para el parche que estableceremos
        # Definimos el url junto a nuestra version como variable 
        version = '13.12.1'
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
        champions_data.drop(columns=["image", "version", "id", "name", "title", "blurb"], inplace=True)
        champions_data.rename(columns={'key':'championId'}, inplace=True)
        
        # transformamos la col a joiner en el mismo tipo
        champions_data['championId'] = champions_data['championId'].astype('int64')
        
        dataset_to_train = information_to_train02.merge(champions_data, on='championId', how='inner')
        
        print(f"Se finalizo todo el proceso para la partida {id_partida}")

        return dataset_to_train
    
    except Exception as e:
        print(f"Error al obtener los datos de la partida {id_partida}: {e}")
        return pd.DataFrame()
    
######################################################################################
######################################################################################

# Creamos una funcion que actue como bucle for
def detalle_partidas_lista_for_train(lista_partidas):
    # Creamos un DataFrame vacío para ir almacenando los resultados
    df_resultados = pd.DataFrame()
    
    # Iteramos sobre cada elemento de la lista
    for partida in lista_partidas:
        
        try:
            # Llamamos a la función detalle_partidas() para obtener el detalle de la partida actual
            detalle_partida = detalle_partidas_for_train(partida).reset_index(drop=True)
            
            # Concatenamos el resultado al DataFrame de resultados
            df_resultados = pd.concat([df_resultados, detalle_partida])
            
        except Exception as e:
            print(f"Error al obtener los detalles de la partida {partida}: {str(e)}")
            continue
        
    print("Se finalizo todo el proceso de creacion del df para entrenar el modelo.")

    # Devolvemos el DataFrame final con los detalles de todas las partidas
    return df_resultados.reset_index()
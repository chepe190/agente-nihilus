#######################
# Agente Basico De IA #
# Herramientas        #
#######################

# Importacion para el manejo de sistema
import os
import requests

class IntermediateTools:
    def __init__(self):
        pass

    # Herramienta para consultar el tipo de cambio
    def consultar_tipo_cambio_api(self, moneda: str):
        if not moneda:
            return "Error: Se requiere el código de la moneda para obtener el tipo de cambio."
        
        # URL del servicio para obtener el tipo de cambio según la moneda:
        url = (
            f"https://open.er-api.com/v6/latest/{moneda.upper()}"
        )
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Lanza una excepción si la respuesta no es exitosa
            return response.json()  # Intentar decodificar la respuesta como JSON
        except Exception as e:
            print(f"Error al obtener_tipo_cambio_api: {moneda}. Error: {e}")
            return f"ERROR: No se pudo obtener el tipo de cambio para la moneda: {moneda}"

    # Herramienta para consultar la tasa de desempleo de un pais
    def consultar_desempleo_pais_api(self, codigo_pais: str):
        if not codigo_pais:
            return "Error: Se requiere el código ISO del país (por ejemplo GT, US, MX) para consultar la tasa de desempleo."
        
        # URL del servicio del Banco Mundial para el indicador de desempleo (gratis, sin necesidad de registro)
        url = (
            f"https://api.worldbank.org/v2/country/{codigo_pais.upper()}/indicator/SL.UEM.TOTL.ZS"
            f"?format=json&per_page=100"
        )
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error al obtener_desempleo_pais_api: {codigo_pais}. Error: {e}")
            return f"ERROR: No se pudo obtener la tasa de desempleo del país con código: {codigo_pais}"

    # Herramienta para consultar informacion general de un pais (moneda, capital, region, poblacion, etc.)
    def consultar_info_pais_api(self, pais: str):
        if not pais:
            return "Error: Se requiere el nombre del país para obtener su información."
        
        # URL del servicio countries.dev para obtener datos generales de un pais (gratis, sin necesidad de registro)
        url = (
            f"https://countries.dev/name/{pais}"
        )
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error al obtener_info_pais_api: {pais}. Error: {e}")
            return f"ERROR: No se pudo obtener la información del país: {pais}"

    # Herramienta para consultar el PIB (Producto Interno Bruto) de un pais
    def consultar_pib_pais_api(self, codigo_pais: str):
        if not codigo_pais:
            return "Error: Se requiere el código ISO del país (por ejemplo GT, US, MX) para consultar el PIB."
        
        # URL del servicio del Banco Mundial para el indicador de PIB (gratis, sin necesidad de registro)
        url = (
            f"https://api.worldbank.org/v2/country/{codigo_pais.upper()}/indicator/NY.GDP.MKTP.CD"
            f"?format=json&per_page=100"
        )
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error al obtener_pib_pais_api: {codigo_pais}. Error: {e}")
            return f"ERROR: No se pudo obtener el PIB del país con código: {codigo_pais}"

    # Herramienta para consultar la inflacion (indice de precios al consumidor) de un pais
    def consultar_inflacion_pais_api(self, codigo_pais: str):
        if not codigo_pais:
            return "Error: Se requiere el código ISO del país (por ejemplo GT, US, MX) para consultar la inflación."
        
        # URL del servicio del Banco Mundial para el indicador de inflacion (gratis, sin necesidad de registro)
        url = (
            f"https://api.worldbank.org/v2/country/{codigo_pais.upper()}/indicator/FP.CPI.TOTL.ZG"
            f"?format=json&per_page=100"
        )
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error al obtener_inflacion_pais_api: {codigo_pais}. Error: {e}")
            return f"ERROR: No se pudo obtener la inflación del país con código: {codigo_pais}"

    # Herramienta para consultar el precio actual de una criptomoneda
    def consultar_precio_cripto_api(self, criptomoneda: str, moneda_referencia: str = "usd"):
        if not criptomoneda:
            return "Error: Se requiere el nombre de la criptomoneda (por ejemplo bitcoin, ethereum) para consultar su precio."
        
        # URL del servicio CoinGecko para consultar precios de criptomonedas (gratis, sin necesidad de registro)
        url = (
            f"https://api.coingecko.com/api/v3/simple/price"
            f"?ids={criptomoneda.lower()}&vs_currencies={moneda_referencia.lower()}"
        )
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error al obtener_precio_cripto_api: {criptomoneda}. Error: {e}")
            return f"ERROR: No se pudo obtener el precio de la criptomoneda: {criptomoneda}"
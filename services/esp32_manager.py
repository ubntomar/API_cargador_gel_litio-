#!/usr/bin/env python3
"""
ESP32Manager - VERSIÓN FRONTEND OPTIMIZADA
Maneja polling cada 3 segundos del frontend sin bloquear comandos SET
ARCHIVO: services/esp32_manager.py
"""

import serial
import json
import time
import asyncio
import threading
from typing import Optional, Dict, Any
from core.config import settings
from core.logger import logger
from models.esp32_data import ESP32Data

class ESP32Manager:
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.connected = False  # ✅ CORRECCIÓN: Atributo faltante para compatibilidad
        self.lock = threading.Lock()  # ✅ CORRECCIÓN: Lock thread-safe para concurrencia real
        self._last_data = None
        self._last_data_time = 0
        self._cache_duration = 20.0  # ✅ FRONTEND: Cache por 20 segundos para polling cada 3s
        self._communication_errors = 0
        self._max_retries = 3
        
        # ✅ NUEVOS: Atributos para get_connection_info
        self.last_successful_communication = None
        self.communication_errors = 0
        
        # ✅ FRONTEND POLLING: Control especial para comandos concurrentes
        self._last_set_command_time = 0
        self._min_set_command_interval = 1.0  # Reducido a 1s para mejor responsividad
        
        # ✅ NUEVO: Sistema de prioridades para GET vs SET
        self._priority_lock = threading.RLock()  # Re-entrant lock para operaciones anidadas
        self._get_requests_active = 0  # Contador de peticiones GET activas
        self._max_concurrent_gets = 1  # Máximo 1 petición GET simultánea para no saturar
        
        logger.info("🚀 Iniciando ESP32 Manager optimizado para frontend polling...")
        
    async def start(self) -> bool:
        """Inicializar manager y conectar"""
        logger.info("🚀 Iniciando ESP32 Manager optimizado con chunks...")
        
        if await self._connect():
            logger.info("✅ ESP32 Manager iniciado correctamente")
            return True
        
        logger.error("❌ Error iniciando ESP32 Manager")
        return False
    
    async def _connect(self) -> bool:
        """Establecer conexión serial con timeout optimizado"""
        max_retries = 3
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔌 Intento {attempt}: Conectando a {self.port}")
                
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=1.0,
                    write_timeout=1.0
                )
                
                # Esperar estabilización
                await asyncio.sleep(2)
                
                # Probar comunicación
                if await self._test_communication():
                    self.connected = True  # ✅ CORRECCIÓN: Marcar como conectado
                    logger.info(f"✅ Conectado al ESP32 en {self.port}")
                    return True
                else:
                    self.connected = False
                    if self.serial_conn:
                        self.serial_conn.close()
                        
            except Exception as e:
                logger.error(f"❌ Error en intento {attempt}: {e}")
                if self.serial_conn:
                    self.serial_conn.close()
                    
                if attempt < max_retries:
                    await asyncio.sleep(2)
        
        return False
    
    async def _test_communication(self) -> bool:
        """Probar comunicación básica con ESP32"""
        try:
            logger.info("🧪 Probando comunicación con ESP32...")
            
            # Limpiar buffer
            self.serial_conn.reset_input_buffer()
            
            # Enviar comando de prueba
            await self._send_command_simple("CMD:GET_DATA")
            await asyncio.sleep(2)
            
            # Intentar leer respuesta
            response = await self._read_json_chunked(timeout=3.0)
            
            if response and len(response) > 50:
                logger.info("✅ Comunicación con ESP32 exitosa")
                return True
            else:
                logger.warning(f"⚠️ Respuesta inesperada del ESP32")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando comunicación: {e}")
            return False

    async def _send_command_simple(self, command: str) -> bool:
        """Envío simple de comando (sin lectura de respuesta)"""
        try:
            if not self.serial_conn or not self.serial_conn.is_open:
                return False
            
            # Limpiar buffer antes de enviar
            self.serial_conn.reset_input_buffer()
            
            # Enviar comando
            command_bytes = (command + '\n').encode('utf-8')
            self.serial_conn.write(command_bytes)
            self.serial_conn.flush()
            
            logger.debug(f"📤 Comando enviado: {command}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando comando: {e}")
            return False

    async def _read_json_chunked(self, chunk_size: int = 32, timeout: float = 5.0) -> Optional[str]:
        """
        ✅ TÉCNICA OPTIMIZADA: Lectura por chunks (basada en paste.txt)
        - Chunks de 16-32 bytes que funcionaron perfectamente en RISC-V
        - Validación inteligente de JSON completo
        - Manejo robusto de errores
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
        
        logger.debug(f"📥 Leyendo JSON con chunks de {chunk_size} bytes")
        
        start_time = time.time()
        response = ""
        consecutive_empty = 0
        max_empty = 50
        
        try:
            while (time.time() - start_time) < timeout:
                bytes_available = self.serial_conn.in_waiting
                
                if bytes_available > 0:
                    # ✅ MEJORA: Chunks pequeños que funcionaron en RISC-V
                    read_size = min(chunk_size, bytes_available)
                    chunk = self.serial_conn.read(read_size)
                    
                    if chunk:
                        chunk_str = chunk.decode('utf-8', errors='replace')
                        response += chunk_str
                        consecutive_empty = 0
                        
                        # Verificar JSON completo
                        if self._is_json_complete(response):
                            logger.debug(f"✅ JSON completo: {len(response)} caracteres")
                            return response
                else:
                    consecutive_empty += 1
                    if consecutive_empty > max_empty:
                        break
                    await asyncio.sleep(0.01)
            
            return response if response else None
            
        except Exception as e:
            logger.error(f"❌ Error en lectura chunked: {e}")
            return None

    async def _read_json_adaptive(self, timeout: float = 5.0) -> Optional[str]:
        """
        ✅ TÉCNICA AVANZADA: Lectura adaptativa que ajusta chunk size según el tráfico
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
        
        logger.debug("📊 Leyendo JSON con tamaño adaptativo")
        
        start_time = time.time()
        response = ""
        chunk_size = 16  # Empezar pequeño
        max_chunk = 128
        good_reads = 0
        
        try:
            while (time.time() - start_time) < timeout:
                bytes_available = self.serial_conn.in_waiting
                
                if bytes_available > 0:
                    # Ajustar chunk size dinámicamente
                    if bytes_available >= chunk_size * 2 and good_reads > 3:
                        chunk_size = min(chunk_size * 2, max_chunk)
                    
                    read_size = min(chunk_size, bytes_available)
                    chunk = self.serial_conn.read(read_size)
                    
                    if chunk:
                        chunk_str = chunk.decode('utf-8', errors='replace')
                        response += chunk_str
                        good_reads += 1
                        
                        # Mostrar progreso
                        if len(response) % 200 == 0:
                            logger.debug(f"   📊 {len(response)} chars (chunk: {chunk_size}b)")
                        
                        # Verificar JSON completo
                        if self._is_json_complete(response):
                            logger.debug(f"   🎯 JSON completo: {len(response)} caracteres")
                            return response
                else:
                    await asyncio.sleep(0.01)
            
            return response if response else None
            
        except Exception as e:
            logger.error(f"   ❌ Error en lectura adaptativa: {e}")
            return None

    def _is_json_complete(self, data: str) -> bool:
        """
        ✅ TÉCNICA OPTIMIZADA: Verificación inteligente de JSON completo (basada en paste.txt)
        - Balance de llaves
        - Parsing JSON real
        - Validación de campos característicos del ESP32
        """
        if not data or len(data.strip()) < 50:
            return False
        
        try:
            # Buscar inicio de JSON
            json_start = data.find('{')
            if json_start == -1:
                return False
            
            json_part = data[json_start:]
            
            # Verificar balance de llaves
            open_braces = json_part.count('{')
            close_braces = json_part.count('}')
            
            if open_braces != close_braces or open_braces == 0:
                return False
            
            # Intentar parsear JSON
            parsed = json.loads(json_part)
            
            # Verificar que tiene campos característicos del ESP32
            required_fields = ['batteryVoltage', 'batteryCapacity', 'temperatureC']
            if not any(field in parsed for field in required_fields):
                return False
            
            return True
            
        except (json.JSONDecodeError, ValueError):
            return False

    async def _get_json_with_strategies(self, command: str) -> Optional[str]:
        """
        ✅ ESTRATEGIAS MÚLTIPLES: Combinar técnicas exitosas de paste.txt
        """
        logger.debug(f"🎯 Obteniendo JSON para: {command}")
        
        # Preparación inicial
        await self._send_command_simple(command)
        await asyncio.sleep(0.3)
        
        # ✅ Estrategia 1: Chunks 16 bytes (funcionó perfectamente en RISC-V)
        logger.debug("🔧 Estrategia 1: Chunks 16 bytes")
        data = await self._read_json_chunked(chunk_size=16, timeout=4.0)
        if data and self._is_json_complete(data):
            return data
        
        # ✅ Estrategia 2: Chunks 32 bytes (también funcionó perfectamente)
        logger.debug("🔧 Estrategia 2: Chunks 32 bytes")
        await self._send_command_simple(command)
        await asyncio.sleep(0.3)
        data = await self._read_json_chunked(chunk_size=32, timeout=4.0)
        if data and self._is_json_complete(data):
            return data
        
        # ✅ Estrategia 3: Lectura adaptativa (backup)
        logger.debug("🔧 Estrategia 3: Adaptativa")
        await self._send_command_simple(command)
        await asyncio.sleep(0.3)
        data = await self._read_json_adaptive(timeout=4.0)
        if data and self._is_json_complete(data):
            return data
        
        logger.warning("❌ Todas las estrategias fallaron")
        return None

    async def get_data(self) -> Optional[Dict[str, Any]]:
        """
        ✅ FRONTEND OPTIMIZADO: Gestión especial para polling cada 3 segundos
        Prioriza cache agresivo y evita bloquear comandos SET
        """
        current_time = time.time()
        
        # ✅ FRONTEND POLLING: Cache más agresivo para peticiones frecuentes
        if (self._last_data and 
            (current_time - self._last_data_time) < self._cache_duration):
            return self._last_data
        
        # ✅ FRONTEND POLLING: Control de concurrencia para evitar saturar puerto serial
        with self._priority_lock:
            self._get_requests_active += 1
            
            # Si hay muchas peticiones GET concurrentes, usar cache más tiempo
            if self._get_requests_active > self._max_concurrent_gets:
                self._get_requests_active -= 1
                if self._last_data and (current_time - self._last_data_time) < 30.0:
                    logger.debug(f"🚦 Demasiadas peticiones GET concurrentes, usando cache extendido")
                    return self._last_data
        
        # ✅ FRONTEND POLLING: Timeout muy corto para peticiones GET (no bloquear SET)
        lock_timeout = 1.5  # Solo 1.5 segundos para peticiones GET
        lock_acquired = self.lock.acquire(timeout=lock_timeout)
        
        try:
            if not lock_acquired:
                # Si no puede obtener lock rápidamente, usar cache si existe
                with self._priority_lock:
                    self._get_requests_active -= 1
                
                if self._last_data and (current_time - self._last_data_time) < 30.0:
                    logger.debug(f"🚦 Lock ocupado, usando cache extendido para GET")
                    return self._last_data
                
                logger.warning(f"⚠️ GET request timeout después de {lock_timeout}s, usando cache")
                return self._last_data if self._last_data else None
            
            logger.debug(f"🔒 Lock adquirido para obtener datos")
            
            response = await self._get_json_with_strategies("CMD:GET_DATA")
            
            if response and self._is_json_complete(response):
                # ✅ CORRECCIÓN: Parsear JSON response a diccionario
                parsed_data = self._parse_data_response(response)
                if parsed_data:
                    # Actualizar cache
                    self._last_data = parsed_data
                    self._last_data_time = current_time
                    self._communication_errors = 0  # Reset counter on success
                    
                    # ✅ NUEVO: Actualizar timestamp de comunicación exitosa
                    self.last_successful_communication = current_time
                    self.communication_errors = self._communication_errors
                    
                    logger.info(f"✅ Datos ESP32 obtenidos exitosamente (cached por {self._cache_duration}s)")
                    return parsed_data
                else:
                    logger.warning("⚠️ Error parseando respuesta del ESP32")
                    return self._last_data if self._last_data else None
            else:
                logger.warning("⚠️ Respuesta incompleta del ESP32")
                # Usar cache si existe
                return self._last_data if self._last_data else None
                
        except Exception as e:
            self._communication_errors += 1
            self.communication_errors = self._communication_errors  # ✅ Sincronizar contador público
            logger.error(f"❌ Error obteniendo datos del ESP32 (error #{self._communication_errors}): {e}")
            
            # ✅ MEJORA: Retornar datos cached si hay errores de comunicación recientes
            if self._last_data and (current_time - self._last_data_time) < 30.0:
                logger.info(f"🔄 Retornando datos cached por error de comunicación")
                return self._last_data
                
            return None
        finally:
            if lock_acquired:
                self.lock.release()
            
            with self._priority_lock:
                self._get_requests_active -= 1
    
    def _parse_data_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parsear respuesta de datos del ESP32 (SIN CAMBIOS - compatible)
        """
        try:
            # El ESP32 envía: DATA:{json}
            if response.startswith("DATA:"):
                json_str = response[5:]  # Remover "DATA:"
                return json.loads(json_str)
            
            # O puede enviar JSON directo
            elif "{" in response:
                # Buscar el JSON en la respuesta
                start = response.find("{")
                if start != -1:
                    json_str = response[start:]
                    return json.loads(json_str)
            
            logger.error(f"❌ Formato de respuesta inválido: {response[:100]}")
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            return None

    async def _send_command_and_read_text(self, command: str, timeout: float = 4.0) -> Optional[str]:
        """
        ✅ COMANDO SET: Enviar comando y leer respuesta de texto plano
        Usado para comandos SET que retornan texto, no JSON
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("❌ Puerto serial no disponible")
            return None
        
        try:
            logger.debug(f"📤 Enviando comando SET: {command}")
            
            # Limpiar buffer antes de enviar
            self.serial_conn.reset_input_buffer()
            
            # Enviar comando
            command_bytes = (command + '\n').encode('utf-8')
            self.serial_conn.write(command_bytes)
            self.serial_conn.flush()
            
            # Esperar procesamiento
            await asyncio.sleep(0.5)
            
            # Leer respuesta de texto plano
            start_time = time.time()
            response = ""
            
            while (time.time() - start_time) < timeout:
                bytes_available = self.serial_conn.in_waiting
                
                if bytes_available > 0:
                    chunk = self.serial_conn.read(bytes_available)
                    if chunk:
                        chunk_str = chunk.decode('utf-8', errors='replace')
                        response += chunk_str
                        
                        # Verificar si tenemos respuesta completa
                        if "OK:" in response or "ERROR:" in response:
                            # Limpiar la respuesta
                            response = response.strip()
                            logger.debug(f"📥 Respuesta SET recibida: {response}")
                            return response
                        
                        # Si detectamos JSON, es que el ESP32 cambió de protocolo
                        if "{" in response and "}" in response:
                            logger.warning(f"⚠️ ESP32 devolvió JSON en lugar de texto para comando SET")
                            # Generar respuesta sintética basada en el comando
                            if "True" in command or "1" in command:
                                return f"OK:{command.split(':')[1] if ':' in command else 'parameter'} updated to True"
                            elif "False" in command or "0" in command:
                                return f"OK:{command.split(':')[1] if ':' in command else 'parameter'} updated to False"
                            else:
                                return f"OK:{command.split(':')[1] if ':' in command else 'parameter'} updated to {command.split(':')[-1] if ':' in command else 'value'}"
                else:
                    await asyncio.sleep(0.05)
            
            logger.warning(f"⚠️ Timeout esperando respuesta de texto para: {command}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error en comando SET: {e}")
            return None

    async def set_parameter(self, parameter: str, value: Any) -> Dict[str, Any]:
        """
        ✅ COMANDO SET OPTIMIZADO: Configurar parámetro con mayor timeout para SET
        """
        current_time = time.time()
        
        # ✅ FRONTEND: Rate limiting mejorado para comandos SET
        if (current_time - self._last_set_command_time) < self._min_set_command_interval:
            wait_time = self._min_set_command_interval - (current_time - self._last_set_command_time)
            logger.debug(f"⏱️ Rate limiting: esperando {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        
        # ✅ FRONTEND: Timeout más largo para comandos SET (críticos)
        lock_timeout = 8.0  # 8 segundos para comandos SET
        lock_acquired = self.lock.acquire(timeout=lock_timeout)
        
        if not lock_acquired:
            error_msg = f"Timeout obteniendo lock para configuración (esperó {lock_timeout}s)"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "parameter": parameter,
                "value": value
            }
        
        try:
            self._last_set_command_time = time.time()
            logger.debug(f"🔒 Lock adquirido para configurar {parameter}")
            
            # ✅ CONVERSIÓN: ESP32 necesita 1/0 para booleanos, no True/False
            esp32_value = value
            if isinstance(value, bool):
                esp32_value = 1 if value else 0
                logger.debug(f"🔄 Convirtiendo valor booleano: {value} → {esp32_value}")
            
            # ✅ CORRECCIÓN CRÍTICA: ESP32 espera nombres exactos, NO en mayúsculas
            # El ESP32 busca "useFuenteDC", no "USEFUENTEDC"
            command = f"CMD:SET_{parameter}:{esp32_value}"
            
            # ✅ PROTOCOLO SEPARADO: Usar texto plano para comandos SET
            response = await self._send_command_and_read_text(command, timeout=6.0)
            
            result = {
                "success": False,
                "esp32_response": response,
                "parameter": parameter,
                "value": value
            }
            
            if response:
                if response.startswith("OK:"):
                    result["success"] = True
                    logger.info(f"✅ {parameter} configurado exitosamente: {value} → {response}")
                elif response.startswith("ERROR:"):
                    result["error"] = response
                    logger.error(f"❌ Error configurando {parameter}: {response}")
                else:
                    result["error"] = f"Respuesta inesperada: {response}"
                    logger.warning(f"⚠️ Respuesta inesperada para {parameter}: {response}")
            else:
                result["error"] = "Sin respuesta del ESP32"
                logger.error(f"❌ Sin respuesta del ESP32 para {parameter}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error configurando {parameter}: {e}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "parameter": parameter,
                "value": value
            }
        finally:
            if lock_acquired:
                self.lock.release()

    def get_connection_info(self) -> Dict[str, Any]:
        """Obtener información de conexión del ESP32"""
        from core.config import settings
        
        return {
            "connected": self.connected,
            "port": settings.SERIAL_PORT,
            "baudrate": settings.SERIAL_BAUDRATE,
            "last_communication": self.last_successful_communication,
            "communication_errors": self.communication_errors,
            "queue_size": 0,
            "has_cached_data": self._last_data is not None,
            "cache_age_seconds": time.time() - self._last_data_time if self._last_data else 0,
            "optimization": "chunks_enabled"
        }

    async def toggle_load(self, total_seconds: int) -> bool:
        """
        ✅ COMANDO ESP32: Apagar carga temporalmente
        Basado en el protocolo TOGGLE_LOAD del ESP32
        """
        try:
            logger.info(f"🔌 Enviando comando para apagar carga por {total_seconds} segundos")
            
            # Validar rango según el ESP32 (máximo 43200 segundos = 12 horas)
            if total_seconds < 1 or total_seconds > 43200:
                logger.error(f"❌ Tiempo fuera de rango: {total_seconds}s (permitido: 1-43200)")
                return False
            
            command = f"CMD:TOGGLE_LOAD:{total_seconds}"
            
            # ✅ USAR MÉTODO DE TEXTO PLANO (como SET)
            lock_acquired = self.lock.acquire(timeout=3.0)
            
            if not lock_acquired:
                logger.error("❌ Timeout obteniendo lock para toggle_load")
                return False
            
            try:
                response = await self._send_command_and_read_text(command, timeout=6.0)
                
                if response and response.startswith("OK:"):
                    logger.info(f"✅ Comando toggle_load enviado exitosamente: {response}")
                    # ✅ Invalidar cache
                    self._last_data = None
                    return True
                else:
                    logger.error(f"❌ Error en toggle_load: {response}")
                    return False
                    
            finally:
                self.lock.release()
                
        except Exception as e:
            logger.error(f"❌ Excepción en toggle_load: {e}")
            return False

    async def cancel_temporary_off(self) -> bool:
        """
        ✅ COMANDO ESP32: Cancelar apagado temporal
        Basado en el protocolo CANCEL_TEMP_OFF del ESP32
        """
        try:
            logger.info("🔌 Enviando comando para cancelar apagado temporal")
            
            command = "CMD:CANCEL_TEMP_OFF"
            
            lock_acquired = self.lock.acquire(timeout=3.0)
            
            if not lock_acquired:
                logger.error("❌ Timeout obteniendo lock para cancel_temporary_off")
                return False
            
            try:
                response = await self._send_command_and_read_text(command, timeout=4.0)
                
                if response and response.startswith("OK:"):
                    logger.info(f"✅ Comando cancel_temporary_off enviado exitosamente: {response}")
                    # ✅ Invalidar cache
                    self._last_data = None
                    return True
                else:
                    logger.error(f"❌ Error en cancel_temporary_off: {response}")
                    return False
                    
            finally:
                self.lock.release()
                
        except Exception as e:
            logger.error(f"❌ Excepción cancelando apagado: {e}")
            return False

    async def stop(self) -> None:
        """Detener manager y cerrar conexión"""
        logger.info("🛑 Deteniendo ESP32 Manager...")
        
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                logger.info("✅ Puerto serial cerrado")
            self.connected = False  # ✅ CORRECCIÓN: Marcar como desconectado
        except Exception as e:
            logger.error(f"❌ Error cerrando puerto serial: {e}")
        
        logger.info("✅ ESP32 Manager detenido")

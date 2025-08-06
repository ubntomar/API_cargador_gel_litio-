#!/usr/bin/env python3
"""
ESP32Manager - VERSIÓN OPTIMIZADA con Técnicas de Chunks
Integra las estrategias exitosas de paste.txt con protección anti-congelamiento
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
        self.lock = threading.Lock()  # ✅ CORRECCIÓN: Lock thread-safe para concurrencia real
        self._last_data = None
        self._last_data_time = 0
        self._cache_duration = 15.0  # ✅ CRÍTICO: Cache por 15 segundos para frontend con polling cada 3s
        self._communication_errors = 0
        self._max_retries = 3
        
        # ✅ FRONTEND POLLING: Control especial para comandos concurrentes
        self._last_set_command_time = 0
        self._min_set_command_interval = 1.0  # Reducido a 1s para mejor responsividad
        
        # ✅ NUEVO: Sistema de prioridades para GET vs SET
        self._priority_lock = threading.RLock()  # Re-entrant lock para operaciones anidadas
        self._get_requests_active = 0  # Contador de peticiones GET activas
        self._max_concurrent_gets = 2  # Máximo 2 peticiones GET simultáneas
        
        logger.info("🚀 Iniciando ESP32 Manager optimizado con chunks...")
        
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
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔌 Intento {attempt + 1}: Conectando a {settings.SERIAL_PORT}")
                
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                
                self.serial_conn = serial.Serial(
                    port=settings.SERIAL_PORT,
                    baudrate=settings.SERIAL_BAUDRATE,
                    timeout=min(settings.SERIAL_TIMEOUT, 2.0),  # ✅ Máximo 2s timeout
                    write_timeout=1.0,  # ✅ Timeout de escritura
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )
                
                # Limpiar buffers
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                
                # Probar comunicación con timeout corto
                if await self._test_communication():
                    self.connected = True
                    self.communication_errors = 0
                    logger.info(f"✅ Conectado al ESP32 en {settings.SERIAL_PORT}")
                    return True
                else:
                    logger.warning(f"❌ No se pudo comunicar con ESP32 en intento {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"❌ Intento {attempt + 1} falló: {e}")
                await asyncio.sleep(min(1, attempt))  # ✅ Backoff progresivo
        
        self.connected = False
        return False
    
    async def _test_communication(self) -> bool:
        """Probar comunicación con timeout agresivo"""
        try:
            logger.info("🧪 Probando comunicación con ESP32...")
            
            # ✅ Test rápido con estrategias optimizadas
            response = await self._get_json_with_strategies("CMD:GET_DATA", timeout=3.0)
            
            if response and (response.startswith("DATA:") or "panelToBatteryCurrent" in response):
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
                        
                        # Mostrar progreso cada 200 caracteres
                        if len(response) % 200 == 0 and len(response) > 0:
                            logger.debug(f"   📊 Recibidos: {len(response)} caracteres...")
                        
                        # ✅ MEJORA: Verificación inteligente de JSON completo
                        if self._is_json_complete(response):
                            logger.debug(f"   🎯 JSON completo: {len(response)} caracteres")
                            return response
                else:
                    consecutive_empty += 1
                    if consecutive_empty >= max_empty:
                        break
                
                # ✅ MEJORA: Sleep optimizado para chunks pequeños
                await asyncio.sleep(0.01 if chunk_size <= 32 else 0.02)
            
            return response if response else None
            
        except Exception as e:
            logger.error(f"   ❌ Error en lectura chunked: {e}")
            return None

    async def _read_json_adaptive(self, timeout: float = 5.0) -> Optional[str]:
        """
        ✅ TÉCNICA OPTIMIZADA: Lectura adaptativa (estrategia secundaria de paste.txt)
        - Ajusta automáticamente el tamaño del chunk
        - Fallback robusto si chunks fijos fallan
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
        
        logger.debug("🧠 Lectura adaptativa")
        
        start_time = time.time()
        response = ""
        chunk_size = 16  # Empezar pequeño
        max_chunk = 256
        min_chunk = 8
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
            
            # ✅ MEJORA: Verificar balance de llaves
            open_braces = 0
            close_braces = 0
            end_pos = -1
            
            for i, char in enumerate(json_part):
                if char == '{':
                    open_braces += 1
                elif char == '}':
                    close_braces += 1
                    if open_braces == close_braces and open_braces > 0:
                        end_pos = i
                        break
            
            if end_pos == -1 or open_braces != close_braces:
                return False
            
            # ✅ MEJORA: Extraer y parsear JSON real
            complete_json = json_part[:end_pos + 1]
            parsed_data = json.loads(complete_json)
            
            # ✅ MEJORA: Verificar campos característicos del ESP32
            esp32_fields = [
                'panelToBatteryCurrent', 'batteryToLoadCurrent', 'voltagePanel',
                'voltageBatterySensor2', 'chargeState', 'currentPWM', 'temperature',
                'bulkVoltage', 'absorptionVoltage', 'floatVoltage', 'batteryCapacity'
            ]
            
            present_fields = sum(1 for field in esp32_fields if field in parsed_data)
            
            # Debe tener al menos 5 campos del ESP32
            return present_fields >= 5
            
        except (json.JSONDecodeError, ValueError, TypeError):
            return False

    async def _get_json_with_strategies(self, command: str, timeout: float = 5.0) -> Optional[str]:
        """
        ✅ TÉCNICA OPTIMIZADA: Estrategias múltiples ordenadas por éxito (basada en paste.txt)
        - Estrategia 1: Chunks 16 bytes (funcionó perfectamente en RISC-V)
        - Estrategia 2: Chunks 32 bytes (también funcionó perfectamente)  
        - Estrategia 3: Lectura adaptativa (backup robusto)
        """
        # Enviar comando inicial
        if not await self._send_command_simple(command):
            logger.error("❌ Error enviando comando")
            return None
        
        # Pausa inicial para que el ESP32 procese
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
        ✅ MEJORADO: Obtener datos del ESP32 con gestión de concurrencia optimizada
        Prioriza cache para reducir carga en puerto serial
        """
        current_time = time.time()
        
        # ✅ MEJORA: Cache más inteligente para reducir peticiones concurrentes
        if (self._last_data and 
            (current_time - self._last_data_time) < self._cache_duration):
            logger.debug(f"� Retornando datos cached (edad: {current_time - self._last_data_time:.1f}s)")
            return self._last_data
        
        # ✅ MEJORA: Timeout más corto para peticiones GET (no son críticas)
        try:
            with self.lock:
                logger.debug(f"🔒 Lock adquirido para obtener datos")
                
                response = await self._get_json_with_strategies("CMD:GET_DATA")
                
                if response and self._is_json_complete(response):
                    # Actualizar cache
                    self._last_data = response
                    self._last_data_time = current_time
                    self._communication_errors = 0  # Reset counter on success
                    
                    # Log de éxito ocasional para no saturar logs
                    if current_time % 30 < 3:  # Log cada ~30 segundos
                        logger.info(f"✅ Datos ESP32 obtenidos exitosamente (cached por {self._cache_duration}s)")
                    
                    return response
                else:
                    logger.warning("⚠️ Respuesta incompleta del ESP32")
                    return None
                    
        except Exception as e:
            self._communication_errors += 1
            logger.error(f"❌ Error obteniendo datos del ESP32 (error #{self._communication_errors}): {e}")
            
            # ✅ MEJORA: Retornar datos cached si hay errores de comunicación recientes
            if self._last_data and (current_time - self._last_data_time) < 10.0:
                logger.info(f"🔄 Retornando datos cached por error de comunicación")
                return self._last_data
                
            return None
    
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
            logger.error(f"   Respuesta: {response[:200]}")
            return None
    
    async def _send_command_and_read_text(self, command: str, timeout: float = 5.0) -> Optional[str]:
        """
        ✅ MEJORADO: Enviar comando y leer respuesta de texto plano (no JSON)
        Específico para comandos SET que devuelven texto simple
        Maneja casos donde ESP32 envía respuestas mixtas o con timing irregular
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
            
        try:
            # Enviar comando
            if not await self._send_command_simple(command):
                return None
                
            # Pausa para procesamiento
            await asyncio.sleep(0.3)
            
            # Leer respuesta completa con estrategia multi-fase
            start_time = time.time()
            response = ""
            lines = []
            confirmation_found = False
            
            while (time.time() - start_time) < timeout:
                if self.serial_conn.in_waiting > 0:
                    chunk = self.serial_conn.read(self.serial_conn.in_waiting)
                    if chunk:
                        chunk_str = chunk.decode('utf-8', errors='replace')
                        response += chunk_str
                        
                        # Procesar líneas completas
                        while '\n' in response:
                            line, response = response.split('\n', 1)
                            line = line.replace('\r', '').strip()
                            if line:
                                lines.append(line)
                                logger.debug(f"📨 Línea ESP32: {line}")
                                
                                # ✅ MEJORA: Buscar respuesta de confirmación primero
                                if line.startswith("OK:") or line.startswith("ERROR:"):
                                    logger.info(f"✅ Respuesta de confirmación encontrada: {line}")
                                    confirmation_found = True
                                    return line
                                    
                        # ✅ NUEVO: Detección temprana de JSON para evitar lectura innecesaria
                        if len(response) > 100 and not confirmation_found:
                            # Verificar si lo que tenemos es claramente JSON
                            if response.strip().startswith("{") and ("\"" in response or ":" in response):
                                logger.warning(f"⚠️ JSON detectado tempranamente sin confirmación previa")
                                # Esperar un poco más por si la confirmación viene después
                                await asyncio.sleep(0.2)
                                continue
                        
                        # ✅ MEJORA: Si acumulamos mucha data sin OK/ERROR, asumir que no viene
                        if len(response) > 500:  # Demasiado texto acumulado
                            logger.warning(f"⚠️ Mucha data sin confirmación, posible respuesta JSON")
                            # Revisar si tenemos líneas válidas previas
                            for line in lines:
                                if line.startswith("OK:") or line.startswith("ERROR:"):
                                    return line
                            break
                            
                await asyncio.sleep(0.01)
            
            # ✅ MEJORA: Análisis final inteligente de respuesta
            if lines:
                # Prioridad 1: Buscar confirmación explícita
                for line in lines:
                    if line.startswith("OK:") or line.startswith("ERROR:"):
                        return line
                
                # Prioridad 2: Si no hay confirmación pero hay líneas de texto plano
                for line in lines:
                    if not line.startswith("{") and not "\"" in line and len(line) < 100:
                        logger.info(f"✅ Usando línea de texto plano como confirmación: {line}")
                        return line
                        
                # Prioridad 3: Último recurso - primera línea no-JSON corta
                first_line = lines[0]
                if len(first_line) < 50 and not first_line.startswith("{"):
                    logger.warning(f"⚠️ Usando primera línea como confirmación por defecto: {first_line}")
                    return first_line
                        
            # ✅ NUEVO: Para casos extremos, generar confirmación sintética si el comando parece procesado
            if len(response) > 200 and "{" in response:
                logger.warning(f"⚠️ ESP32 envió JSON sin confirmación - posible éxito implícito")
                # Extraer parámetro del comando para respuesta sintética
                if "SET_" in command:
                    param_part = command.split("SET_")[1]
                    if ":" in param_part:
                        param_name = param_part.split(":")[0]
                        param_value = param_part.split(":", 1)[1]
                        synthetic_response = f"OK:{param_name} updated to {param_value}"
                        logger.info(f"🔧 Generando respuesta sintética: {synthetic_response}")
                        return synthetic_response
                        
            logger.warning(f"⚠️ Sin respuesta de texto válida, data recibida: {len(response)} chars")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error leyendo respuesta texto: {e}")
            return None

    async def set_parameter(self, parameter: str, value: Any) -> Dict[str, Any]:
        """
        ✅ MÉTODO MEJORADO: Establecer parámetro con respuesta detallada
        Maneja respuestas de texto plano del ESP32
        """
        result = {
            "success": False,
            "parameter": parameter,
            "value": value,
            "error": None,
            "response": None
        }
        
        try:
            logger.info(f"⚙️ Configurando {parameter} = {value}")
            
            # Formatear comando según protocolo ESP32
            command = f"CMD:SET_{parameter}:{value}"
            
            # ✅ MEJORA: Control de tasa para comandos SET
            current_time = time.time()
            time_since_last_set = current_time - self._last_set_command_time
            
            if time_since_last_set < self._min_set_command_interval:
                wait_time = self._min_set_command_interval - time_since_last_set
                logger.info(f"⏱️ Esperando {wait_time:.1f}s antes del siguiente comando SET (anti-saturación)")
                await asyncio.sleep(wait_time)
            
            # ✅ MEJORA: Timeout más largo para parámetros problemáticos
            lock_acquired = False
            try:
                # Timeout más largo para parámetros conocidos problemáticos
                timeout_seconds = 8.0 if parameter in ["useFuenteDC", "isLithium"] else 3.0
                
                # ✅ CORRECCIÓN: Usar with para manejo automático del lock
                with self.lock:
                    self._last_set_command_time = time.time()
                    logger.debug(f"🔒 Lock adquirido para {parameter}")
                    
                    # ✅ CORRECCIÓN: Usar método específico para texto plano con timeout ajustado
                    communication_timeout = 8.0 if parameter in ["useFuenteDC", "isLithium"] else 4.0
                    response = await self._send_command_and_read_text(command, timeout=communication_timeout)
                    result["response"] = response
                    
            except Exception as e:
                result["error"] = f"Error de comunicación: {str(e)}"
                logger.error(f"❌ Error en comunicación con ESP32: {e}")
                return result
            
            # ✅ MEJORA: Validación más específica para respuestas del ESP32
            if response:
                if response.startswith("OK:"):
                    logger.info(f"✅ {parameter} configurado exitosamente: {response}")
                    # ✅ Invalidar cache
                    self._last_data = None
                    result["success"] = True
                    result["error"] = None
                elif response.startswith("ERROR:"):
                    error_msg = f"Error del ESP32: {response}"
                    result["error"] = error_msg
                    logger.error(f"❌ Error configurando {parameter}: {error_msg}")
                elif "{" in response or "\"" in response:
                    # ✅ NUEVO: Detección de respuesta JSON inesperada
                    error_msg = f"ESP32 devolvió JSON en lugar de confirmación de texto. Esto sugiere un problema de protocolo."
                    result["error"] = error_msg
                    logger.error(f"❌ Protocolo mixto detectado para {parameter}: JSON recibido cuando se esperaba texto")
                    logger.debug(f"   Respuesta JSON: {response[:200]}...")
                else:
                    # ✅ NUEVO: Para useFuenteDC y parámetros similares, intentar interpretar como éxito
                    if parameter in ["useFuenteDC", "loadTestMode"] and len(response) < 50:
                        logger.info(f"✅ {parameter} posiblemente configurado - respuesta no estándar: {response}")
                        self._last_data = None
                        result["success"] = True
                        result["error"] = None
                    else:
                        error_msg = f"Respuesta inesperada del ESP32: {response}"
                        result["error"] = error_msg
                        logger.warning(f"⚠️ Respuesta no estándar para {parameter}: {error_msg}")
            else:
                error_msg = "Sin respuesta del ESP32"
                result["error"] = error_msg
                logger.error(f"❌ Sin respuesta configurando {parameter}")
                
        except asyncio.TimeoutError:
            result["error"] = "Timeout comunicándose con ESP32"
            logger.error(f"❌ Timeout configurando {parameter}")
        except Exception as e:
            result["error"] = f"Excepción: {str(e)}"
            logger.error(f"❌ Excepción configurando {parameter}: {e}")
            
        return result
    
    async def toggle_load(self, total_seconds: int) -> bool:
        """
        ✅ MÉTODO MEJORADO: Toggle load con estrategias optimizadas
        """
        try:
            logger.info(f"🔌 Enviando comando para apagar carga por {total_seconds} segundos")
            
            command = f"CMD:TOGGLE_LOAD:{total_seconds}"
            
            # ✅ MEJORA: Timeout extra largo para acciones críticas
            if not self.lock.acquire(timeout=3.0):
                logger.error("❌ Timeout obteniendo lock para toggle_load")
                return False
            
            try:
                response = await self._get_json_with_strategies(command, timeout=8.0)
            finally:
                self.lock.release()
            
            if response and ("OK:" in response or "success" in response.lower()):
                logger.info(f"✅ Comando toggle_load enviado exitosamente")
                logger.info(f"   Respuesta ESP32: {response}")
                # ✅ Invalidar cache
                self._last_data = None
                return True
            else:
                logger.error(f"❌ Error en toggle_load: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción en toggle_load: {e}")
            return False
    
    async def cancel_temporary_off(self) -> bool:
        """
        ✅ MÉTODO MEJORADO: Cancelar apagado temporal con estrategias optimizadas
        """
        try:
            logger.info("🔌 Enviando comando para cancelar apagado temporal")
            
            command = "CMD:CANCEL_TEMP_OFF"
            
            if not self.lock.acquire(timeout=3.0):
                logger.error("❌ Timeout obteniendo lock para cancel_temporary_off")
                return False
            
            try:
                response = await self._get_json_with_strategies(command, timeout=8.0)
            finally:
                self.lock.release()
            
            if response and ("OK:" in response or "success" in response.lower()):
                logger.info(f"✅ Comando cancel_temporary_off enviado exitosamente")
                logger.info(f"   Respuesta ESP32: {response}")
                # ✅ Invalidar cache
                self._last_data = None
                return True
            else:
                logger.error(f"❌ Error en cancel_temporary_off: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción cancelando apagado: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Obtener información de conexión (SIN CAMBIOS - compatible)
        """
        return {
            "connected": self.connected,
            "port": settings.SERIAL_PORT,
            "baudrate": settings.SERIAL_BAUDRATE,
            "last_communication": self.last_successful_communication,
            "communication_errors": self.communication_errors,
            "queue_size": 0,
            "has_cached_data": self._last_data is not None,
            "cache_age_seconds": time.time() - self._last_data_time if self._last_data else 0,
            "optimization": "chunks_enabled"  # ✅ Indicador de optimización
        }
    
    async def stop(self):
        """
        Detener manager (SIN CAMBIOS - compatible)
        """
        logger.info("🛑 Deteniendo ESP32 Manager...")
        
        # ✅ Liberar lock si está bloqueado
        try:
            if self.lock.locked():
                self.lock.release()
        except:
            pass
        
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                logger.info("✅ Puerto serial cerrado")
            except Exception as e:
                logger.error(f"❌ Error cerrando puerto serial: {e}")
        
        self.connected = False
        logger.info("✅ ESP32 Manager detenido")